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
    "SOUTH_DINNER",
    "NORTH_BREAKFAST",
    "SOUTH_SNACK",
    "NORTH_SNACK",
    "NORTH_DINNER",
    "NORTH_LUNCH",
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

#: TASKS_3.md R4d ("South dinner reuses much of South lunch"). A South Indian
#: family dinner is, in the ordinary case, the same meal grammar as lunch —
#: rice + sambar/kuzhambu/rasam + one or two poriyals + a closing curd course
#: — not a structurally different plate the way NORTH_DINNER's counted-bread
#: grammar differs from NORTH_LUNCH's rice option. Portions run smaller at
#: dinner in practice, but that is a serving-count fact the solver already
#: handles per meal-target, not a slot-shape fact this grammar needs to
#: encode. Deliberately mirrors SOUTH_LUNCH's five slots and categories
#: exactly rather than inventing a distinct dinner grammar with no comparable
#: real-world basis in this project's own domain modelling — a genuine
#: difference would earn its own slot list the way south_breakfast's does;
#: none was identified here, so none is asserted.
SOUTH_DINNER = MealTemplate(
    id="south_dinner",
    region=Region.SOUTH_INDIAN,
    meal_slot=MealSlot.DINNER,
    slots=(
        TemplateSlot(
            name="rice_base",
            accepted_categories=frozenset({"rice", "mixed_rice"}),
        ),
        TemplateSlot(
            name="gravy",
            accepted_categories=frozenset({"sambar", "kuzhambu", "rasam"}),
        ),
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

#: TASKS_3.md R4d ("North Indian breakfast" — the genuinely new piece, unlike
#: SOUTH_DINNER above, which reused SOUTH_LUNCH's grammar wholesale). A stuffed
#: paratha served with curd/raita and pickle is named as the archetypal North
#: Indian breakfast by every source consulted (see aloo_paratha.yaml's own
#: header) — structurally distinct from both NORTH_LUNCH (rice-or-roti base,
#: a legume curry) and NORTH_DINNER (roti, dal, sabzi): no dal course at
#: breakfast, no rice option, and a curd/raita course that lunch and dinner
#: only offer optionally is close to standard here.
#:
#: `bread_base` accepts {"roti", "paratha"}, not paratha alone, and is
#: OPTIONAL rather than required — both measured before committing to the
#: narrower/required versions and reverted when they failed. First revert:
#: a paratha's added oil makes it fat-dense enough (and, by the same token,
#: carb-light enough) that no combination of aloo/paneer/plain paratha and
#: onion_raita, at any legal serving count, could satisfy the breakfast
#: target's carb floor and fat ceiling together — phulka (dry-griddled, no
#: oil, already in the library for NORTH_DINNER) was added for its far
#: better carb:fat ratio, a genuine everyday North Indian breakfast food in
#: its own right, not invented to pass this template. Second revert: even
#: with all four bread candidates, the two-slot template (bread + curd)
#: still could not satisfy the protein floor (28 g) and fat ceiling (~22.6 g)
#: together — protein-dense breads carry too much fat, and phulka alone
#: cannot reach the protein floor at any count. `protein_course`
#: (moong_dal_chilla — see its own header) closes that gap: a genuine,
#: separately-named North Indian breakfast dish, high-protein and low-fat,
#: not a bread substitute. Making `bread_base` optional rather than required
#: alongside it is itself realistic, not just numerically convenient: a
#: chilla-only breakfast with no separate bread is an ordinary meal, not an
#: invented one.
#:
#: Known limitation, stated before it is discovered rather than after
#: (finding 51's lesson): `curd_or_raita`'s only current filler is
#: onion_raita, which is dairy-classed and therefore not vegan-eligible.
#: Vegan north_indian/breakfast is a structural zero today, the same shape of
#: gap soya_curd closed for vegan south_indian/lunch — closing it the same way
#: needs a north-region vegan curd/raita dish, deliberately left for a
#: separate task rather than folded into this one.
NORTH_BREAKFAST = MealTemplate(
    id="north_breakfast",
    region=Region.NORTH_INDIAN,
    meal_slot=MealSlot.BREAKFAST,
    slots=(
        TemplateSlot(
            name="bread_base",
            accepted_categories=frozenset({"roti", "paratha"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
        TemplateSlot(
            name="protein_course",
            accepted_categories=frozenset({"dal_chilla"}),
        ),
        TemplateSlot(
            name="curd_or_raita",
            accepted_categories=frozenset({"curd", "raita"}),
        ),
        # Pickle has no filler in the library yet, same as SOUTH_LUNCH's
        # `crisp` slot (appalam/pickle) — optional so its emptiness is not a
        # structural block, real the moment a pickle recipe lands.
        TemplateSlot(
            name="pickle",
            accepted_categories=frozenset({"pickle"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
        # Mirrors SOUTH_BREAKFAST.beverage — also currently unfilled, also
        # optional for the same reason.
        TemplateSlot(
            name="beverage",
            accepted_categories=frozenset({"beverage"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)

#: TASKS_3.md R4d ("South Indian snack", 2026-09-25). The ordinary Tamil
#: evening snack: a katori of sundal -- boiled legumes tempered with mustard,
#: urad dal and curry leaves, finished with coconut -- with a glass of neer mor
#: (thin spiced buttermilk) beside it, or without. One required dish and one
#: optional drink; no base, no curry, no side, because a snack is not a small
#: lunch.
#:
#: Below the per-template floor, stated before anyone measures it
#: (docs/audit_log.md 2026-09-25): 0/144 profiles reach the two-plate pass
#: mark, 25/144 get one valid plate. The cause is structural, not a thin
#: library. The snack's energy window is roughly 20-35 kcal wide, and a
#: one-dish plate moves in whole units: the only other plate is the same
#: sundal plus neer mor, 31 kcal away, so two plates rarely both fit one
#: window. Heavier lose_fat profiles also need more quality protein per kcal
#: than a sundal carries. No bound was widened to change either number.
SOUTH_SNACK = MealTemplate(
    id="south_snack",
    region=Region.SOUTH_INDIAN,
    meal_slot=MealSlot.SNACK,
    slots=(
        TemplateSlot(
            name="sundal",
            accepted_categories=frozenset({"sundal"}),
        ),
        # Optional for the reason this module's header gives: a ~31 kcal extra
        # the solver can use to close a small energy gap. A sundal alone is a
        # complete snack.
        TemplateSlot(
            name="drink",
            accepted_categories=frozenset({"buttermilk"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)

#: TASKS_3.md R4d ("North Indian snack", 2026-09-25). One main snack dish --
#: a chaat or a tikka -- with a glass of chaas beside it, or without. Built
#: with two genuinely different main dishes from the start
#: (soya_chana_chaat, soya_tikka), per the owner's 2026-09-25 decision that
#: the two-plate pass mark stays for snacks and is met with more dishes, not
#: a lower bar (docs/audit_log.md 2026-09-25). Same shape as SOUTH_SNACK:
#: one required dish, one optional ~30 kcal drink.
#:
#: Plans 0/144 profiles, stated before anyone measures it (docs/audit_log.md
#: 2026-09-25, North Indian snack): the chaat is too lean for the snack's fat
#: floor, the tikka too low in carbohydrate for its carb floor. Both are
#: ordinary dishes and neither was tuned. For that reason web/dashboard.html
#: deliberately offers no North Indian snack card: a card that never solves
#: would tell the user something false.
NORTH_SNACK = MealTemplate(
    id="north_snack",
    region=Region.NORTH_INDIAN,
    meal_slot=MealSlot.SNACK,
    slots=(
        TemplateSlot(
            name="snack",
            accepted_categories=frozenset({"chaat", "tikka"}),
        ),
        # Optional for SOUTH_SNACK.drink's reason. Region filtering keeps
        # neer_mor (south_indian) out; chaas is the North filler.
        TemplateSlot(
            name="drink",
            accepted_categories=frozenset({"buttermilk"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)

ALL_TEMPLATES: tuple[MealTemplate, ...] = (
    SOUTH_BREAKFAST,
    SOUTH_LUNCH,
    SOUTH_DINNER,
    NORTH_BREAKFAST,
    SOUTH_SNACK,
    NORTH_SNACK,
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
