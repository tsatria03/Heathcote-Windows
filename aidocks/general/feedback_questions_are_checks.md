---
name: feedback_questions_are_checks
description: "A question about the original or the port is a check: answer it in chat, don't edit code, comments or docs off the back of it."
metadata:
  node_type: memory
  type: feedback
---

When the dev asks a question about the original or the port, or states a fact in reply, answer it in chat and change nothing. Findings from the check, even a correction to the docs, are reported and offered, not written.

**Why:** The dev's standing rule, adopted for this project on 2026-10-19. On 2026-10-19 the dev asked whether their reorganization of `game/` was correct; that was answered in chat by checking the files against the bundle index, with no edits to `game/`.

**How to apply:** Only edit files when the dev asks for a change. If a check turns up something wrong, mention it in one line and let the dev decide.
