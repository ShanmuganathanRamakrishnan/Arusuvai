"""D6: what fraction of a plate's energy rests on evidence nobody opened.

Finding 20. ``NutritionEstimate.unverified_energy_kcal`` was wrong in both
directions at once -- it charged a recipe's *whole* energy when any process
constant on it was unverified, and charged *nothing* for unverified ingredient
composition. Two large errors that do not cancel, in a number the 15% shipping
threshold and the ``dev_mode`` exit both depend on.

This probe prints the arithmetic line by line so the fraction can be checked by
hand rather than trusted, and computes three figures per plate:

  OLD     the rule as it stood: charge the whole recipe iff any of its process
          constants is unverified. Reimplemented here rather than read from a
          worktree of the old tree -- see below.
  NEW     the rule as fixed: charge each *line* whose energy rests on unopened
          evidence, for either reason, once.
  SHIPPED whatever `core/foods/nutrition_of.py` returns right now.

**Why OLD is reimplemented instead of measured on the pre-D6 tree.** Every
other before/after probe here copies itself into a worktree, because the old
behaviour lives in code too tangled to restate. This one does not: the old rule
is four lines and is quoted verbatim in ``_old_rule`` below. Restating it makes
the two columns come from one process and one library load, and -- the actual
reason -- makes the comparison independent of which tree the probe runs on, so
it keeps working after D6 lands. A worktree column would go stale the moment
the pre-D6 commit stops being interesting.

NEW and SHIPPED are printed side by side precisely so this probe cannot quietly
agree with the code it is auditing: they are two implementations of the same
rule, and a difference between them is a bug in one of them.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d6_unverified.py
"""
from __future__ import annotations

from core.foods.nutrition_of import nutrition_of_components, nutrition_of_recipe
from core.nutrition import citations
from core.planner.plan import load_library

lib = load_library()

#: The four plates the reference profile is served today, from `CLAUDE.md`'s
#: build-status row for `core/planner`. Hard-coded rather than re-solved: this
#: probe is about the evidence behind a plate, and re-running the solver here
#: would make the figures move for reasons that have nothing to do with D6.
PLATES = {
    "south_breakfast": (("idli", 6), ("soya_kuzhambu", 1),
                        ("coconut_chutney", 2), ("thayir_plain", 1)),
    "south_lunch": (("steamed_rice", 1), ("soya_kuzhambu", 2),
                    ("carrot_poriyal", 2), ("thayir_plain", 1)),
    "north_lunch": (("phulka", 5), ("soya_chunk_curry", 1), ("paneer_masala", 1)),
    "north_dinner": (("phulka", 3), ("soya_chunk_curry", 1),
                     ("aloo_sabzi", 1), ("onion_raita", 2)),
}


def _process_verified(process_key: str) -> bool:
    return citations.evidence(citations.constant(process_key).evidence_id).verified


def _old_rule(recipe, count) -> float:
    """The pre-D6 rule, restated in full so the before column is auditable.

        if any process constant is unverified: charge the whole recipe's energy
        else: charge nothing
    """

    for key in recipe.process_constants:
        if not _process_verified(key):
            return nutrition_of_recipe(recipe, count, lib.ingredients).energy_kcal
    return 0.0


def main() -> None:
    recipes = lib.recipes.recipes
    for plate, items in PLATES.items():
        print("=" * 100)
        print(f"{plate}")
        print("=" * 100)
        old = new = total = 0.0
        components = []
        for recipe_id, count in items:
            recipe = recipes[recipe_id]
            components.append((lib.recipes.component(recipe_id), count))
            r_energy = nutrition_of_recipe(recipe, count, lib.ingredients).energy_kcal
            r_old = _old_rule(recipe, count)
            total += r_energy
            old += r_old
            print(f"\n  {recipe_id} x{count}  ({r_energy:.1f} kcal)")
            r_new = 0.0
            for line in recipe.ingredients:
                ing = lib.ingredients[line.ingredient_id]
                energy = ing.for_grams(line.quantity_g).energy_kcal * count
                bad_comp = not ing.verified
                bad_proc = line.process_key is not None and not _process_verified(
                    line.process_key
                )
                # Union, not sum: a line can be unverified for both reasons and
                # its energy is still that much energy. Adding the two terms
                # would charge it twice and could push a plate past 100%, which
                # is not a thing a fraction of its own energy can do.
                charged = energy if (bad_comp or bad_proc) else 0.0
                r_new += charged
                why = ",".join(
                    w for w, f in (("composition", bad_comp), ("process", bad_proc)) if f
                ) or "-"
                # quantity x count, not the per-unit figure: the energy beside
                # it is for the whole serving, and two columns on different
                # bases in a transcript meant to be checked by hand is how a
                # reader concludes the arithmetic is wrong when it is not.
                print(f"    {line.ingredient_id:<22} {line.quantity_g * count:6.1f}g "
                      f"{energy:7.1f} kcal  verified={ing.verified!s:<5} "
                      f"process={line.process_key or '-':<28} charged={charged:7.1f} "
                      f"({why})")
            new += r_new
            print(f"    {'':<22} {'':>6}  {'':>7}       "
                  f"OLD charges {r_old:7.1f}   NEW charges {r_new:7.1f}")

        shipped = nutrition_of_components(components, lib.ingredients)
        print(f"\n  PLATE {plate}: {total:.1f} kcal")
        print(f"    OLD     {old:8.1f} / {total:.1f} = {old / total:6.1%}")
        print(f"    NEW     {new:8.1f} / {total:.1f} = {new / total:6.1%}")
        print(f"    SHIPPED {shipped.unverified_energy_kcal:8.1f} / "
              f"{shipped.point.energy_kcal:.1f} = "
              f"{shipped.unverified_energy_fraction():6.1%}"
              f"   <- must equal NEW once D6 lands")
        print()


if __name__ == "__main__":
    main()
