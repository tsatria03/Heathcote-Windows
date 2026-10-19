---
name: feedback_no_question_pickers
description: "Ask questions as plain text in the reply, never through the multiple-choice picker tool (AskUserQuestion)."
metadata:
  node_type: memory
  type: feedback
---

**Never ask the dev anything through the question picker** (the `AskUserQuestion` tool). Ask in the reply instead, in plain sentences.

**Why:** The dev's standing rule, adopted for this project on 2026-10-19. They read by screen reader, and a picker is a separate control to navigate rather than text they can read straight through ([[user_screen_reader]]).

**How to apply:**
- Put the question at the end of the reply.
- Say which answer is recommended and why, in one line, so a short reply is enough.
- Keep code or layout samples in a fenced block in the reply.
