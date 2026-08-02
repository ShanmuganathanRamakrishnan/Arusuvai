"""Concrete meal templates.

The point of this module is the *differences* between the three templates. A
uniform five-slot grammar (base / protein / curry / vegetable / accompaniment)
does not describe any of these meals correctly:

* **South Indian breakfast** (idli + sambar + chutney) has no base/curry split
  and no separate vegetable slot at all. The sambar is simultaneously the
  protein and the vegetable; the chutney is a condiment measured in
  tablespoons, not a dish. Forcing a vegetable slot here produces plates nobody
  eats — idli, sambar, and a side of poriyal is not a breakfast in Chennai.

* **South Indian lunch** (rice + sambar/kuzhambu + one or two poriyals + curd)
  does have a base/gravy split, takes a *variable* number of vegetable dishes,
  and ends with a curd or rasam course that is close to obligatory. Its
  vegetable slot is the one genuinely variable-length slot in this file.

* **North Indian dinner** (roti + dal + sabzi) has no rice slot at all, and its
  base is a counted bread rather than a scooped grain — which is also why the
  serving units differ in kind: "3 rotis" and "1 cup rice" are not the same
  sort of quantity even though both are the base.

Salad/papad-type extras are modelled as optional slots rather than left out,
because an optional slot that contributes ~30 kcal is exactly the sort of thing
the solver can use to close a small energy gap without distorting the plate.
"""

from __future__ import annotations

from core.foods.models import MealTemplate, TemplateSlot
from core.schemas import MealSlot, Region

__all__ = [
    "SOUTH_BREAKFAST",
    "SOUTH_LUNCH",
    "NORTH_DINNER",
    "ALL_TEMPLATES",
    "template_for",
]


SOUTH_BREAKFAST = MealTemplate(
    id="south_breakfast",
    region=Region.SOUTH_INDIAN,
    meal_slot=MealSlot.BREAKFAST,
    slots=(
        # The steamed/griddled item is the meal. Everything else accompanies it.
        TemplateSlot(
            name="tiffin_item",
            accepted_categories=frozenset({"tiffin"}),
        ),
        TemplateSlot(
            name="gravy_accompaniment",
            accepted_categories=frozenset({"sambar", "kuzhambu"}),
        ),
        # One or two chutneys is normal; zero is not, hence required.
        TemplateSlot(
            name="chutney",
            accepted_categories=frozenset({"chutney", "podi"}),
            min_selections=1,
            max_selections=2,
        ),
        # Added 2026-08-02 to close docs/audit_log.md finding 25: none of the
        # four slots above can accept a high-quality protein source, so a
        # per-meal quality floor would have made this template unsatisfiable
        # for a structural reason rather than a thin-library one. A katori of
        # plain curd beside idli or dosa is an ordinary South Indian breakfast,
        # so the slot is real food rather than a hole cut to fit a rule.
        #
        # Deliberately OPTIONAL, unlike SOUTH_LUNCH.curd_course, which is
        # required because a South Indian lunch ends with thayir close to
        # obligatorily. Breakfast does not: idli + sambar + chutney with no
        # curd must still enumerate, and it does.
        TemplateSlot(
            name="curd_course",
            accepted_categories=frozenset({"curd", "buttermilk"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
        TemplateSlot(
            name="beverage",
            accepted_categories=frozenset({"beverage"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)

SOUTH_LUNCH = MealTemplate(
    id="south_lunch",
    region=Region.SOUTH_INDIAN,
    meal_slot=MealSlot.LUNCH,
    slots=(
        TemplateSlot(
            name="rice_base",
            accepted_categories=frozenset({"rice", "mixed_rice"}),
        ),
        TemplateSlot(
            name="gravy",
            accepted_categories=frozenset({"sambar", "kuzhambu", "rasam"}),
        ),
        # The variable-length slot: one poriyal on a weekday, two on a Sunday.
        TemplateSlot(
            name="vegetable",
            accepted_categories=frozenset({"poriyal", "kootu"}),
            min_selections=1,
            max_selections=2,
        ),
        TemplateSlot(
            name="curd_course",
            accepted_categories=frozenset({"curd", "buttermilk"}),
        ),
        TemplateSlot(
            name="crisp",
            accepted_categories=frozenset({"appalam", "pickle"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)

NORTH_DINNER = MealTemplate(
    id="north_dinner",
    region=Region.NORTH_INDIAN,
    meal_slot=MealSlot.DINNER,
    slots=(
        # Counted breads, not a scooped grain. No rice slot in this template.
        TemplateSlot(
            name="bread",
            accepted_categories=frozenset({"roti", "paratha"}),
        ),
        TemplateSlot(
            name="dal",
            accepted_categories=frozenset({"dal", "legume_curry"}),
        ),
        TemplateSlot(
            name="sabzi",
            accepted_categories=frozenset({"sabzi"}),
        ),
        TemplateSlot(
            name="salad_or_raita",
            accepted_categories=frozenset({"raita", "salad"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)

#: Rajma chawal is the awkward case that proves the grammar is per-meal rather
#: than global: it is a North Indian meal built on rice, so it belongs to a
#: north *lunch* template, not to NORTH_DINNER. Written here as a fourth
#: template because leaving it out would have tempted a future reader to widen
#: NORTH_DINNER's bread slot to accept rice, which would let the enumerator
#: produce roti-with-chawal plates.
NORTH_LUNCH = MealTemplate(
    id="north_lunch",
    region=Region.NORTH_INDIAN,
    meal_slot=MealSlot.LUNCH,
    slots=(
        TemplateSlot(
            name="grain_base",
            accepted_categories=frozenset({"rice", "roti"}),
        ),
        TemplateSlot(
            name="legume_curry",
            accepted_categories=frozenset({"legume_curry", "dal", "combo_rice_legume"}),
        ),
        TemplateSlot(
            name="sabzi",
            accepted_categories=frozenset({"sabzi"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
        TemplateSlot(
            name="salad_or_raita",
            accepted_categories=frozenset({"raita", "salad"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)

ALL_TEMPLATES: tuple[MealTemplate, ...] = (
    SOUTH_BREAKFAST,
    SOUTH_LUNCH,
    NORTH_LUNCH,
    NORTH_DINNER,
)


def template_for(region: Region, meal_slot: MealSlot) -> MealTemplate:
    """Look up the grammar for a (region, meal_slot) pair.

    Raises rather than falling back to a default template: a missing grammar is
    impossible input, and silently substituting another region's plate shape is
    precisely the class of error this module exists to prevent.
    """

    for t in ALL_TEMPLATES:
        if t.region is region and t.meal_slot is meal_slot:
            return t
    raise KeyError(
        f"no meal template for region={region.value} slot={meal_slot.value}. "
        "Templates are per (region, meal_slot) by design; add one rather than "
        "reusing another region's plate shape."
    )
