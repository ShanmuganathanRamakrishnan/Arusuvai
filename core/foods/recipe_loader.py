"""Load hand-authored recipe YAML into :class:`Recipe` objects.

The loader is where ``data/recipes/schema.yaml``'s rules are actually enforced,
in particular the one that is easiest to let slide: a recipe may not invent a
nutritional constant. Every macro in ``process_uncertainty`` must be justified
by an ``uncertainty_notes`` entry and backed by a constant registered in
``citations.py``, or the recipe is rejected.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from core.foods.models import Component, Ingredient, Recipe, RecipeIngredient
from core.foods.nutrition_of import nutrition_of_lines
from core.foods.portions import serving_unit as build_serving_unit
from core.foods.templates import ALL_TEMPLATES
from core.nutrition import citations
from core.schemas import MACRO_KEYS, RawOrCooked, Region

logger = logging.getLogger(__name__)

__all__ = ["RecipeLibrary", "load_recipes", "load_recipe_file"]


@dataclass
class RecipeLibrary:
    recipes: dict[str, Recipe] = field(default_factory=dict)
    components: dict[str, Component] = field(default_factory=dict)
    rejected: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def component(self, recipe_id: str) -> Component:
        return self.components[recipe_id]

    def summary(self) -> str:
        return (
            f"{len(self.recipes)} recipes loaded, {len(self.rejected)} rejected, "
            f"{len(self.warnings)} warnings"
        )


_KNOWN_CATEGORIES: frozenset[str] = frozenset().union(
    *(t.categories() for t in ALL_TEMPLATES)
)


def _require(doc: dict, key: str, path: Path):
    if key not in doc:
        raise ValueError(f"{path.name}: missing required key {key!r}")
    return doc[key]


def _derive_process_uncertainty(
    lines: Sequence[RecipeIngredient],
    ingredients: Mapping[str, Ingredient],
    unassessed: Sequence[str],
    path: Path,
) -> dict[str, float]:
    """Fractional process uncertainty per macro, computed from the lines.

    For each macro: sum, over the lines carrying a process constant, of that
    line's contribution to the macro times the constant's own uncertainty; then
    divide by the dish total for that macro.

    Worked example, masala dosa energy — gingelly oil is 884 kcal/100 g:

        griddle oil 3.5 g x 8.84 kcal/g x 0.20 = 6.188 kcal
        temper  oil 3.0 g x 8.84 kcal/g x 0.10 = 2.652 kcal
        (6.188 + 2.652) / 223.65 kcal          = 0.03953

    Every macro is present in the result. A macro nothing process-sensitive
    touches derives to 0.0, which is a *computed* zero rather than an omitted
    one — the author cannot obtain it by leaving the work undone. A macro the
    author declares unassessed takes the registered wide band instead.
    """

    total = nutrition_of_lines(lines, ingredients, recipe_id=path.stem)
    unassessed_band = citations.value_of("process.unassessed_uncertainty")

    derived: dict[str, float] = {}
    for macro in MACRO_KEYS:
        if macro in unassessed:
            derived[macro] = unassessed_band
            continue
        denominator = getattr(total, macro)
        if denominator == 0:
            # Nothing of this macro in the dish, so no fraction is meaningful.
            derived[macro] = 0.0
            continue
        absolute = 0.0
        for line in lines:
            if not line.process_key:
                continue
            contribution = ingredients[line.ingredient_id].for_grams(line.quantity_g)
            absolute += getattr(contribution, macro) * citations.uncertainty_of(
                line.process_key
            )
        derived[macro] = absolute / denominator
    return derived


#: The two things a recipe can be, for the purpose of process uncertainty.
#: ``cooked`` is the default *deliberately*: omitting the key is the cheapest
#: authoring path, and it must lead to the demanding treatment, never the
#: confident one. See ``_check_zero_process_is_earned``.
PREPARATIONS: tuple[str, ...] = ("cooked", "uncooked")


def _check_zero_process_is_earned(
    doc: Mapping[str, object],
    lines: Sequence[RecipeIngredient],
    ingredients: Mapping[str, Ingredient],
    unassessed: Sequence[str],
    path: Path,
) -> None:
    """Reject a *cooked* dish that attributes its zero process uncertainty to nothing.

    `docs/audit_log.md` finding 2, and the question D10 was written to settle:
    can a recipe declare uncertainty with nothing to attribute it to? The answer
    is yes — but only if it says so, because the loader could not otherwise tell
    the two cases apart:

      * ``onion_raita`` is whisked curd with raw onion. Nothing is heated,
        drained, griddled or fried, so every macro's process uncertainty is a
        genuine zero. Its own file header has said so in prose since it was
        written; prose is not something the loader can read.
      * ``phulka`` is griddled and ``idli`` is steamed. Both derived exactly the
        same zeros, from exactly the same absence of a ``process:`` line — not
        because their processes are inert but because nobody has quantified
        them. Measured 2026-08-09: both showed a combined energy band of 0.2500,
        identical to the raw dishes and to the composition-only floor.

    So a recipe with no process constant at all must either declare
    ``preparation: uncooked`` — a claim about the food, checked against the
    lines — or name the macros it cannot quantify, which then take the
    registered wide band.

    **Third earned path, added 2026-08-09 (D12, `docs/audit_log.md` finding
    44).** D10's rule as first written was too blunt in one direction: it
    demanded a justification for every macro, including macros whose every gram
    comes from a composition row that already describes the food *as eaten*.
    ``steamed_rice`` is one line — 200 g of ``rice_cooked``, a cooked-basis row —
    and the boiling is inside the row, not applied by the recipe. There is no
    process step there whose uncertainty went unmeasured, so D10 charged it
    0.20 on all nine macros for a transformation the recipe does not perform.
    The remaining doubt is doubt about the row, which is already charged as
    composition uncertainty at 0.25.

    So a macro is also earned when **no raw-basis line contributes to it**.

    Keyed off ``Ingredient.state`` — the composition record's own basis — and
    deliberately NOT off ``RecipeIngredient.state``, which is author-declared
    and which nothing cross-checks against the row it points at
    (`docs/audit_log.md` finding 46). Keying off the line would make writing
    ``state: cooked`` over a raw-basis row the cheapest way to earn the zeros,
    which is the ordering this whole check exists to prevent, reintroduced by
    the fix for it.

    **Scope, stated rather than left to be discovered.** This fires only when a
    recipe has *no* process constant whatsoever. A cooked dish that carries one
    still derives 0.0 for every macro that constant does not touch, and that
    zero is just as unexamined — but it is unexamined only where a *raw-basis*
    line feeds the macro. Measured, `docs/design/probes/d12_process_attribution.py`:
    34.8% of the library's protein sits on raw-basis lines the recipe cooks and
    nothing quantifies; the other 65.2% is served-basis and its zero is earned.
    Closing the remainder needs process constants for steaming, dry-griddling,
    sauteing and rehydration, which is a data problem, not a loader rule.
    `docs/audit_log.md` finding 41.
    """

    preparation = str(doc.get("preparation", "cooked"))
    if preparation not in PREPARATIONS:
        raise ValueError(
            f"{path.name}: preparation {preparation!r} is not one of {PREPARATIONS}"
        )

    has_process = any(line.process_key for line in lines)
    if preparation == "uncooked":
        if has_process:
            raise ValueError(
                f"{path.name}: preparation is 'uncooked' but an ingredient line "
                "carries a 'process:' key. One of the two is wrong — a dish that "
                "is not cooked has no cooking process to attribute uncertainty to."
            )
        return
    if has_process:
        return

    # Grams of each macro arriving on a raw-basis line. A macro with none of
    # these is fed entirely by rows describing the food as eaten, so the recipe
    # performs no transformation of it and its zero is earned. See the docstring
    # for why this reads the ingredient's state and not the line's.
    from_raw = {macro: 0.0 for macro in MACRO_KEYS}
    for line in lines:
        ingredient = ingredients[line.ingredient_id]
        if ingredient.state is not RawOrCooked.RAW:
            continue
        contribution = ingredient.for_grams(line.quantity_g)
        for macro in MACRO_KEYS:
            from_raw[macro] += getattr(contribution, macro)

    # A macro the dish contains none of is filtered by the same test: nutrient
    # values are non-negative, so a macro with no raw-basis grams has none from
    # a raw-basis line to justify. D10 spelled that case out separately as
    # `getattr(total, macro) != 0`; that arm is now strictly subsumed by this
    # one — `from_raw[m] > 0` implies `total[m] > 0` — and keeping both would
    # leave a condition no input can reach on its own, which the next deletion
    # sweep would correctly report as untested.
    unearned = [
        macro
        for macro in MACRO_KEYS
        if macro not in unassessed and from_raw[macro] != 0
    ]
    if unearned:
        raise ValueError(
            f"{path.name}: no ingredient line carries a 'process:' key, so "
            f"{unearned} would each derive a process uncertainty of 0.0 with "
            "nothing behind it — each is fed by a raw-basis composition row "
            "that this recipe cooks. Either add 'preparation: uncooked' if the "
            "dish genuinely involves no cooking step, or list the macros in "
            "'process_uncertainty_unassessed' so they take the registered wide "
            "band. Omitting both is the cheapest path and must not be the most "
            "confident-looking one."
        )


def load_recipe_file(
    path: Path, ingredients: Mapping[str, Ingredient]
) -> tuple[Recipe, str]:
    """Parse one recipe file. Returns ``(recipe, category)``.

    Raises on anything malformed — a recipe is hand-authored, so a broken one is
    a mistake someone can fix, not a data-quality statistic to tolerate.

    Takes the full ingredient mapping rather than just the set of known ids,
    because process uncertainty is now derived from each line's actual macro
    contribution, which needs composition data.
    """

    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"{path.name}: top level must be a mapping")

    recipe_id = str(_require(doc, "id", path))
    region = Region(str(_require(doc, "region", path)))
    if "diet_patterns" in doc:
        raise ValueError(
            f"{path.name}: 'diet_patterns' is no longer read from the recipe "
            "file — eligibility is derived from the union of ingredient "
            "classes (see core.schemas.IngredientClass) and checked against "
            "core.schemas.DIET_PATTERN_PERMITTED_CLASSES. A hand-listed "
            "whitelist could disagree with what the ingredients actually are: "
            "no recipe ever declared 'eggetarian' or 'non_vegetarian', so both "
            "patterns returned zero candidates everywhere despite every dish "
            "in the library being edible under both (TASKS_3.md R1a)."
        )
    category = str(_require(doc, "category", path))

    su = _require(doc, "serving_unit", path)
    serving = build_serving_unit(
        str(_require(su, "measure", path)),
        min_count=int(_require(su, "min_count", path)),
        default_count=int(_require(su, "default_count", path)),
        max_count=int(_require(su, "max_count", path)),
        grams_per_unit=(
            float(su["grams_per_unit"]) if su.get("grams_per_unit") is not None else None
        ),
        name=su.get("name"),
    )

    lines: list[RecipeIngredient] = []
    for raw_line in _require(doc, "ingredients", path):
        ingredient_id = str(_require(raw_line, "id", path))
        if ingredient_id not in ingredients:
            raise ValueError(
                f"{path.name}: ingredient {ingredient_id!r} is not in the loaded "
                "ingredient set (rejected at load time, or never present)"
            )
        process_key = raw_line.get("process")
        if process_key is not None:
            process_key = str(process_key)
            # Raises with a pointed message if unregistered. Checked here rather
            # than in models.py so the dataclass layer stays free of a
            # dependency on the citations registry.
            citations.constant(process_key)
        lines.append(
            RecipeIngredient(
                ingredient_id=ingredient_id,
                quantity_g=float(_require(raw_line, "quantity_g", path)),
                state=RawOrCooked(str(_require(raw_line, "state", path))),
                process_key=process_key,
            )
        )

    if "process_constants" in doc:
        raise ValueError(
            f"{path.name}: recipe-level 'process_constants' is no longer read — a "
            "hand-maintained list can disagree with the lines it describes. Put "
            "'process: <constant key>' on the ingredient line whose quantity the "
            "constant determines; Recipe.process_constants is derived from those."
        )
    if "process_uncertainty" in doc:
        raise ValueError(
            f"{path.name}: 'process_uncertainty' is no longer read from the recipe "
            "file — it is derived at load time from the process constants on the "
            "ingredient lines and their actual macro contribution. A figure "
            "hand-computed once and pasted here goes stale the moment the "
            "constant in citations.py changes, with the test suite still green. "
            "Use 'process_uncertainty_unassessed: [macro, ...]' for macros you "
            "believe are process-sensitive but cannot quantify."
        )

    unassessed = [str(m) for m in (doc.get("process_uncertainty_unassessed") or [])]
    for macro in unassessed:
        if macro not in MACRO_KEYS:
            raise ValueError(
                f"{path.name}: process_uncertainty_unassessed lists {macro!r}, "
                f"which is not a known macro (one of {MACRO_KEYS})"
            )

    _check_zero_process_is_earned(doc, lines, ingredients, unassessed, path)
    uncertainty = _derive_process_uncertainty(lines, ingredients, unassessed, path)

    recipe = Recipe(
        id=recipe_id,
        name=str(_require(doc, "name", path)),
        region=region,
        ingredients=tuple(lines),
        serving_unit=serving,
        prep_minutes=int(doc.get("prep_minutes", 0)),
        tags=frozenset(str(t) for t in (doc.get("tags") or [])),
        process_uncertainty=uncertainty,
    )
    return recipe, category


def load_recipes(
    recipe_dir: Path | str,
    ingredients: Mapping[str, Ingredient],
    *,
    strict: bool = True,
) -> RecipeLibrary:
    recipe_dir = Path(recipe_dir)
    library = RecipeLibrary()
    for path in sorted(recipe_dir.glob("*.yaml")):
        if path.name == "schema.yaml":
            continue  # the specification, not a recipe
        try:
            recipe, category = load_recipe_file(path, ingredients)
        except (ValueError, KeyError, TypeError) as exc:
            message = f"{path.name}: {exc}"
            logger.warning("rejected recipe — %s", message)
            library.rejected.append(message)
            if strict:
                raise
            continue

        if recipe.id in library.recipes:
            raise ValueError(f"duplicate recipe id {recipe.id!r} in {path.name}")
        if category not in _KNOWN_CATEGORIES:
            # A warning, not a rejection: the recipe library legitimately grows
            # ahead of the template library. But it is surfaced, because a
            # category no template accepts means this dish can never be planned.
            library.warnings.append(
                f"{recipe.id}: category {category!r} is accepted by no meal "
                f"template, so it can never be selected into a plan"
            )
        library.recipes[recipe.id] = recipe
        library.components[recipe.id] = Component(recipe=recipe, category=category)

    logger.info("recipe load: %s", library.summary())
    return library
