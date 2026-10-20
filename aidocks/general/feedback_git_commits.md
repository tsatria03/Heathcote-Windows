---
name: feedback_git_commits
description: "One commit per fix. Commit without asking; raise pushing only at 10 or more unpushed commits. 'Commit' means commit only; 'commit/push' means both. History rewrites need an explicit go-ahead. Use git commit -F with a message file written by the Write tool, run git from PowerShell, and never hide git's errors."
metadata:
  node_type: memory
  type: feedback
---

**"Commit" means commit only; "commit/push" means commit and push.** Commits pile up locally by default, because the dev tests batches before pushing.

**Commit without asking; ask before pushing** (the dev: "For commits, you don't have to ask me if I want it done. You can always commit, but still ask if I want it pushed"). When a change is done, commit it straight away.

**Bring up pushing only from 10 unpushed commits.** Below 10, commit quietly, with no count and no question about pushing. At 10 or more, say how many are waiting and ask whether to push.

**Hold while the dev says so.** When the dev holds pushes, do not ask about pushing even past 10 commits. When the hold ends, report the count and ask. The dev can still ask for a push during a hold.

**A hold is on now** (the dev, 2026-10-19: "Do not push untill all plans are written and recorded with answered questions."). It began with 12 unpushed commits. Until every plan is written in `aidocks/plans/` with its questions answered, never push and never ask about pushing. Once they are all written, report the count and ask.

**Make multiple commits when possible** (the dev, 2026-10-19: "in the future, try to make multiple commits when possible"). Split a batch into one commit per logical change. The dev's reorganization of `game/` went in as five commits, one per kind of file (audio, text, images, certificates, source files), each staging the old and new paths together so git records them as renames.

**Fetching is fine without asking; bringing commits in is not.** Never pull, merge, rebase, cherry-pick or reset onto incoming commits without the dev's go-ahead.

**Rewriting published history needs an explicit go-ahead every time.** That covers force pushes, amending or rebasing pushed commits, and changing authors. When approved, push with `--force-with-lease`, and keep a backup until the dev is happy.

**The first rewrite** was on 2026-10-19, before any push: `fmod.dll` was taken out of every commit on `main` with `git filter-branch`, after the dev asked for a backup branch first ([[project_fmod]]). **Push only `main`, never `backup/before-fmod-rewrite`,** and never `git push --all` or `--mirror`: that backup branch still holds the DLL, which FMOD's licence does not allow in a public repo. Delete it only when the dev says so.

**Why:** The dev's standing rules, adopted for this project on 2026-10-19. The dev approves what goes into a commit, and history rewrites can lose work.

**How to apply:**
- Write the message to a file in the scratchpad with the Write tool, then run `git commit -F <file>` from PowerShell. Windows PowerShell 5.1 breaks double quotes inside `-m` arguments.
- Keep git commands plain: chain them with `;`, but pipe nothing after them. Never send git's error output to `$null`; a failed commit must be visible.
- **One commit per fix or change.** Each commit carries its own todo, changelog, docs and memory lines.
- **Mark the work finished before committing it**, so the finished line goes in the same commit as the work.
- Stage files by name when the commit should hold exactly what the dev approved. Check `git status` first.
- Never commit work the dev made by hand (such as a reorganization of `game/`) without asking first.
- Format: a short summary line, a blank line, then a plain-text description wrapped at about 72 characters, ending with the Claude attribution line.
- The author is always tsatria03, with no `Co-authored-by:` lines for people ([[project_solo]], [[feedback_use_github_usernames]]).
- Never add large binaries casually; they stay in git history forever.
- After pushing, confirm with `git ls-remote origin refs/heads/main` and report the new commit.
- Committing isn't building or running; [[feedback_dont_run_or_build]] still applies.
