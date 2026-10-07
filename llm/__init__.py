"""Calls to a local language model (Ollama). Architecture steps 5 and 6.

The only package that talks to a model. It never receives or returns a
quantity (CLAUDE.md invariant 1): ``core`` hands it dish names and gets back
a choice among plates that are already valid, or nothing. Every failure --
model off, slow, or answering outside the list -- is ``None``, and the
planner's own choice stands.

Nothing in the app imports this yet: see llm/ranker.py.
"""
