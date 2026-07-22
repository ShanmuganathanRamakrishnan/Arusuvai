"""Deterministic planning: candidates -> combinations -> solver.

Everything under here is a pure function over already-loaded ``core.foods``
data. No LLM call, no I/O, no web framework — see CLAUDE.md's "What the LLM
actually does" and the architecture diagram. ``core/nutrition`` must never
import from this package; this package may import from ``core.foods``,
``core.nutrition`` and ``core.schemas`` only.
"""

from __future__ import annotations
