---
name: feedback_completed_projects
description: "Every plan lives in aidocks/plans/, planned or complete; a finished one is marked finished in its note and listed under Completed projects in the index, but never moves."
metadata:
  node_type: memory
  type: feedback
---

**A completed plan stays where it is.** `aidocks/plans/` holds every plan, planned or complete. `aidocks/general/` holds the rest: feedback, project and user notes, and `MEMORY.md`. When the dev says a project works, its status line says finished and its line in `MEMORY.md` moves to the "Completed projects" section. The file itself does not move.

**Why:** The dev's layout, adopted for this project on 2026-10-19 ("plans for things that needs to be completed. It can also hold things that are completed as well."). A plan that never moves keeps the same path from the day it is written, so whatever cites it never needs repointing.

**How to apply:**
- A new plan is `aidocks/plans/<name>_plan.md`, with no `project_` prefix and `name:` matching the file.
- A `[[name]]` link resolves to `aidocks/general/<name>.md` or `aidocks/plans/<name>.md`, whichever holds it. Inside `MEMORY.md`, a plan's link is `../plans/<name>.md`.
- Only a project the dev confirmed is listed as completed.
