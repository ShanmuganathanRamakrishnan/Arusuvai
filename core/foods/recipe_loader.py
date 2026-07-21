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

import yaml

from core.foods.models import Component, Recipe, RecipeIngredient
from core.foods.portions import serving_unit as build_serving_unit
from core.foods.templates import ALL_TEMPLATES
from core.nutrition import citations
from core.schemas import DietPattern, RawOrCooked, Region

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


def load_recipe_file(path: Path, known_ingredients: frozenset[str]) -> tuple[Recipe, str]:
    """Parse one recipe file. Returns ``(recipe, category)``.

    Raises on anything malformed — a recipe is hand-authored, so a broken one is
    a mistake someone can fix, not a data-quality statistic to tolerate.
    """

    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"{path.name}: top level must be a mapping")

    recipe_id = str(_require(doc, "id", path))
    region = Region(str(_require(doc, "region", path)))
    patterns = frozenset(
        DietPattern(str(p)) for p in _require(doc, "diet_patterns", path)
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
        if ingredient_id not in known_ingredients:
            raise ValueError(
                f"{path.name}: ingredient {ingredient_id!r} is not in the loaded "
                "ingredient set (rejected at load time, or never present)"
            )
        lines.append(
            RecipeIngredient(
                ingredient_id=ingredient_id,
                quantity_g=float(_require(raw_line, "quantity_g", path)),
                state=RawOrCooked(str(_require(raw_line, "state", path))),
            )
        )

    uncertainty = {str(k): float(v) for k, v in (doc.get("process_uncertainty") or {}).items()}
    notes = {str(k): str(v) for k, v in (doc.get("uncertainty_notes") or {}).items()}
    constants = frozenset(str(k) for k in (doc.get("process_constants") or []))

    for key in constants:
        citations.constant(key)  # raises with a pointed message if unregistered

    for macro, value in uncertainty.items():
        if macro not in notes or not notes[macro].strip():
            raise ValueError(
                f"{path.name}: process_uncertainty[{macro!r}] = {value} has no "
                "uncertainty_notes entry. An uncertainty figure without its "
                "derivation is a magic number in a data file."
            )
        if value > 0 and not constants:
            raise ValueError(
                f"{path.name}: declares uncertainty on {macro!r} but lists no "
                "process_constants to derive it from"
            )

    recipe = Recipe(
        id=recipe_id,
        name=str(_require(doc, "name", path)),
        region=region,
        diet_patterns=patterns,
        ingredients=tuple(lines),
        serving_unit=serving,
        prep_minutes=int(doc.get("prep_minutes", 0)),
        tags=frozenset(str(t) for t in (doc.get("tags") or [])),
        process_uncertainty=uncertainty,
        process_constants=constants,
    )
    return recipe, category


def load_recipes(
    recipe_dir: Path | str,
    known_ingredients: frozenset[str],
    *,
    strict: bool = True,
) -> RecipeLibrary:
    recipe_dir = Path(recipe_dir)
    library = RecipeLibrary()
    for path in sorted(recipe_dir.glob("*.yaml")):
        if path.name == "schema.yaml":
            continue  # the specification, not a recipe
        try:
            recipe, category = load_recipe_file(path, known_ingredients)
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
