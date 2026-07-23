"""Nutrition layer: the citation registry, the target shape, and target
derivation.

- ``citations``  — every nutritional constant, with evidence and mechanism review.
- ``target``     — the canonical ``NutritionTarget`` shape the planner consumes.
- ``targets``    — derive a real, cited, dev-mode target from a ``Profile``.

Depends only on ``core.schemas`` (and itself); never on ``core.planner`` or
``core.foods`` (CLAUDE.md, "Architecture").
"""
