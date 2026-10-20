---
name: feedback_docs_after_each_plan
description: "When a plan is finished, bring every doc up to date, developer and player alike: README.md, requirements.txt, tools/README.md, CLAUDE.md, every note and plan in aidocks/ with its index, and docks/readme.txt, changelog.txt and todo list.txt. Only then push."
metadata:
  node_type: memory
  type: feedback
---

**After each plan is finished, update every doc it touches, so none falls behind** (the dev, 2026-10-19: "Remember to update the dev/player docks where possible after the completion of each plan so no dock falls behind.").

**Why:** before plan 3 the player readme was still empty and README.md was two lines, although two plans were finished. The dev had to ask for a catch-up.

**How to apply:**
- When the dev confirms a plan finished, before offering the next plan's review ([[feedback_review_plan_sections]]), go through:
  - **Developer docs:**
    - `README.md`: status by plan, requirements, running, options, files, tests, by-ear tools, layout, credits, licences.
    - `requirements.txt`, when a package is added.
    - `tools/README.md`, when a tool changed.
    - `CLAUDE.md`'s layout and status.
    - **All of `aidocks/`** (the dev, 2026-10-19: "the dev docks also include your ai docks as well, including the aidocks folder."):
      - the finished plan's own note
      - every later plan its build changed
      - the project notes, such as [[project_dev_tasks]] and [[project_later_topics]]
      - the `MEMORY.md` index
  - **Player docs, in `docks/`:**
    - `readme.txt`: describes only what works in the game now, never what is planned.
    - `changelog.txt`: one line per noticeable change, if any were missed ([[feedback_changelog]]).
    - `todo list.txt`: move what the plan finished, and add what it left ([[feedback_todo_list_format]]).
- Say what changed in each doc, and commit them, one commit per kind of doc.
- **Then push.** A plan is complete only once its docs are updated, and that is when its commits go up ([[feedback_git_commits]]).
- Keep the changelog and todo list up to date as changes land, too. This catch-up is a safety net, not a replacement.
- Never name the other game in user/ ([[feedback_no_other_games]]), and never record a release ([[feedback_no_release_records]]).
