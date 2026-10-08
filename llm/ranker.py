"""Choose one plate among valid ones, by how well its dishes go together.

**Not called by the app.** N13 stopped at its premise check (audit
2026-10-07 "N13"): on the one property that can be counted, the same main
ingredient in several dishes, this model chose no better than the planner's
nearest plate. Kept because probe_ranker_live.py measures exactly this code.

Architecture step 5. TASKS_3.md N13, owner 2026-10-07 (option 1). The
solver has already made every plate offered here valid and set every count;
this only judges which set of dishes a family would serve together, the one
thing the solver cannot know (audit 2026-10-07 "N12": nearest-to-target put
soya in three courses of one plate).

What the model sees: the region, the meal, and per plate a letter and its
dish names. No gram, count or nutrient value -- the spec (architecture.md
step 5) mentions macro summaries, left out on purpose: every plate already
meets the limits, so a number could only pull the choice toward "more
protein", which is the solver's job, not taste. A test checks the prompt
holds no digit at all. Plates are labelled with letters for the same reason.

What it returns: an index into the plates, or ``None``. ``None`` whenever
the model is off, slow, or answers anything but one of the letters; the
caller then keeps the nearest plate. The answer is also constrained by a
JSON schema whose only allowed values are the letters, and checked again
here, since a constraint the server applies is not one this code has seen.
"""

from __future__ import annotations

import json
import os
import string
import urllib.error
import urllib.request
from typing import Sequence

__all__ = ["make_ranker", "build_prompt", "parse_choice", "LETTERS"]

#: Plate labels. Letters, so the prompt has no digits (see module docstring).
LETTERS = string.ascii_uppercase

DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:7b-instruct"
#: Seconds to wait for an answer before keeping the nearest plate. Measured
#: in audit 2026-10-07 "N13" (warm answers well under this; a cold model load
#: can exceed it, and then that one request falls back).
TIMEOUT_S = 15.0

REGION_WORDS = {"south_indian": "South Indian", "north_indian": "North Indian"}

SYSTEM = (
    "You help plan Indian home meals. Every plate offered already meets the "
    "person's nutrition needs, and the amounts are fixed: do not judge or "
    "change amounts. Choose the one plate a family from the region would most "
    "naturally serve together as this meal: dishes that are usually eaten "
    "together, and not the same main ingredient in several dishes. Answer "
    "with the plate's letter only."
)


def build_prompt(region: str, meal: str, plates: Sequence[Sequence[str]]) -> str:
    lines = [f"Meal: {REGION_WORDS.get(region, region)} {meal}.", "Plates:"]
    for letter, dishes in zip(LETTERS, plates):
        lines.append(f"{letter}: {', '.join(dishes)}")
    return "\n".join(lines)


def parse_choice(content: str, n: int) -> int | None:
    """The plate index a reply names, or None for anything else."""

    try:
        letter = json.loads(content)["plate"]
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(letter, str) or len(letter) != 1:
        return None
    i = LETTERS.find(letter)
    return i if 0 <= i < n else None


def _ask(url: str, model: str, region: str, meal: str, plates: tuple[tuple[str, ...], ...]) -> int | None:
    letters = list(LETTERS[: len(plates)])
    body = {
        "model": model,
        "stream": False,
        "keep_alive": "30m",
        # Same plates, same answer: greedy decoding and a fixed seed.
        "options": {"temperature": 0, "seed": 0},
        "format": {
            "type": "object",
            "properties": {"plate": {"type": "string", "enum": letters}},
            "required": ["plate"],
        },
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_prompt(region, meal, plates)},
        ],
    }
    req = urllib.request.Request(
        f"{url}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as res:
            reply = json.load(res)
        return parse_choice(reply["message"]["content"], len(plates))
    except (OSError, ValueError, KeyError, TypeError):
        # OSError covers refused connections, timeouts and HTTP errors.
        return None


#: Answers already given, so a page going back and forth between the same
#: plates gets the same plate without waiting. Only answers are kept, never
#: a failure: the model may be up on the next request.
_answers: dict[tuple, int] = {}


def make_ranker(region: str, meal: str):
    """A ``rank`` callable for ``plan_meal``, or None when ranking is off.

    ``FOODAI_RANKER=off`` turns it off (the test suite does, so no test
    depends on a model being installed). ``FOODAI_OLLAMA_URL`` and
    ``FOODAI_RANKER_MODEL`` point it elsewhere.
    """

    if os.environ.get("FOODAI_RANKER", "on") == "off":
        return None
    url = os.environ.get("FOODAI_OLLAMA_URL", DEFAULT_URL)
    model = os.environ.get("FOODAI_RANKER_MODEL", DEFAULT_MODEL)

    def rank(plates: tuple[tuple[str, ...], ...]) -> int | None:
        key = (url, model, region, meal, plates)
        if key not in _answers:
            choice = _ask(url, model, region, meal, plates)
            if choice is None:
                return None
            _answers[key] = choice
        return _answers[key]

    return rank
