---
name: feedback_todo_list_format
description: "docks/todo list.txt: ##Unfinished. then ##Finished. headings, one plain sentence per line stating the bug itself (never \"Fix a bug where\"), new items at the top, each as short as the rest, no markdown or numbers. Players only."
metadata:
  node_type: memory
  type: feedback
---

`docks/todo list.txt`, with a space in the name, is the dev's task list. **It holds only what a player notices**, because it ships beside the game. Developer tasks (the repository, tools, tests, build and docs) go in [[project_dev_tasks]] instead.

**Its format:**
- `##Unfinished.` on the first line, a blank line, then one item per line.
- A blank line, then `##Finished.`, a blank line, and its items below.
- **An empty `##Unfinished.` still has a line**, so a player hears something between the headings: "Nothing is waiting here right now. New bugs, planned changes and anything still to be decided will be listed here as they come up." It goes as soon as a real item is added, and comes back when the last one is finished.
- **Every heading is followed by one blank line, and a new item goes after that blank line**, at the top of the items. Never put an item straight under the heading.
- Each item is a plain sentence or two. **A bug is stated as what happens**, with no "Fix a bug where" in front.
- **Every sentence ends with a period**, the last one in an item included (the dev: "Please make sure change logs and todo list entries contain periods at the end of each centince").
- An enhancement or task starts with what to do: "Add ...", "Make ...", "Remove ...".
- A finished item says what is now true, newest first. A reworded line goes back to the top.
- No numbering, no bullets, no markdown, no file:line references. Avoid contractions.
- Line endings do not matter. No BOM. Keep every line well under 1024 characters.

**Why:** The dev's standing rules, adopted for this project on 2026-10-19. They read it by screen reader, so plain sentences read cleanly and markdown symbols would be spoken aloud.

**How to apply:**
- A player-facing finding that is reported and not fixed in the same change goes into `##Unfinished.` as soon as it is reported.
- A bug found and fixed in the same change goes straight into `##Finished.`.
- Move an item to `##Finished.` only when the dev confirms it is done.
- Keep each item as short as the others. The technical detail lives in a plan or memory note.
