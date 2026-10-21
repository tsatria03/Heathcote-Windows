---
name: feedback_next_section_on_pass
description: "Within a plan being built, when the dev says a section's tests passed, record and commit that, then build the next section at once, without asking."
metadata:
  node_type: memory
  type: feedback
---

**When the dev says a section's tests have passed, mark it, commit it, and move straight on to building the next section** (the dev, 2026-10-20, during plan 5: "From now on, when I say a test has past, move on to the next section after marking/commiting it.").

**Why:** asking "shall I build the next section?" after every pass was an extra round trip. Saying the tests passed is the go-ahead.

**How to apply:**
- On a pass: record it in the plan, mark the section finished, commit, then build the next section in the same turn.
- Before building it, still list its ear tests, each optional or mandatory, and remind the dev of any mandatory test not yet reported ([[feedback_say_ear_tests_ahead]]).
- This is within a plan only. When the last section passes, the plan is finished: docs, progress summary and push follow ([[feedback_docs_after_each_plan]]), and the next plan still waits for its review and the dev's word ([[feedback_review_plan_sections]]).
