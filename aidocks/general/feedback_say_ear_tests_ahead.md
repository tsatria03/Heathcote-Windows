---
name: feedback_say_ear_tests_ahead
description: "Before starting each section of a plan, tell the dev whether they will need to test anything by ear once it is built, and what, so they never have to ask after it is finished."
metadata:
  node_type: memory
  type: feedback
---

**Before each section starts, say whether the dev will need to test anything by ear, and what** (the dev, 2026-10-19: "From now on, let me know if I'll need to test anything by ear ahead of time before commiting to each section so I don't have to ask every time you finish the section.").

**Why:** after the title volume change the dev had to ask "Did I need to test anything?". Knowing beforehand lets them plan their checking, and confirm a section without a round of questions.

**How to apply:**
- When a section is proposed, or the dev asks to start one, give a short "To test by ear" list before building it:
  - what to run, such as `python Heathcote.py` or a tool in `tests/interact/`
  - what to listen for
- Or say plainly "Nothing to test by ear", and why: for example, the section is silent tests, or its parts cannot be heard until a later plan.
- Name what cannot be heard yet, so the dev doesn't look for it.
- When the section is finished, repeat the same list as the steps to try, and say if anything changed from what was promised.
- This goes with [[feedback_dont_run_or_build]]: the dev runs anything that makes sound, never Claude.
