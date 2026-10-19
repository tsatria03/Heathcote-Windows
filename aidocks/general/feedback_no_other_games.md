---
name: feedback_no_other_games
description: "Never name or refer to the dev's other games, kept in the gitignored user/ folder, anywhere in this repo's own files. Adapting their code, docs or layout is fine; naming where it came from is not."
metadata:
  node_type: memory
  type: feedback
---

The gitignored `user/` folder holds the dev's other game, kept as a reference to adapt from. Never mention it in this repo's own files:
- the player documents in `docks/` (readme, changelog, todo list)
- any `aidocks/` note, `CLAUDE.md` or `README.md`
- the Python code, its comments and docstrings, and commit messages

That rules out its name, its folder names and its paths, and phrases like "the same as in their other game".

**Why:** The dev's standing rule, adopted for this project on 2026-10-19: "Do not mention the game if you dicide to adapt stuff from it, such as docks."

**How to apply:**
- Reading `user/` for reference is fine. Never edit anything in it.
- When adapting something from it, write about Heathcote alone, as if the idea started here.
- When a source must be cited, say "the reference material in the gitignored `user/` folder".
- Before saving a note, a doc line, a comment or a commit message, check it for the other game's name.
