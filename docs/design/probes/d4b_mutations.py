"""D4b: every gate and guard in the planner, deleted one at a time.

Finding 26. Deleting the solver's quality gate left all 31 of slice 4's new
tests green, because the pre-filter caught everything first. A test that cannot
fail on the defect it names is not evidence, and the only way to know which
tests those are is to inject the defect and watch.

This probe is the inventory and the audit in one artifact. Each entry below
names one mechanism -- a conditional, an ordering, a clip, a construction-time
check -- and states the smallest edit that removes it. The harness applies each
edit to a throwaway git worktree, runs the suite, records whether anything went
red and which test went first, and reverts.

## Why a worktree and not the working tree

53 sequential edit-run-revert cycles against the real checkout is 53 chances to
leave the repo in a mutated state if anything interrupts the run. The worktree
is disposable and the real checkout is never written to.

## What SURVIVED means

Not "this mechanism is untested". It means: **no test in the suite fails when
this mechanism is deleted.** That is the finding-26 condition exactly. A
mechanism can have several tests named after it and still survive, which is
what happened with the solver's quality gate.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py

Optionally limit to one module, or to named mechanisms, while iterating:

    ... python docs/design/probes/d4b_mutations.py solver
    ... python docs/design/probes/d4b_mutations.py C3,V10,V11

## Which version of the code is measured: the working tree, not HEAD

``core/`` and ``tests/`` are both copied into the worktree from the **working
tree**. The worktree contributes isolation and nothing else, which was its only
stated job here anyway.

Changed 2026-08-09 (D4b-ii); it used to run whatever `git worktree add HEAD`
checked out. That could only grade already-committed code, which inverts the
order this whole practice requires: CLAUDE.md says to watch a test fail before
believing it, and a test you must commit before you can watch it is a test you
have already believed. The same applies to the mutations -- a row retargeted at
a line you just edited reports "pattern not found" against HEAD, which reads as
a harness error rather than as the stale-checkout it is.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

#: SGR escape sequences, stripped before any line is matched. See `_run_suite`.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

#: The deliberately-red test (D10). It fails before and after every mutation, so
#: leaving it in would mark all 53 mechanisms as covered by it.
DESELECT = (
    "tests/test_recipes.py::TestRecipeLoaderRules"
    "::test_declared_uncertainty_is_backed_by_registered_constants"
)


@dataclass(frozen=True)
class Mutation:
    """One mechanism, and the smallest edit that deletes it."""

    id: str
    module: str
    mechanism: str
    old: str
    new: str


CANDIDATES = "core/planner/candidates.py"
COMBINATIONS = "core/planner/combinations.py"
SOLVER = "core/planner/solver.py"
VALIDATOR = "core/planner/validator.py"
#: Not a planner module. Added for D6 (2026-08-09) because `CLAUDE.md`'s
#: deletion-testing convention points at this harness for *any* new gate, and
#: the unverified-energy attribution is a gate on whether anything can ever be
#: certified. The harness never cared which package a module was in.
NUTRITION_OF = "core/foods/nutrition_of.py"

MUTATIONS: tuple[Mutation, ...] = (
    # ---------------------------------------------------------------- candidates
    Mutation(
        "C1", CANDIDATES, "hard filter: diet pattern",
        "    if diet_pattern not in recipe.diet_patterns:\n        return False\n",
        "",
    ),
    Mutation(
        "C2", CANDIDATES, "hard filter: allergens",
        "    if recipe_allergens(recipe, ingredients) & allergens:\n        return False\n",
        "",
    ),
    Mutation(
        "C3", CANDIDATES, "hard filter: region or pan-Indian",
        "    if recipe.region not in (template.region, Region.PAN_INDIAN):\n"
        "        return False\n",
        "",
    ),
    Mutation(
        "C4", CANDIDATES, "hard filter: category accepted by template",
        "    if component.category not in template.categories():\n        return False\n",
        "",
    ),
    Mutation(
        "C5", CANDIDATES, "uncertainty eligibility ceiling comparison",
        "        if fraction > ceiling:",
        "        if False:",
    ),
    Mutation(
        "C6", CANDIDATES, "dev_mode decides exclude-vs-flag",
        "            if dev_mode:\n                flagged.extend(flags)\n"
        "            else:\n                excluded.extend(flags)\n                continue",
        "            flagged.extend(flags)",
    ),
    Mutation(
        "C7", CANDIDATES, "for_slot sorts by component id (finding 18)",
        "        out.sort(key=lambda component: component.id)\n",
        "",
    ),
    # C8 -- "for_slot deduplicates across categories" -- is gone, not skipped.
    # It survived the 2026-08-09 sweep because it was unreachable: a component
    # lives in exactly one `by_category` bucket, so no id repeats. D4b-ii
    # deleted the dedup rather than testing it (`docs/audit_log.md` finding 33),
    # so there is no longer a mechanism here to mutate. A row asserting an
    # absence would report "pattern not found" forever and teach the next
    # reader nothing.
    Mutation(
        "C9", CANDIDATES, "eligibility priced at min_count, not 1 (finding 27)",
        "        [(component, component.recipe.serving_unit.min_count)], ingredients",
        "        [(component, 1)], ingredients",
    ),
    # -------------------------------------------------------------- combinations
    Mutation(
        "B1", COMBINATIONS, "slot selection spans min..max, not just min",
        "    for size in range(slot.min_selections, slot.max_selections + 1):",
        "    for size in (slot.min_selections,):",
    ),
    Mutation(
        # KNOWN AND ACCEPTED SURVIVOR. `itertools.product` over an empty
        # sequence yields nothing, so deleting this early return leaves the
        # return value identical and no test can go red. Kept in the code and
        # kept as a row here, both deliberately (`docs/audit_log.md` finding
        # 33): what it protects is the log line naming the blocking slots,
        # which no assertion reads. A row whose expected result is "survives"
        # is worth more than no row -- it stops the next sweep re-discovering
        # it as news.
        "B2", COMBINATIONS, "unfillable required slot returns no combinations",
        "        # one call would also be strictly worse than either alone.\n        return ()",
        "        # one call would also be strictly worse than either alone.",
    ),
    Mutation(
        "B3", COMBINATIONS, "variety filter excludes recent recipe ids",
        "        if not (combo.recipe_ids() & recent_recipe_ids)\n",
        "",
    ),
    Mutation(
        "B4", COMBINATIONS, "macro_bounds low uses the unit's min_count",
        "    low = getattr(nutrition_of_recipe(component.recipe, unit.min_count, ingredients), macro)",
        "    low = getattr(nutrition_of_recipe(component.recipe, unit.max_count, ingredients), macro)",
    ),
    Mutation(
        "B5", COMBINATIONS, "quality_protein_bounds spans min..max count",
        "        quality_protein_of_recipe(component.recipe, unit.min_count, ingredients),",
        "        quality_protein_of_recipe(component.recipe, unit.max_count, ingredients),",
    ),
    Mutation(
        "B6", COMBINATIONS, "pre-filter discards combos that cannot reach a floor",
        "            if floor is not None and total_high < floor:",
        "            if False:",
    ),
    Mutation(
        "B7", COMBINATIONS, "pre-filter discards combos that must exceed a ceiling",
        "            if ceiling is not None and total_low > ceiling:",
        "            if False:",
    ),
    Mutation(
        "B8", COMBINATIONS, "pre-filter discards combos that cannot reach the quality floor",
        "            if reachable < quality_floor:",
        "            if False:",
    ),
    # ------------------------------------------------------------------- solver
    Mutation(
        "S1", SOLVER, "solver gate: macro floor",
        "        if floor is not None and value < floor:\n            return False",
        "        if False:\n            return False",
    ),
    Mutation(
        "S2", SOLVER, "solver gate: macro ceiling",
        "        if ceiling is not None and value > ceiling:\n            return False",
        "        if False:\n            return False",
    ),
    Mutation(
        "S3", SOLVER, "solver gate: quality-protein floor (finding 26's own case)",
        "    if quality_floor is not None and quality_protein_g < quality_floor:\n"
        "        return False",
        "    if False:\n        return False",
    ),
    Mutation(
        "S4", SOLVER, "scoring skips macros with no registered ideal point",
        "        if ideal is None:\n            continue",
        "        if ideal is None:\n            ideal = 0.0",
    ),
    Mutation(
        "S5", SOLVER, "search domain is the serving unit's legal counts",
        "    domains = [c.recipe.serving_unit.counts() for c in components]",
        "    domains = [range(1, c.recipe.serving_unit.max_count + 1) for c in components]",
    ),
    Mutation(
        "S6", SOLVER, "empty plate is still gated (0g of qualifying protein)",
        "        if not _within_target_point(point, target, 0.0):\n            return None",
        "        if False:\n            return None",
    ),
    Mutation(
        "S7", SOLVER, "unset quality protein defaults conservatively to 0.0",
        "    quality_protein_g: float = 0.0",
        "    quality_protein_g: float = 1e9",
    ),
    Mutation(
        "S8", SOLVER, "solve_combination keeps the best-scoring assignment",
        "        score = _deviation_point(point, target)\n"
        "        if best_items is None or score < best_score:",
        "        score = _deviation_point(point, target)\n"
        "        if best_items is None:",
    ),
    Mutation(
        "S9", SOLVER, "solve returns plans best-scoring first",
        "    solved.sort(key=lambda p: p.score)\n",
        "",
    ),
    Mutation(
        "S10", SOLVER, "swap_candidates skips the selection already in the plan",
        "            if frozenset(c.id for c in selection) == current_ids:\n"
        "                continue  # not actually a swap\n",
        "",
    ),
    Mutation(
        "S11", SOLVER, "a swap must keep the WHOLE plan valid, not just its slot",
        "                items = fixed_items + list(zip(selection, counts))",
        "                items = list(zip(selection, counts))",
    ),
    # ---------------------------------------------------------------- validator
    Mutation(
        "V1", VALIDATOR, "clinical flags contribute their locked macros",
        "        out |= LOCKED_CONSTRAINTS[flag]",
        "        out |= frozenset()",
    ),
    Mutation(
        "V2", VALIDATOR, "_capped clips a widened ceiling to the hard ceiling",
        "    return min(widened, hard_ceiling)",
        "    return widened",
    ),
    Mutation(
        "V3", VALIDATOR, "_widen_band leaves locked macros alone",
        "        if macro in locked:\n            continue\n        point = target.point(macro)",
        "        point = target.point(macro)",
    ),
    Mutation(
        "V4", VALIDATOR, "_widen_band leaves point-less macros alone",
        "        if point is None:",
        "        if point is not None and False:",
    ),
    Mutation(
        "V5", VALIDATOR, "band re-derived from the point, never scaled from the bound",
        "        lo, hi = band(point, tolerance)",
        "        lo, hi = band(ceilings.get(macro, point), tolerance)",
    ),
    Mutation(
        "V6", VALIDATOR, "replace() keeps fields no rung touches (e.g. the quality floor)",
        "    return replace(target, floors=floors, ceilings=ceilings)",
        "    return NutritionTarget(floors=floors, ceilings=ceilings, points=target.points)",
    ),
    Mutation(
        "V7", VALIDATOR, "rung 1 widens the sodium ceiling, never drops it",
        '        ceilings["sodium_mg"] = _capped(widened, hard)',
        '        del ceilings["sodium_mg"]',
    ),
    Mutation(
        "V8", VALIDATOR, "the bound_source follows the number when the guard clips it",
        '            sources["sodium_mg"] = "absurdity_guard"',
        "            pass",
    ),
    Mutation(
        "V9", VALIDATOR, "rung 1 skips sodium when a flag locks it",
        '    if "sodium_mg" in ceilings and "sodium_mg" not in locked:',
        '    if "sodium_mg" in ceilings:',
    ),
    Mutation(
        "V10", VALIDATOR, "rung 4 skips protein entirely when a flag locks it",
        '    if "protein_g" in locked:\n        return target\n',
        "",
    ),
    Mutation(
        "V11", VALIDATOR, "rung 4 lowers the floor only, never raises the ceiling",
        '    floors["protein_g"] = point * (1.0 - fraction)\n    return replace(target, floors=floors)',
        '    floors["protein_g"] = point * (1.0 - fraction)\n'
        "    ceilings = dict(target.ceilings)\n"
        '    if "protein_g" in ceilings:\n'
        '        ceilings["protein_g"] = ceilings["protein_g"] * (1.0 + fraction)\n'
        "    return replace(target, floors=floors, ceilings=ceilings)",
    ),
    Mutation(
        "V12", VALIDATOR, "the ladder runs in CLAUDE.md's order",
        "    for step in RELAXATION_ORDER:",
        "    for step in tuple(reversed(RELAXATION_ORDER)):",
    ),
    Mutation(
        "V13", VALIDATOR, "a fully-locked rung is skipped, not merely ineffective",
        "        if step.is_fully_locked(locked):",
        "        if False:",
    ),
    Mutation(
        "V14", VALIDATOR, "relaxed protein without a disclosure is a construction error",
        '        if protein_relaxed and not (self.disclosure or "").strip():',
        "        if False:",
    ),
    Mutation(
        "V15", VALIDATOR, "a failed result must name a violation",
        "            if not self.violations:",
        "            if False:",
    ),
    Mutation(
        "V16", VALIDATOR, "a failed result must carry a disclosure",
        '            if not (self.disclosure or "").strip():\n'
        "                raise ValueError(\n"
        '                    "a failed ValidationResult must explain the decline to the user"\n'
        "                )",
        "            pass",
    ),
    Mutation(
        "V17", VALIDATOR, "Violation.reach is validated against its vocabulary",
        "        if self.reach not in VIOLATION_REACH:",
        "        if False:",
    ),
    Mutation(
        "V18", VALIDATOR, "Violation.relaxability is validated against its vocabulary",
        "        if self.relaxability not in VIOLATION_RELAXABILITY:",
        "        if False:",
    ),
    Mutation(
        "V19", VALIDATOR, "blocking_slots only on a no_candidates violation",
        '        if self.blocking_slots and self.kind != "no_candidates":',
        "        if False:",
    ),
    Mutation(
        "V20", VALIDATOR, "bound_source is read off the target, never inferred",
        '    return target.bound_sources.get(macro, "meal_share")',
        '    return "meal_share"',
    ),
    Mutation(
        "V21", VALIDATOR, "the gate reads the POINT estimate, never the interval",
        "    estimate = plan.estimate\n    violations = _violations_for(\n        estimate.point,",
        "    estimate = plan.estimate\n    violations = _violations_for(\n        estimate.low,",
    ),
    Mutation(
        "V22", VALIDATOR, "the protein disclosure keeps one decimal",
        'f"This plan delivers {actual:.1f}{unit} of protein against a "',
        'f"This plan delivers {actual:.0f}{unit} of protein against a "',
    ),
    Mutation(
        "V23", VALIDATOR, "_reach reuses the pre-filter's own component bounds",
        "            c_lo, c_hi = macro_bounds(component, macro, ingredients)",
        "            c_lo, c_hi = 0.0, float(\"inf\")",
    ),
    Mutation(
        "V24", VALIDATOR, "the pre-filter re-runs against each rung's widened target",
        "        return solve(feasible_combinations(combinations, t, ingredients), t, ingredients)",
        "        return solve(feasible_combinations(combinations, target, ingredients), t, ingredients)",
    ),
    Mutation(
        "V25", VALIDATOR, "a disclosure-requiring rung produces a disclosure",
        "        if any(\n            s.requires_disclosure for s in RELAXATION_ORDER if s.name in applied\n        ):",
        "        if False:",
    ),
    Mutation(
        "V26", VALIDATOR, "the ladder stops at the first rung that solves",
        "        solved = _attempt(current)\n        if not solved:\n            continue",
        "        solved = _attempt(current)\n        if not solved or True:\n            continue",
    ),
    Mutation(
        "V27", VALIDATOR, "a locked blocking bound adds the clinical sentence",
        "    if locked_hits:",
        "    if False:",
    ),
    # ------------------------------------------------- nutrition_of (D6)
    # Finding 20's fix. Note the real library cannot grade any of these: every
    # ingredient row but `water` is unverified and `water` has no energy, so
    # every real plate is 100% unverified under the correct rule AND under most
    # broken ones. The tests these rows grade build their own mixed data; see
    # `tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution`.
    Mutation(
        "N1", NUTRITION_OF, "unverified ingredient composition is charged",
        "        unverified_composition = not ing.verified\n",
        "        unverified_composition = False\n",
    ),
    Mutation(
        "N2", NUTRITION_OF, "an unverified process constant charges its line",
        "        unverified_process = line.process_key is not None and not "
        "_process_verified(\n            line.process_key\n        )\n",
        "        unverified_process = False\n",
    ),
    Mutation(
        "N3", NUTRITION_OF, "a doubly-unverified line is charged once, not twice",
        "        if unverified_composition or unverified_process:\n"
        "            total += ing.for_grams(line.quantity_g).energy_kcal * unit_count\n",
        "        if unverified_composition:\n"
        "            total += ing.for_grams(line.quantity_g).energy_kcal * unit_count\n"
        "        if unverified_process:\n"
        "            total += ing.for_grams(line.quantity_g).energy_kcal * unit_count\n",
    ),
    Mutation(
        "N4", NUTRITION_OF, "attribution is per line, not per whole recipe",
        "            total += ing.for_grams(line.quantity_g).energy_kcal * unit_count\n"
        "    return total\n",
        "            return sum(\n"
        "                _ingredient(ingredients, other.ingredient_id)\n"
        "                .for_grams(other.quantity_g).energy_kcal * unit_count\n"
        "                for other in recipe.ingredients\n"
        "            )\n"
        "    return total\n",
    ),
    Mutation(
        "N5", NUTRITION_OF, "the charge scales with the serving count",
        "            total += ing.for_grams(line.quantity_g).energy_kcal * unit_count\n",
        "            total += ing.for_grams(line.quantity_g).energy_kcal\n",
    ),
)


#: Which test files count as *correctly scoped* for a module's mechanisms —
#: a test that knows what it is protecting. Everything not listed here
#: (`test_planner_plan.py`, the API suites, the web suites) is end-to-end: it
#: exercises these mechanisms in passing and will report red if one breaks, but
#: nobody editing it would know that, so it cannot be relied on to keep them.
#:
#: This mapping is a judgement, made once and written down rather than applied
#: silently per row. `test_planner_plan.py` is deliberately NOT scoped to any
#: module: it is the wiring test, and its own docstring says so.
OWN_TESTS: dict[str, tuple[str, ...]] = {
    CANDIDATES: ("test_planner_candidates.py", "test_planner_determinism.py"),
    COMBINATIONS: ("test_planner_combinations.py", "test_planner_determinism.py"),
    SOLVER: ("test_planner_solver.py", "test_planner_quality.py"),
    VALIDATOR: (
        "test_planner_validator.py", "test_planner_decline.py",
        "test_planner_quality.py",
    ),
    # `test_recipes.py` is scoped here too: it is where the derived-uncertainty
    # rules live, and a reader editing it knows they are editing evidence
    # attribution. `test_planner_*` is not — a planner test that goes red on an
    # attribution change is reporting a coincidence.
    NUTRITION_OF: ("test_nutrition_of.py", "test_recipes.py"),
}


def _run_suite(worktree: Path) -> tuple[str, ...]:
    """Every failing test id. Empty means the mutation survived.

    Deliberately NOT ``-x``. The first failure under ``-x`` is the first in
    pytest's collection order, which is alphabetical by filename and has nothing
    to do with which test is actually about the mechanism. Classifying from it
    reports whichever file sorts earliest: deleting the solver's quality gate
    stops at ``test_planner_plan.py`` and never reaches
    ``test_planner_quality.py::TestTheSolverGateItself``, which is the test that
    genuinely covers it. Reading that as "held up by a wiring test" would have
    been exactly backwards, so the whole suite runs every time.
    """

    proc = subprocess.run(
        # --color=no and the strip below are belt and braces, added 2026-08-09
        # after a sweep returned "(non-test failure)" for all nine rows it ran.
        # pytest had emitted its summary as "\x1b[31mFAILED\x1b[0m tests/...",
        # so `startswith("FAILED ")` matched nothing and every mutation looked
        # like a crash. The tests had failed exactly as intended; only the
        # parser was blind. Colour is off by default when stdout is a pipe, so
        # this depends on the *inherited environment* (FORCE_COLOR / PY_COLORS)
        # -- meaning the harness could report differently for the same code
        # depending on which shell launched it, which is precisely the kind of
        # unreproducible measurement this probe exists to avoid.
        [sys.executable, "-m", "pytest", "tests/", "-q", "--color=no",
         "-p", "no:cacheprovider", "--deselect", DESELECT],
        cwd=worktree, capture_output=True, text=True,
        env={**os.environ, "FORCE_COLOR": "0", "PY_COLORS": "0", "NO_COLOR": "1"},
    )
    if proc.returncode == 0:
        return ()
    lines = [_ANSI.sub("", line) for line in proc.stdout.splitlines()]
    failed = tuple(
        line.split(" ", 1)[1].split(" - ")[0].strip()
        for line in lines
        if line.startswith("FAILED ") or line.startswith("ERROR ")
    )
    # A collection error or interpreter-level failure is still red.
    return failed or ("(non-test failure; see output)",)


#: Test classes that sit in a correctly-scoped file but behave like end-to-end
#: tests: they pin an exact plate from the real library, so almost any change
#: anywhere in the planner breaks them. They are valuable — they are how D3 and
#: slice 4 proved which plate a profile actually gets — but they are not
#: evidence that a specific mechanism is protected, because they would go red
#: whatever broke. Counting them as scoped made "covered" an upper bound; this
#: exclusion is what makes the number mean what it says.
UNSCOPED_CLASSES: tuple[str, ...] = ("TestAgainstTheRealLibrary",)


def _classify(mutation: Mutation, failures: tuple[str, ...]) -> str:
    """covered | soft-covered | SURVIVED."""

    if not failures:
        return "SURVIVED"
    scoped = OWN_TESTS.get(mutation.module, ())
    if any(_is_scoped(f, scoped) for f in failures):
        return "covered"
    return "soft-covered"


def _is_scoped(failure: str, scoped: tuple[str, ...]) -> bool:
    if not any(name in failure for name in scoped):
        return False
    return not any(cls in failure for cls in UNSCOPED_CLASSES)


def _selected(mutation: Mutation, only: str) -> bool:
    """``only`` is a module substring ("solver") or a comma-separated id list."""

    if not only:
        return True
    tokens = [t.strip() for t in only.split(",") if t.strip()]
    return any(t == mutation.id or t in mutation.module for t in tokens)


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    worktree = REPO / ".d4b_worktree"
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
                   cwd=REPO, capture_output=True, text=True, check=True)
    # See the module docstring: the working tree, not HEAD.
    for tree in ("core", "tests"):
        shutil.rmtree(worktree / tree, ignore_errors=True)
        shutil.copytree(
            REPO / tree, worktree / tree,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
        )
    rows: list[tuple[Mutation, str, str]] = []
    try:
        for mutation in MUTATIONS:
            if not _selected(mutation, only):
                continue
            path = worktree / mutation.module
            original = path.read_text(encoding="utf-8")
            if mutation.old not in original:
                rows.append((mutation, "ERROR", "pattern not found in source"))
                print(f"{mutation.id:4s} ERROR    pattern not found", flush=True)
                continue
            if original.count(mutation.old) > 1:
                rows.append((mutation, "ERROR", "pattern is not unique"))
                print(f"{mutation.id:4s} ERROR    pattern not unique", flush=True)
                continue
            path.write_text(original.replace(mutation.old, mutation.new), encoding="utf-8")
            try:
                failures = _run_suite(worktree)
            finally:
                path.write_text(original, encoding="utf-8")
            status = _classify(mutation, failures)
            scoped = OWN_TESTS.get(mutation.module, ())
            # For a soft-covered row, the useful detail is what caught it
            # incidentally; for a covered row, which correctly-scoped test did.
            if status == "covered":
                note = next(f for f in failures if _is_scoped(f, scoped))
            elif status == "soft-covered":
                note = f"{len(failures)} incidental: {failures[0]}"
            else:
                note = ""
            rows.append((mutation, status, note))
            print(f"{mutation.id:4s} {status:12s} {note}", flush=True)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                       cwd=REPO, capture_output=True, text=True)

    print("=" * 100)
    buckets = {name: [r for r in rows if r[1] == name]
               for name in ("covered", "soft-covered", "SURVIVED", "ERROR")}
    print(f"{len(rows)} mechanisms: "
          f"{len(buckets['covered'])} covered, "
          f"{len(buckets['soft-covered'])} soft-covered, "
          f"{len(buckets['SURVIVED'])} SURVIVED, "
          f"{len(buckets['ERROR'])} harness errors.")
    for name in ("soft-covered", "SURVIVED", "ERROR"):
        for mutation, _, note in buckets[name]:
            print(f"  {name:12s} {mutation.id:4s} {mutation.module.split('/')[-1]:18s} "
                  f"{mutation.mechanism}")
            if note:
                print(f"               {note}")


if __name__ == "__main__":
    main()
