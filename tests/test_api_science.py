"""``GET /api/science`` — the canonical citation-registry endpoint.

Per DESIGN_SYSTEM.md's content-redundancy rule, no frontend page may hardcode
a citation summary or phenomenon string of its own; a "why these numbers?"
expander fetches this endpoint at request time instead. These tests assert
the endpoint is a faithful, live passthrough of ``core.nutrition.citations``'
own registries -- not a fixed string baked into ``api/``.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from core.nutrition import citations

client = TestClient(app)


def test_science_is_reachable_and_shaped():
    r = client.get("/api/science")
    assert r.status_code == 200
    data = r.json()
    assert "scope_statement" in data
    assert "substitute" in data["scope_statement"]
    assert isinstance(data["evidence"], list)
    assert isinstance(data["rejected_citations"], list)


def test_science_reflects_the_live_registry_not_a_fixed_copy():
    # Mirrors the perturbation-test pattern used elsewhere in this repo
    # (test_ifct_loader.py): register a throwaway Evidence, assert it shows up,
    # proving the endpoint reads the registry live rather than a snapshot
    # written into api/.
    marker_id = "test_marker_evidence_science_endpoint"
    citations.register_evidence(
        citations.Evidence(
            id=marker_id,
            summary="marker for test_science_reflects_the_live_registry",
            phenomenon="not a real phenomenon, test-only",
            source="test suite",
            grade=citations.Grade.PROJECT_ESTIMATE,
        )
    )
    try:
        data = client.get("/api/science").json()
        ids = {e["id"] for e in data["evidence"]}
        assert marker_id in ids
    finally:
        del citations._EVIDENCE[marker_id]


def test_science_reports_every_registered_evidence_entry():
    data = client.get("/api/science").json()
    assert data["total_count"] == len(citations.all_evidence())
    assert {e["id"] for e in data["evidence"]} == {
        ev.id for ev in citations.all_evidence()
    }


def test_unverified_count_matches_the_registry():
    data = client.get("/api/science").json()
    expected = sum(1 for ev in citations.all_evidence() if not ev.verified)
    assert data["unverified_count"] == expected


def test_rejected_citations_include_the_dosa_oil_uptake_case():
    # The specific worked example CLAUDE.md and docs/methodology.md both cite:
    # a real, findable, correctly-formatted DOI-less citation for the wrong
    # physical process (deep-fry crust cooling, not griddle surface pickup).
    data = client.get("/api/science").json()
    dosa_rejections = [
        rc for rc in data["rejected_citations"] if rc["for_constant"] == "oil_uptake.dosa_griddled"
    ]
    assert dosa_rejections
    assert "griddled" in dosa_rejections[0]["why_rejected"].lower() or "tawa" in dosa_rejections[0]["why_rejected"].lower()


def test_evidence_rows_carry_phenomenon_distinct_from_summary():
    # Structural check that the field CLAUDE.md calls load-bearing actually
    # made it across the HTTP boundary, not just summary.
    data = client.get("/api/science").json()
    for e in data["evidence"]:
        assert e["phenomenon"].strip()
        assert e["summary"].strip()
