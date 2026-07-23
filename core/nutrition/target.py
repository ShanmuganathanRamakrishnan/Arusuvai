"""The canonical target shape: a floor and/or ceiling per macro, plus an ideal.

This lives in ``core/nutrition`` — not ``core/planner`` — because the target is
a nutrition concept the planner *consumes*, and the dependency direction is
strictly downward (CLAUDE.md, "Architecture": ``core/nutrition`` must never
import from ``core/planner``). It was moved here from ``core/planner`` when
``core/nutrition/targets.py`` landed: that module derives a real target from a
``Profile`` (BMR -> activity factor -> goal energy -> DIAAS-adjusted protein ->
macros) and, per this file's original promise, produces *exactly this shape*
via :func:`simple_target` rather than a parallel one. The planner still imports
``NutritionTarget``/``band`` from here (downward), so nothing about how the
solver and validator consume a target changed.

Tolerance (this module) and uncertainty (``core.foods.nutrition_of``) are the
two axes CLAUDE.md's "Uncertainty" section says must never be merged. Nothing
here reads a composition or process uncertainty figure, and nothing in the
eligibility filter reads a floor or ceiling. Keeping them in separate modules
makes that separation structural rather than a habit to remember.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from core.nutrition import citations

__all__ = ["NutritionTarget", "band", "simple_target"]


@dataclass(frozen=True)
class NutritionTarget:
    """Per-macro floor/ceiling (admissibility) plus an optional ideal point.

    Floor and ceiling are the *tolerance* axis (CLAUDE.md, "Uncertainty" —
    kept structurally separate from the uncertainty axis, which lives in
    ``core.foods.nutrition_of`` and never appears here): they define whether
    a plan counts as valid at all, and that is all ``core/planner/solver.py``
    uses them for (``_within_target``).

    ``points`` is a distinct, independent notion: the value the solver's
    weighted-deviation objective ranks *among already-valid* assignments by
    closeness to. It is not derived from floor/ceiling (a macro may have one
    without the other), because collapsing them would make every in-band
    assignment score identically — floor/ceiling alone cannot rank two
    assignments that are both valid, only decide validity.
    """

    floors: Mapping[str, float] = field(default_factory=dict)
    ceilings: Mapping[str, float] = field(default_factory=dict)
    points: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "floors", MappingProxyType(dict(self.floors)))
        object.__setattr__(self, "ceilings", MappingProxyType(dict(self.ceilings)))
        object.__setattr__(self, "points", MappingProxyType(dict(self.points)))
        for macro, lo in self.floors.items():
            hi = self.ceilings.get(macro)
            if hi is not None and lo > hi:
                raise ValueError(
                    f"target: floor for {macro!r} ({lo}) exceeds its own ceiling ({hi})"
                )

    def floor(self, macro: str) -> float | None:
        return self.floors.get(macro)

    def ceiling(self, macro: str) -> float | None:
        return self.ceilings.get(macro)

    def point(self, macro: str) -> float | None:
        return self.points.get(macro)

    def bounded_macros(self) -> frozenset[str]:
        """Every macro this target constrains, floor or ceiling or both."""

        return frozenset(self.floors) | frozenset(self.ceilings)


def band(point: float, tolerance: float) -> tuple[float, float]:
    """A symmetric (floor, ceiling) pair around ``point``.

    Relaxation (Phase 3) is exactly a second call to this with a wider
    ``tolerance`` — the ladder widens tolerance, never touches uncertainty,
    and this function is the one place tolerance turns into a floor/ceiling
    pair, so that widening has a single call site to change.
    """

    if tolerance < 0:
        raise ValueError(f"tolerance must be >= 0, got {tolerance}")
    return point * (1 - tolerance), point * (1 + tolerance)


def simple_target(
    *,
    energy_kcal: float,
    protein_g_min: float,
    fat_g: float | None = None,
    carb_g: float | None = None,
    sodium_mg_max: float | None = None,
    fibre_g_min: float | None = None,
    energy_tolerance: float | None = None,
    fat_carb_tolerance: float | None = None,
) -> NutritionTarget:
    """Build a target from a point-estimate profile plus CLAUDE.md's default
    tolerances: energy +/-5%, fat/carb +/-15%, protein a hard floor (no
    symmetric band — the relaxation ladder only ever loosens it downward, and
    a ceiling on protein is not one of CLAUDE.md's default constraints).

    The two tolerances default to the registered constants rather than to
    literals, so this constructor and ``validator.RELAXATION_ORDER`` (which
    widens the same two figures) read the same source. They stayed as literals
    through Phase 2 and were the only pair of numbers in ``core/planner`` that
    could have drifted apart silently.
    """

    if energy_tolerance is None:
        energy_tolerance = citations.value_of("tolerance.energy_default")
    if fat_carb_tolerance is None:
        fat_carb_tolerance = citations.value_of("tolerance.fat_carb_default")

    floors: dict[str, float] = {"protein_g": protein_g_min}
    ceilings: dict[str, float] = {}
    # The ideal point a macro relaxes toward is not always its floor (protein)
    # or its band centre (energy/fat/carb): populated per macro below, right
    # where each is computed, rather than derived generically afterward.
    points: dict[str, float] = {"protein_g": protein_g_min}

    floors["energy_kcal"], ceilings["energy_kcal"] = band(energy_kcal, energy_tolerance)
    points["energy_kcal"] = energy_kcal
    if fat_g is not None:
        floors["fat_g"], ceilings["fat_g"] = band(fat_g, fat_carb_tolerance)
        points["fat_g"] = fat_g
    if carb_g is not None:
        floors["carb_g"], ceilings["carb_g"] = band(carb_g, fat_carb_tolerance)
        points["carb_g"] = carb_g
    if sodium_mg_max is not None:
        ceilings["sodium_mg"] = sodium_mg_max
    if fibre_g_min is not None:
        floors["fibre_g"] = fibre_g_min

    return NutritionTarget(floors=floors, ceilings=ceilings, points=points)
