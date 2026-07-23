"""HTTP layer. Thin — it translates JSON to ``core`` calls and back, and holds
no nutrition logic of its own (CLAUDE.md, "Architecture"). It depends on
``core``; ``core`` never imports from here, and no quantity a user relies on is
computed in this layer — the numbers come out of ``core.nutrition.targets``.
"""
