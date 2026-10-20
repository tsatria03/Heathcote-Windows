---
name: feedback_say_ear_tests_ahead
description: "Before starting each section, tell the dev what they will test by ear (sound or speech), marking each test optional or mandatory; remind them of any mandatory test they have not reported on before moving on."
metadata:
  node_type: memory
  type: feedback
---

**Before each section starts, say whether the dev will need to test anything by ear, and what** (the dev, 2026-10-19: "From now on, let me know if I'll need to test anything by ear ahead of time before commiting to each section so I don't have to ask every time you finish the section.").

**Mark every test optional or mandatory** (the dev, 2026-10-19: "Please let me know if some of the hering tests are optional. This also include the speech tests, not just sound. If a test becomes mandatory, let me know so I don't forget to open the script before telling you to move on. You can let me know if I did not report back on a test I forgot to open.").

**Why:** after the title volume change the dev had to ask "Did I need to test anything?". Knowing beforehand, and knowing which tests matter, lets them plan their checking and confirm a section without a round of questions.

**How to apply:**
- When a section is proposed, or the dev asks to start one, give a short "To test by ear" list before building it:
  - what to run, such as `python Heathcote.py` or a tool in `tests/interact/`
  - what to listen for
- **By ear means both sound and speech.** A screen reader line to check counts as much as an FMOD sound.
- **Label each test.**
  - **Mandatory:** only a person can judge it, such as how something sounds, whether speech interrupts properly, or timing by feel. The silent tests cannot cover it.
  - **Optional:** a reassurance check that the silent tests already cover.
  - When a test becomes mandatory, say so plainly and name the script to open.
- Or say plainly "Nothing to test by ear", and why: for example, the section is silent tests, or its parts cannot be heard until a later plan.
- Name what cannot be heard yet, so the dev doesn't look for it.
- When the section is finished, repeat the same list, still labelled, as the steps to try, and say if anything changed from what was promised.
- **Hold the dev to the mandatory ones.** If the dev confirms a section or asks to move on without reporting on a mandatory test, remind them which one before going on. Don't remind them about optional ones.
- This goes with [[feedback_dont_run_or_build]]: the dev runs anything that makes sound or speaks, never Claude.
