---
name: feedback_record_plans_first
description: "Write an agreed plan into its own aidocks/plans/ note before building it, commit the plan first on its own, and mark it finished only once the dev says it works."
metadata:
  node_type: memory
  type: feedback
---

**Record a plan in aidocks before starting on it.** Once the dev and Claude have agreed a plan, it goes into its own note, `aidocks/plans/<name>_plan.md`, with a pointer in `MEMORY.md`, before any code is written. The note keeps every decision, the dev's own words where they settle something, and what is left out and why.

**Mark it finished only when the dev says it works.**
- Its status stays "planned" while waiting for the go-ahead.
- It becomes "built, not yet confirmed" once the code lands.
- It becomes "finished" only when the dev confirms it works, in that same note and its `MEMORY.md` line. Code landing or tests passing is not enough.

**Why:** The dev's standing rules, adopted for this project on 2026-10-19. A plan agreed in conversation is lost when the context is compacted, and a big change built from memory drifts from what was agreed.

**How to apply:**
- A plan big enough to need questions answered gets a note before its first edit. A one-line fix does not need one.
- If the plan changes while it is being built, update the note first, then the code.
- Update the note as each part lands, and say which parts are built and which are waiting.
- **Commit the plan first, on its own, and never push it until the whole thing is built and tested.** The code follows as a separate commit; then both are pushed together. The dev can choose otherwise.
- A finished plan stays in `aidocks/plans/` as a record ([[feedback_completed_projects]]).
