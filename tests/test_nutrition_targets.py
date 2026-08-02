"""Profile -> target derivation.

Every expected value is hand-computed from the registered constants and the
published equations, with the arithmetic shown in a comment (CLAUDE.md,
"Conventions"). Never a snapshot of current output. The constant values used in
the arithmetic below are pinned in ``test_the_target_constants_are_exactly_these``
so that if one changes, exactly one test's arithmetic has to be revisited on
purpose rather than silently.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from core.nutrition import citations
from core.nutrition.targets import (
    _compute_macros,
    _energy_uncertainty,
    bmr_mifflin_st_jeor,
    compute_protein,
    derive_target,
    energy_target,
    tdee,
)
from core.schemas import ActivityLevel, ClinicalFlag, DietPattern, Goal, Profile, Sex


def _make(
    *,
    weight_kg=70.0,
    height_cm=175.0,
    age_years=28,
    sex=Sex.MALE,
    activity=ActivityLevel.MODERATE,
    goal=Goal.MAINTAIN,
    diet=DietPattern.NON_VEGETARIAN,
    clinical_flags=frozenset(),
) -> Profile:
    return Profile(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age_years=age_years,
        sex=sex,
        activity=activity,
        goal=goal,
        diet=diet,
        clinical_flags=clinical_flags,
    )


class TestBMR:
    def test_mifflin_male(self):
        # 10*70 + 6.25*175 - 5*28 + 5 = 700 + 1093.75 - 140 + 5 = 1658.75
        assert bmr_mifflin_st_jeor(_make()) == pytest.approx(1658.75)

    def test_mifflin_female_uses_the_minus_161_constant(self):
        # 10*55 + 6.25*160 - 5*30 - 161 = 550 + 1000 - 150 - 161 = 1239.0
        p = _make(weight_kg=55.0, height_cm=160.0, age_years=30, sex=Sex.FEMALE)
        assert bmr_mifflin_st_jeor(p) == pytest.approx(1239.0)


class TestTDEEAndEnergy:
    def test_tdee_applies_the_activity_factor(self):
        # BMR 1658.75 * moderate PAL 1.55 = 2571.0625
        assert tdee(_make()) == pytest.approx(2571.0625)

    def test_very_active_multiplies_more_than_sedentary(self):
        # 1658.75 * 1.9 = 3151.625
        p = _make(activity=ActivityLevel.VERY_ACTIVE)
        assert tdee(p) == pytest.approx(3151.625)

    def test_maintain_goal_leaves_tdee_unchanged(self):
        # goal factor 1.0
        assert energy_target(_make(goal=Goal.MAINTAIN)) == pytest.approx(2571.0625)

    def test_lose_fat_applies_a_20_percent_deficit(self):
        # 2571.0625 * 0.80 = 2056.85
        assert energy_target(_make(goal=Goal.LOSE_FAT)) == pytest.approx(2056.85)

    def test_gain_muscle_applies_a_10_percent_surplus(self):
        # 2571.0625 * 1.10 = 2828.16875
        assert energy_target(_make(goal=Goal.GAIN_MUSCLE)) == pytest.approx(2828.16875)


class TestProteinIsQualityAdjusted:
    def test_non_vegetarian_diaas_is_unity_so_no_adjustment(self):
        # 70 kg * 1.6 g/kg = 112.0 g; DIAAS 1.0 -> 112.0 / 1.0 = 112.0
        pt = compute_protein(_make(diet=DietPattern.NON_VEGETARIAN))
        assert pt.base_g == pytest.approx(112.0)
        assert pt.quality_adjusted_g == pytest.approx(112.0)

    def test_vegan_needs_more_grams_for_the_same_utilisable_protein(self):
        # base 112.0 g; vegan DIAAS 0.75 -> 112.0 / 0.75 = 149.333...
        pt = compute_protein(_make(diet=DietPattern.VEGAN))
        assert pt.quality_adjusted_g == pytest.approx(112.0 / 0.75)

    def test_quality_adjustment_orders_diets_by_protein_quality(self):
        # Same body, five diets. Lower DIAAS => more grams required. This is the
        # "Protein, quality-adjusted" claim: a vegan plate must deliver more.
        grams = {
            diet: compute_protein(_make(diet=diet)).quality_adjusted_g
            for diet in DietPattern
        }
        assert (
            grams[DietPattern.NON_VEGETARIAN]
            < grams[DietPattern.EGGETARIAN]
            < grams[DietPattern.VEGETARIAN]
            < grams[DietPattern.JAIN]
            < grams[DietPattern.VEGAN]
        )

    def test_lose_fat_raises_g_per_kg_above_maintenance(self):
        # maintain 1.6 -> 112 g; lose_fat 1.8 -> 70*1.8 = 126 g (before DIAAS).
        assert compute_protein(_make(goal=Goal.MAINTAIN)).base_g == pytest.approx(112.0)
        assert compute_protein(_make(goal=Goal.LOSE_FAT)).base_g == pytest.approx(126.0)


class TestMacros:
    def test_fat_is_the_amdr_midpoint_and_carb_is_the_remainder(self):
        # AMDR fat midpoint = (0.20 + 0.35) / 2 = 0.275 of energy.
        # At energy 2000, protein 112 g:
        #   fat_energy  = 0.275 * 2000 = 550 kcal -> 550 / 9  = 61.111... g
        #   protein_energy = 112 * 4 = 448 kcal
        #   carb_energy = 2000 - 448 - 550 = 1002 kcal -> 1002 / 4 = 250.5 g
        fat_g, carb_g, warnings = _compute_macros(2000.0, 112.0)
        assert fat_g == pytest.approx(550.0 / 9.0)
        assert carb_g == pytest.approx(250.5)
        assert warnings == ()

    def test_carb_floors_at_zero_and_warns_when_protein_plus_fat_exceed_energy(self):
        # energy 1500, protein 360 g: protein_energy = 1440, fat = 0.275*1500 = 412.5,
        # carb_energy = 1500 - 1440 - 412.5 = -352.5 < 0 -> floor to 0, record a warning.
        fat_g, carb_g, warnings = _compute_macros(1500.0, 360.0)
        assert carb_g == 0.0
        assert len(warnings) == 1
        assert "exceed" in warnings[0]


class TestEnergyInterval:
    def test_uncertainty_is_rmr_and_pal_in_quadrature(self):
        # sqrt(0.10^2 + 0.10^2) = sqrt(0.02) = 0.141421...
        assert _energy_uncertainty(_make()) == pytest.approx(math.sqrt(0.02))

    def test_interval_brackets_the_point_symmetrically(self):
        dt = derive_target(_make())
        lo, hi = dt.energy_interval()
        assert lo < dt.energy_kcal < hi
        assert lo == pytest.approx(dt.energy_kcal * (1 - dt.energy_uncertainty))
        assert hi == pytest.approx(dt.energy_kcal * (1 + dt.energy_uncertainty))


class TestDeriveTargetIntegration:
    def test_protein_floor_is_the_base_grams_not_the_quality_adjusted_ones(self):
        # Inverted 2026-08-02 (slice 2, the DIAAS reversal). This test used to
        # assert the opposite and its comment read "the number a plan must
        # actually deliver, not the pre-adjustment base".
        #
        # The vegan profile is deliberately the one exercised: DIAAS 0.75 is the
        # largest adjustment in the registry, so base and quality-adjusted are
        # 149.33 and 112.0 -- far enough apart that the assertion cannot pass by
        # coincidence the way it would on a non-vegetarian profile, where DIAAS
        # is 1.0 and the two figures are equal.
        dt = derive_target(_make(diet=DietPattern.VEGAN))
        assert dt.nutrition_target.floor("protein_g") == pytest.approx(
            dt.protein.base_g
        )
        assert dt.protein.quality_adjusted_g > dt.protein.base_g, (
            "the adjustment must still be computed and inspectable; only its "
            "use as the target was removed"
        )
        assert dt.nutrition_target.floor("protein_g") < dt.protein.quality_adjusted_g

    def test_diet_pattern_no_longer_moves_the_protein_floor(self):
        # The load-bearing consequence, asserted directly rather than left to be
        # inferred from the test above: between slice 2 and the quality-source
        # rule (slice 4), protein quality influences nothing. Two profiles
        # identical but for diet get the same floor.
        #
        # This is a real gap and the test exists to make it visible rather than
        # to bless it -- when slice 4 lands, quality must start mattering again
        # somewhere, and if it does not, this assertion is the one that should
        # look wrong to whoever reads it next.
        floors = {
            diet: derive_target(_make(diet=diet)).nutrition_target.floor("protein_g")
            for diet in DietPattern
        }
        assert len(set(floors.values())) == 1, floors

    def test_the_carb_target_moved_with_the_protein_floor(self):
        # The side effect, asserted on its own terms because nobody asked for
        # it. _compute_macros derives carbohydrate as the energy REMAINDER after
        # protein and fat, so removing 12.44 g of claimed protein hands 49.8
        # kcal back to carbohydrate. A slice-2 test that checked only protein
        # would pass while this shipped unnoticed, which is exactly why
        # docs/design/target_model_v2.md flags it as the correctness risk.
        #
        # Hand-computed for the reference profile (70 kg / 175 cm / 28 / male /
        # moderate / maintain / vegetarian), energy 2571.1 kcal, fat 707.05 kcal:
        #
        #   protein day floor = 70 * 1.6                      = 112.00 g
        #   carb energy       = 2571.1 - 112.00*4 - 707.05    = 1416.05 kcal
        #   carb day          = 1416.05 / 4                   = 354.01 g
        #
        # Under the old inflated protein (112.0 / 0.9 = 124.44 g) the same
        # arithmetic gave 1366.29 / 4 = 341.57 g, so the target rose by 12.44 g
        # -- one gram of carbohydrate per gram of protein no longer claimed,
        # which is the 4 kcal/g identity and a useful cross-check on the sign.
        veg = derive_target(_make(diet=DietPattern.VEGETARIAN))
        assert veg.protein.base_g == pytest.approx(112.00)
        assert veg.carb_g == pytest.approx(354.01, abs=0.01)
        # Cross-check on the sign and size: the rise equals the protein no
        # longer claimed, at 4 kcal/g for both macros.
        assert veg.carb_g - 341.57 == pytest.approx(
            veg.protein.quality_adjusted_g - veg.protein.base_g, abs=0.01
        )

    def test_the_carb_target_is_now_diet_independent_too(self):
        # A second-order consequence nobody predicted, and the one worth
        # pinning: carbohydrate used to vary with diet pattern, because it was
        # the remainder after a DIAAS-inflated protein figure. A vegan and a
        # non-vegetarian of identical body and goal were handed carb targets
        # 37 g apart on the strength of a protein-quality constant.
        #
        # base_g does not depend on diet, so neither does the remainder. Diet
        # now changes no target value at all -- see
        # test_diet_pattern_no_longer_moves_the_protein_floor for the other half
        # and docs/methodology.md for why that gap is stated rather than fixed
        # here.
        carbs = {
            diet: derive_target(_make(diet=diet)).carb_g for diet in DietPattern
        }
        assert len(set(round(c, 6) for c in carbs.values())) == 1, carbs

    def test_energy_floor_ceiling_are_the_default_five_percent_band(self):
        # simple_target uses tolerance.energy_default (0.05) for the band.
        dt = derive_target(_make())
        e = dt.energy_kcal
        assert dt.nutrition_target.floor("energy_kcal") == pytest.approx(e * 0.95)
        assert dt.nutrition_target.ceiling("energy_kcal") == pytest.approx(e * 1.05)

    def test_nothing_ships_as_validated_today(self):
        # Every backing constant rests on verified=False evidence, so the honest
        # status is dev_mode with a disclosure. This is asserted, not assumed:
        # CLAUDE.md's round-4 addendum requires dev_mode be distinct from validated.
        dt = derive_target(_make())
        assert dt.status == "dev_mode"
        assert dt.disclosure and "not validated" in dt.disclosure

    def test_profile_warnings_propagate_into_the_target(self):
        # weight 300 kg is out of the plausible-adult range -> Profile warns,
        # and the derived target must carry that caveat, not drop it.
        p = _make(weight_kg=300.0)
        dt = derive_target(p)
        assert any("outside the usual adult range" in w for w in dt.warnings)


class TestClinicalFlagsDoNotTightenTargets:
    """docs/methodology.md, "Clinical flags do not tighten a target" (2026-07-23).

    core/nutrition cannot see core/planner's LOCKED_CONSTRAINTS mapping
    (downward-dependency rule), and no clinical-specific sodium/protein/carb
    constant is registered yet, so a flagged profile gets the exact same
    numbers as an unflagged one today. The only thing that must change is a
    mandatory disclosure, so the gap is structural rather than a paragraph
    nobody reads before a UI checkbox ships next to a number.
    """

    def test_hypertension_flag_does_not_change_the_sodium_ceiling(self):
        plain = derive_target(_make())
        flagged = derive_target(_make(clinical_flags=frozenset({ClinicalFlag.HYPERTENSION})))
        assert flagged.sodium_mg_max == pytest.approx(plain.sodium_mg_max)
        assert flagged.nutrition_target.ceiling("sodium_mg") == pytest.approx(
            plain.nutrition_target.ceiling("sodium_mg")
        )

    def test_flagged_profile_carries_a_mandatory_disclosure(self):
        dt = derive_target(_make(clinical_flags=frozenset({ClinicalFlag.HYPERTENSION})))
        assert any("hypertension" in w and "general-population" in w for w in dt.warnings)

    def test_unflagged_profile_carries_no_such_warning(self):
        dt = derive_target(_make())
        assert not any("general-population" in w for w in dt.warnings)


class TestEnumKeysAllResolve:
    """The f-string key construction must have a constant for every enum member.

    A renamed enum member or a missing constant would raise KeyError here rather
    than silently reading the wrong number at runtime.
    """

    def test_every_activity_level_has_a_pal_constant(self):
        for a in ActivityLevel:
            citations.constant(f"activity.pal_{a.value}")  # raises if missing

    def test_every_goal_has_energy_and_protein_constants(self):
        for g in Goal:
            citations.constant(f"energy.goal_factor_{g.value}")
            citations.constant(f"protein.g_per_kg_{g.value}")

    def test_every_diet_has_a_diaas_constant(self):
        for d in DietPattern:
            citations.constant(f"diaas.{d.value}")


class TestPerturbationMovesTheOutput:
    """CLAUDE.md round-4: perturb an input and check the output actually moves,
    not merely that the rule is mentioned. Mutating a registered constant must
    change the derived target that depends on it."""

    def test_changing_the_activity_factor_changes_tdee_proportionally(self, monkeypatch):
        base = tdee(_make())
        doubled = dataclasses.replace(
            citations.constant("activity.pal_moderate"),
            value=citations.value_of("activity.pal_moderate") * 2,
        )
        monkeypatch.setitem(citations._CONSTANTS, "activity.pal_moderate", doubled)
        assert tdee(_make()) == pytest.approx(base * 2)

    def test_status_is_computed_from_evidence_not_hard_coded(self, monkeypatch):
        # Prove status reacts to the evidence: with a source's evidence flipped
        # to verified, _status_and_disclosure sees the change (it reads the
        # registry live). Uses a single real-source constant to show the wiring
        # without needing every source verified.
        ev = citations.evidence(
            citations.constant("bmr.mifflin.weight_coeff").evidence_id
        )
        assert ev.verified is False
        monkeypatch.setitem(
            citations._EVIDENCE, ev.id, dataclasses.replace(ev, verified=True)
        )
        assert (
            citations.evidence(
                citations.constant("bmr.mifflin.weight_coeff").evidence_id
            ).verified
            is True
        )

    def test_targets_can_never_be_validated_while_they_rest_on_project_estimates(
        self, monkeypatch
    ):
        # The honest conclusion, asserted: verifying every real source (Mifflin,
        # Morton, IOM, WHO) is NOT enough, because the activity, DIAAS and goal
        # factors are PROJECT_ESTIMATE/DECISION evidence that can never be marked
        # verified (Evidence forbids it). So status stays dev_mode even in the
        # best case. docs/methodology.md states this plainly.
        for ev in citations.all_evidence():
            if ev.grade not in (
                citations.Grade.PROJECT_ESTIMATE,
                citations.Grade.PROJECT_DECISION,
            ):
                monkeypatch.setitem(
                    citations._EVIDENCE, ev.id, dataclasses.replace(ev, verified=True)
                )
        assert derive_target(_make()).status == "dev_mode"


def test_the_target_constants_are_exactly_these():
    """Pins the constant values the arithmetic in this file depends on.

    Changing any of these means deliberately editing this test and saying why in
    the commit — the same discipline test_nutrition_of.py applies to its
    load-bearing constants. Uses value_of so a value edited in citations.py fails
    here loudly rather than drifting a hand-computed expectation out of date.
    """

    assert citations.value_of("bmr.mifflin.weight_coeff") == 10.0
    assert citations.value_of("bmr.mifflin.height_coeff") == 6.25
    assert citations.value_of("bmr.mifflin.age_coeff") == 5.0
    assert citations.value_of("bmr.mifflin.sex_constant_male") == 5.0
    assert citations.value_of("bmr.mifflin.sex_constant_female") == -161.0
    assert citations.value_of("activity.pal_moderate") == 1.55
    assert citations.value_of("activity.pal_very_active") == 1.9
    assert citations.value_of("protein.g_per_kg_maintain") == 1.6
    assert citations.value_of("protein.g_per_kg_lose_fat") == 1.8
    assert citations.value_of("diaas.non_vegetarian") == 1.0
    assert citations.value_of("diaas.vegan") == 0.75
    assert citations.value_of("energy.goal_factor_lose_fat") == 0.80
    assert citations.value_of("energy.goal_factor_gain_muscle") == 1.10
    assert citations.value_of("macro.fat_energy_fraction_min") == 0.20
    assert citations.value_of("macro.fat_energy_fraction_max") == 0.35
    assert citations.value_of("nutrient.fibre_g_per_1000kcal") == 14.0
    assert citations.value_of("nutrient.sodium_max_mg") == 2000.0


def test_every_target_source_rests_on_unverified_evidence_today():
    # The honest basis for status == dev_mode. If someone verifies a source,
    # this test tells them which invariant to revisit.
    from core.nutrition.targets import _SOURCE_KEYS

    for key in _SOURCE_KEYS:
        ev = citations.evidence(citations.constant(key).evidence_id)
        assert ev.verified is False, f"{key} unexpectedly rests on verified evidence"
