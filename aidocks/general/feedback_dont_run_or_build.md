---
name: feedback_dont_run_or_build
description: "Never build unless the dev says so. Ask before running the game or anything that executes game code, plays sound or speaks. Tests, once they exist, must be silent and keep off the real save. Read-only inspection is fine."
metadata:
  node_type: memory
  type: feedback
---

**Never build anything unless the dev says to.** That covers PyInstaller and any packaging or zip step.

**Ask first before running:**
- the game, including any headless run
- scratch scripts that import and execute game code
- anything that could speak through NVDA or Prism for real, or play sound

**Tests, once they exist:**
- They speak nothing, play no sound, open no window, and keep off the dev's real save, wherever they are run from.
- Run only the test scripts that cover the files changed, in the background.
- Run the full suite only when the dev asks, in the foreground.
- During a batch of fixes, run no tests between the commits.

**Read-only inspection is always fine:** reading and grepping files, `git status`, `git diff` and `git log`, and reading the original's data and binary.

**Why:** The dev's standing rules, adopted for this project on 2026-10-19. They run and verify builds themselves, and they work with NVDA running, so an unexpected run can make noise, touch their save, or leave stray processes.

**How to apply:** Make the edits, report them, and hand verification by ear back to the dev. When a change needs checking by ear, end with a clear "relaunch to test" note instead of running the game.
