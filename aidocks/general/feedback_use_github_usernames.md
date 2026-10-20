---
name: feedback_use_github_usernames
description: "Name people by GitHub username (tsatria03), never real names, in commit authors, commit messages and everything committed to the repo."
metadata:
  node_type: memory
  type: feedback
---

Identify people by their GitHub username, never their real name. The dev is **tsatria03**. This applies to commit authors and committers, commit messages, and everything committed to the repo.

**Why:** The dev's standing rule, adopted for this project on 2026-10-19. The repo's git identity is `tsatria03`, with the noreply address `156674543+tsatria03@users.noreply.github.com`. The repo itself is private on GitHub and will stay so (the dev, 2026-10-19: "I'm not planning to make this repository public. RIght now it's private, and will remain there."), but the rule holds all the same, and the game players download carries the same credits.

**How to apply:**
- Check `git config user.name` before committing. If it has drifted, pass `--author="tsatria03 <156674543+tsatria03@users.noreply.github.com>"`.
- Emails stay the GitHub noreply address.
- `LICENSE` reads "Copyright (c) 2026 tsatria03".
- The people credited in the original game's own data or credits, such as Fabulae Obscurae and its cast, are part of the original and are cited from it.
