---
name: feedback_grow_check_tools
description: "When a plan has a by-ear check tool in tests/interact/, start it in the first section that can be heard and grow it with every section, never leaving it all for the last section."
metadata:
  node_type: memory
  type: feedback
---

**A plan's by-ear check tool grows section by section** (the dev, 2026-10-20, of plan 4's `story_check.py`: "Yes. It should. Remember that for later plans if they have interactive check scripts."; and earlier, of plan 3's `audio_check.py`: "Deffenatly. I do not want to wait untill we do section 4 to use the entire tool.").

**Why:** a tool written only in a plan's last section leaves every mandatory ear test until the end, so a problem is heard late, when it is harder to fix. A tool that grows lets each section's mandatory tests be heard as that section is built, on the tool's own save.

**How to apply:**
- At a plan's review ([[feedback_review_plan_sections]]), if it has a `tests/interact/` tool, plan it to start in the first section with anything to hear.
- **Each section adds that section's part to the tool.** The plan's last tool section only rounds it off.
- Each section's ear tests ([[feedback_say_ear_tests_ahead]]) name the tool's keys for that section.
- Each tool keeps its own save under `%APPDATA%\Heathcote\interact\` ([[feedback_test_tools_in_interact]]).
- **Before handing a tool over, start it silently through its real entry point:** `python tests\interact\<tool>.py` with `HEATHCOTE_SILENT`, `HEATHCOTE_NOSOUND`, a dummy SDL video driver and a throwaway `HEATHCOTE_USER_DIR`, for a few seconds. Then read its log. Driving the tool's pieces by hand is not enough.
  - **Why:** on 2026-10-20 `story_check.py` quit as the dev opened it ("it quits as soon as I open it"). It made its story screen before the main loop started FMOD. Every silent check had started FMOD first, so none caught it.
- **A tool never closes silently on an error.** It writes `crash.txt` and says why, as the game does.
