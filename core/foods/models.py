"""Frozen dataclasses for ingredients, recipes, serving units and meal templates.

Two conventions are load-bearing and are enforced here rather than documented
and hoped for:

**Cooked weight is the primary record.** ``RecipeIngredient.quantity_g`` is the
finished, plated weight of that ingredient, and the ``state`` field says so
explicitly for every row. Rice roughly triples on cooking, so a raw figure read
as a cooked one is a 3x error rather than a tolerance-band problem. Where only a
raw composition value exists, the conversion goes through
``core.foods.retention`` and a registered yield constant, never an inline
multiplication.

**Portions are integer counts of a named serving unit.** There is no continuous
multiplier and no five-point multiplier scale anywhere in this module: 1.25
idlis is 1.25 idlis, which nobody can serve. A five-point scale produces the
same unservable fractional output, just discretised to look tidier.

Carbohydrate convention: ``carb_g`` is *total* carbohydrate including dietary
fibre, and ``fibre_g`` is the fibre subset of it. This matters for the loader's
Atwater reconciliation, which uses the plain 4/9/4 form on total carbohydrate.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import Mapping

from core.schemas import MACRO_KEYS, DietPattern, MealSlot, RawOrCooked, Region

__all__ = [
    "NutritionVector",
    "Ingredient",
    "RecipeIngredient",
    "ServingUnit",
    "Recipe",
    "Component",
    "TemplateSlot",
    "MealTemplate",
]


@dataclass(frozen=True)
class NutritionVector:
    """Summed nutrient totals. Supports ``+`` and scalar ``*``.

    The scalar multiply is gram-level arithmetic (scaling an ingredient's
    per-100 g record to the quantity actually used), not a portion multiplier.
    Portion size is only ever an integer count of a :class:`ServingUnit`.
    """

    energy_kcal: float = 0.0
    protein_g: float = 0.0
    fat_g: float = 0.0
    carb_g: float = 0.0
    fibre_g: float = 0.0
    sodium_mg: float = 0.0
    iron_mg: float = 0.0
    calcium_mg: float = 0.0
    b12_ug: float = 0.0

    def __add__(self, other: NutritionVector) -> NutritionVector:
        if not isinstance(other, NutritionVector):
            return NotImplemented
        return NutritionVector(
            *(getattr(self, k) + getattr(other, k) for k in MACRO_KEYS)
        )

    def __mul__(self, factor: float) -> NutritionVector:
        if not isinstance(factor, (int, float)):
            return NotImplemented
        return NutritionVector(*(getattr(self, k) * factor for k in MACRO_KEYS))

    __rmul__ = __mul__

    def __radd__(self, other: object) -> NutritionVector:
        # Lets sum() start from 0 without a special case at every call site.
        if other == 0:
            return self
        return NotImplemented

    def as_dict(self) -> dict[str, float]:
        return {k: getattr(self, k) for k in MACRO_KEYS}

    @staticmethod
    def zero() -> NutritionVector:
        return NutritionVector()


# NutritionVector is built positionally from MACRO_KEYS in several places
# above; if someone adds a field without adding the key (or reorders them) the
# arithmetic would silently shift nutrients into the wrong slots.
assert tuple(f.name for f in fields(NutritionVector)) == MACRO_KEYS, (
    "NutritionVector fields must match MACRO_KEYS in order"
)


@dataclass(frozen=True)
class Ingredient:
    """A composition record, per 100 g of edible portion in ``state``."""

    id: str
    name_en: str
    name_ta: str
    name_hi: str
    #: IFCT food code. ``None`` where the row came from the hand-entered
    #: fixture set rather than the published tables — inventing a code that
    #: looks real would be worse than admitting there isn't one.
    ifct_code: str | None
    energy_kcal: float
    protein_g: float
    fat_g: float
    carb_g: float
    fibre_g: float
    sodium_mg: float
    iron_mg: float
    calcium_mg: float
    b12_ug: float
    state: RawOrCooked
    diaas: float | None = None
    is_animal_product: bool = False
    jain_safe: bool = True
    allergens: frozenset[str] = frozenset()
    #: False while the underlying value has not been read out of a primary
    #: source by a human. Mirrors the citations registry's own flag.
    verified: bool = False

    def per_100g(self) -> NutritionVector:
        return NutritionVector(*(getattr(self, k) for k in MACRO_KEYS))

    def for_grams(self, grams: float) -> NutritionVector:
        if grams < 0:
            raise ValueError(f"{self.id}: negative quantity {grams}")
        return self.per_100g() * (grams / 100.0)


@dataclass(frozen=True)
class RecipeIngredient:
    """One line of a recipe. ``quantity_g`` is the finished/plated weight."""

    ingredient_id: str
    quantity_g: float
    state: RawOrCooked
    #: Key of the registered process constant that *determined this line's
    #: quantity* — e.g. ``oil_uptake.dosa_griddled`` on the retained-oil line of
    #: a dosa. Attribution belongs on the line, not the recipe: a masala dosa
    #: has two ``gingelly_oil`` lines that differ only by which process they
    #: belong to, and a recipe-level list cannot express that. It is also what
    #: makes exposure a computed quantity instead of a hand-copied one.
    process_key: str | None = None

    def __post_init__(self) -> None:
        if self.quantity_g <= 0:
            raise ValueError(
                f"{self.ingredient_id}: quantity_g must be positive, got {self.quantity_g}"
            )
        if self.process_key is not None and not self.process_key.strip():
            raise ValueError(
                f"{self.ingredient_id}: process_key must be a registered constant "
                "key or absent, never an empty string"
            )
        if self.state is RawOrCooked.RAW:
            # Not forbidden outright — a raw-basis line is legitimate for
            # something eaten raw — but it must be a deliberate choice, so the
            # loader records it rather than letting it look like an oversight.
            pass


@dataclass(frozen=True)
class ServingUnit:
    """The discrete thing a person is handed: an idli, a katori, a roti.

    ``min_count``/``default_count``/``max_count`` bound the integer domain the
    solver will later search. They are part of the recipe's data, not a knob the
    planner adjusts, because "how many idlis is a plausible serving" is a fact
    about the dish, not about a target.
    """

    name: str
    grams_per_unit: float
    min_count: int
    default_count: int
    max_count: int

    def __post_init__(self) -> None:
        if self.grams_per_unit <= 0:
            raise ValueError(f"serving unit {self.name!r}: grams_per_unit must be > 0")
        for f_name in ("min_count", "default_count", "max_count"):
            v = getattr(self, f_name)
            if not isinstance(v, int) or isinstance(v, bool):
                raise TypeError(
                    f"serving unit {self.name!r}: {f_name} must be an int "
                    f"(got {type(v).__name__}) — portions are integer unit counts, "
                    "never a fractional multiplier"
                )
        if not 1 <= self.min_count <= self.default_count <= self.max_count:
            raise ValueError(
                f"serving unit {self.name!r}: expected "
                f"1 <= min({self.min_count}) <= default({self.default_count}) "
                f"<= max({self.max_count})"
            )

    def counts(self) -> tuple[int, ...]:
        """The full integer domain for this unit, for the solver to enumerate."""

        return tuple(range(self.min_count, self.max_count + 1))

    def grams_for(self, count: int) -> float:
        if not isinstance(count, int) or isinstance(count, bool):
            raise TypeError(
                f"{self.name}: unit count must be an int, got {type(count).__name__}"
            )
        if count < self.min_count or count > self.max_count:
            raise ValueError(
                f"{self.name}: count {count} outside "
                f"[{self.min_count}, {self.max_count}]"
            )
        return self.grams_per_unit * count

    def describe(self, count: int) -> str:
        """Household phrasing for display: '2 idlis', '1 katori'."""

        plural = self.name if count == 1 else f"{self.name}s"
        return f"{count} {plural}"


#: How far the sum of a recipe's ingredient weights may sit from its declared
#: grams_per_unit before the recipe is rejected as internally inconsistent.
#: Not a nutritional constant — it is an authoring-consistency check on our own
#: data, in the same family as the loader's reconciliation tolerance.
_RECIPE_MASS_TOLERANCE = 0.02


@dataclass(frozen=True)
class Recipe:
    """A dish, defined per *one* serving unit.

    ``ingredients`` sum to the finished weight of a single unit of
    ``serving_unit`` — checked on construction, because the alternative (a
    per-batch quantity list plus a separate yield figure) gives two places for
    the same fact to disagree.
    """

    id: str
    name: str
    region: Region
    diet_patterns: frozenset[DietPattern]
    ingredients: tuple[RecipeIngredient, ...]
    serving_unit: ServingUnit
    prep_minutes: int
    tags: frozenset[str] = frozenset()
    #: Fractional process uncertainty keyed by macro, e.g.
    #: ``{"energy_kcal": 0.15}`` for a griddled item whose oil uptake is not
    #: well characterised. Read later by the candidate eligibility filter in
    #: core/planner — it never loosens a tolerance, it makes a recipe less
    #: usable where the macro is target-critical.
    process_uncertainty: Mapping[str, float] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.ingredients:
            raise ValueError(f"recipe {self.id!r} has no ingredients")
        for macro, unc in self.process_uncertainty.items():
            if macro not in MACRO_KEYS:
                raise ValueError(
                    f"recipe {self.id!r}: process_uncertainty key {macro!r} is not "
                    f"a known macro (one of {MACRO_KEYS})"
                )
            if not 0.0 <= unc < 1.0:
                raise ValueError(
                    f"recipe {self.id!r}: process_uncertainty[{macro!r}]={unc} "
                    "must be a fraction in [0, 1)"
                )
        total = sum(ri.quantity_g for ri in self.ingredients)
        declared = self.serving_unit.grams_per_unit
        if abs(total - declared) > _RECIPE_MASS_TOLERANCE * declared:
            raise ValueError(
                f"recipe {self.id!r}: ingredient weights sum to {total:.1f} g but "
                f"serving unit {self.serving_unit.name!r} declares "
                f"{declared:.1f} g per unit. Ingredient quantities are per one "
                "serving unit and must agree with it."
            )
        # Freeze the mapping so a downstream module cannot mutate a recipe's
        # uncertainty — which would be exactly the "uncertainty as a knob"
        # failure CLAUDE.md rules out.
        object.__setattr__(
            self, "process_uncertainty", MappingProxyType(dict(self.process_uncertainty))
        )

    def uncertainty_for(self, macro: str) -> float:
        return float(self.process_uncertainty.get(macro, 0.0))

    @property
    def process_constants(self) -> frozenset[str]:
        """Process constants this recipe depends on, *derived* from its lines.

        Deliberately not a stored field. A hand-maintained list can silently
        disagree with the ingredients it claims to describe, and a reader has no
        way to tell which one is wrong. Deriving it means the disagreement
        cannot be represented.
        """

        return frozenset(
            line.process_key for line in self.ingredients if line.process_key
        )

    def process_exposure_g(self, process_key: str) -> float:
        """Finished grams whose quantity was determined by ``process_key``.

        Computed from the lines every time. The previous design stored the
        equivalent figure (as a pre-divided fraction) in the recipe YAML, where
        editing a quantity left it stale with the tests still green — the
        registry exists precisely so a number derivable from a constant is never
        transcribed beside it.
        """

        return sum(
            line.quantity_g
            for line in self.ingredients
            if line.process_key == process_key
        )

    def lines_for_process(self, process_key: str) -> tuple[RecipeIngredient, ...]:
        """The lines attributed to ``process_key``.

        Needed to attribute an unverified constant's influence to the grams it
        actually governs, rather than to the whole dish.
        """

        return tuple(
            line for line in self.ingredients if line.process_key == process_key
        )


@dataclass(frozen=True)
class Component:
    """A recipe in the role it plays inside a meal: 'base', 'gravy', 'chutney'."""

    recipe: Recipe
    category: str

    @property
    def id(self) -> str:
        return f"{self.recipe.id}@{self.category}"


@dataclass(frozen=True)
class TemplateSlot:
    """One position in a meal's grammar.

    ``min_selections``/``max_selections`` are what make the grammar
    variable-length: a South Indian lunch takes one or two poriyals depending on
    the day, and that is a property of the slot, not something the solver should
    infer.
    """

    name: str
    accepted_categories: frozenset[str]
    required: bool = True
    min_selections: int = 1
    max_selections: int = 1

    def __post_init__(self) -> None:
        if not self.accepted_categories:
            raise ValueError(f"slot {self.name!r} accepts no categories")
        if self.min_selections < 0 or self.max_selections < self.min_selections:
            raise ValueError(f"slot {self.name!r}: bad selection bounds")
        if not self.required and self.min_selections != 0:
            raise ValueError(
                f"slot {self.name!r}: an optional slot must allow zero selections"
            )
        if self.required and self.min_selections == 0:
            raise ValueError(
                f"slot {self.name!r}: a required slot must demand at least one"
            )

    def accepts(self, component: Component) -> bool:
        return component.category in self.accepted_categories


@dataclass(frozen=True)
class MealTemplate:
    """The slot grammar for one (region, meal_slot) pair.

    Deliberately *not* a fixed five-slot base/protein/curry/vegetable/
    accompaniment shape. See ``core/foods/templates.py`` for the three concrete
    templates and why their shapes differ.
    """

    id: str
    region: Region
    meal_slot: MealSlot
    slots: tuple[TemplateSlot, ...]

    def __post_init__(self) -> None:
        if not self.slots:
            raise ValueError(f"template {self.id!r} has no slots")
        names = [s.name for s in self.slots]
        if len(names) != len(set(names)):
            raise ValueError(f"template {self.id!r} has duplicate slot names")

    @property
    def required_slots(self) -> tuple[TemplateSlot, ...]:
        return tuple(s for s in self.slots if s.required)

    @property
    def optional_slots(self) -> tuple[TemplateSlot, ...]:
        return tuple(s for s in self.slots if not s.required)

    def slot(self, name: str) -> TemplateSlot:
        for s in self.slots:
            if s.name == name:
                return s
        raise KeyError(f"template {self.id!r} has no slot {name!r}")

    def categories(self) -> frozenset[str]:
        out: set[str] = set()
        for s in self.slots:
            out |= s.accepted_categories
        return frozenset(out)

    def max_components(self) -> int:
        return sum(s.max_selections for s in self.slots)
