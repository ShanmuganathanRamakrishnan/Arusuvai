"""The citation defence: phenomenon present, mechanism reviewed, honesty kept.

The dangerous failure this guards against is not a fabricated DOI — anyone can
look one of those up. It is a real, findable, correctly-formatted citation that
describes the wrong physical process, which passes every automated check the
registry can perform. Hence the human-reviewed mechanism checklist below rather
than a purely mechanical assertion.
"""

from __future__ import annotations

import pytest

from core.foods import retention
from core.nutrition import citations


class TestEvidence:
    def test_every_evidence_states_a_phenomenon(self):
        for ev in citations.all_evidence():
            assert ev.phenomenon.strip(), f"{ev.id} has no phenomenon"

    def test_phenomenon_is_not_a_copy_of_the_summary(self):
        # If the two are identical, nobody actually wrote down what was
        # measured — they restated what the source is about.
        for ev in citations.all_evidence():
            assert ev.phenomenon.strip().lower() != ev.summary.strip().lower()

    def test_empty_phenomenon_is_impossible_input(self):
        with pytest.raises(ValueError, match="phenomenon"):
            citations.Evidence(
                id="x",
                summary="s",
                phenomenon="   ",
                source="somewhere",
                grade=citations.Grade.TEXTBOOK,
            )

    def test_a_project_estimate_can_never_be_marked_verified(self):
        # There is no source document to open, so "verified" would be a lie
        # with nothing behind it.
        with pytest.raises(ValueError, match="verified"):
            citations.Evidence(
                id="y",
                summary="s",
                phenomenon="p",
                source="us",
                grade=citations.Grade.PROJECT_ESTIMATE,
                verified=True,
            )


class TestConstants:
    def test_every_constant_resolves_to_registered_evidence(self):
        for c in citations.all_constants():
            assert citations.evidence(c.evidence_id)

    def test_every_constant_states_where_it_is_applied(self):
        for c in citations.all_constants():
            assert c.applied_to.strip(), f"{c.key} does not say what it is applied to"

    def test_registering_against_missing_evidence_is_refused(self):
        with pytest.raises(ValueError, match="unregistered evidence"):
            citations.register_constant(
                citations.Constant(
                    key="bogus.key",
                    value=1.0,
                    unit="x",
                    evidence_id="no_such_evidence",
                    applied_to="nothing",
                    uncertainty=0.0,
                )
            )

    def test_unknown_constant_lookup_says_what_to_do_instead(self):
        with pytest.raises(KeyError, match="may not"):
            citations.value_of("yield.something_i_made_up")


class TestMechanismReview:
    """Manual-review checklist, per the Phase 1 acceptance criteria.

    ``REVIEWED_MECHANISM_MATCHES`` records that a person read each evidence's
    ``phenomenon`` beside the constant's ``applied_to`` and judged them the same
    mechanism. This test asserts the checklist is complete and has not drifted.
    """

    def test_no_constant_escapes_mechanism_review(self):
        assert citations.mechanism_mismatches() == ()

    def test_checklist_has_no_entries_for_constants_that_no_longer_exist(self):
        keys = {c.key for c in citations.all_constants()}
        stale = set(citations.REVIEWED_MECHANISM_MATCHES) - keys
        assert stale == set(), f"stale mechanism-review entries: {sorted(stale)}"

    def test_the_deep_fry_citation_is_recorded_as_rejected_not_used(self):
        # A griddled dosa picks oil up off a tawa; deep-fried potato absorbs it
        # into a crust during post-fry cooling. Different mechanism, so the
        # (real, findable) paper is recorded here as refused rather than cited.
        rejected = {r.for_constant for r in citations.REJECTED_CITATIONS}
        assert "oil_uptake.dosa_griddled" in rejected
        entry = next(
            r
            for r in citations.REJECTED_CITATIONS
            if r.for_constant == "oil_uptake.dosa_griddled"
        )
        assert "deep" in entry.phenomenon_measured.lower() or "fried" in entry.phenomenon_measured.lower()
        assert entry.why_rejected.strip()

    def test_the_dosa_oil_constant_is_honestly_unverified(self):
        c = citations.constant("oil_uptake.dosa_griddled")
        ev = citations.evidence(c.evidence_id)
        assert ev.verified is False
        assert ev.grade is citations.Grade.PROJECT_ESTIMATE
        # Wide band: this is the least certain number in the recipe library.
        assert c.uncertainty >= 0.15


class TestHonestyReport:
    def test_unverified_report_lists_every_unverified_constant(self):
        report = citations.unverified_report()
        for c in citations.unverified():
            assert c.key in report

    def test_nothing_has_been_quietly_marked_verified(self):
        # Only a human who has opened the source document may flip this flag.
        # As of this build, nobody has opened IFCT 2017 or FAO FNP 77.
        assert not citations.evidence("ifct_2017").verified
        assert not citations.evidence("fao_fnp_77").verified


class TestRetentionModuleHoldsNoNumbers:
    def test_every_process_reads_its_factor_from_the_registry(self):
        for p in retention.PROCESSES.values():
            assert citations.constant(p.constant_key).value == p.factor

    def test_rice_triples(self):
        # 60 g raw x 3.0 = 180 g cooked, and back again.
        assert retention.cooked_mass(60.0, "boil_rice") == pytest.approx(180.0)
        assert retention.raw_mass_for_cooked(180.0, "boil_rice") == pytest.approx(60.0)

    def test_oil_uptake_and_yield_factors_are_not_interchangeable(self):
        with pytest.raises(ValueError, match="not a yield factor"):
            retention.cooked_mass(10.0, "griddle_dosa")
        with pytest.raises(ValueError, match="not a oil_uptake factor"):
            retention.retained_oil_mass(10.0, "boil_rice")

    def test_griddle_oil_uptake(self):
        # 5 g spooned onto the tawa x 0.70 retained = 3.5 g in the dosa.
        assert retention.retained_oil_mass(5.0, "griddle_dosa") == pytest.approx(3.5)

    def test_unknown_process_points_at_the_registry(self):
        with pytest.raises(KeyError, match="citations.py"):
            retention.process("deep_fry_dosa")

    def test_every_process_factor_is_currently_unverified(self):
        # Stated as a test so that flipping a flag without opening a document
        # breaks something visible rather than passing quietly.
        assert len(retention.unverified_processes()) == len(retention.PROCESSES)
