---
name: feedback_changelog
description: "Whenever a change players will notice lands, add a plain sentence at the top of the unrelease: block in docks/changelog.txt, in the same commit; entries read newest first. One sentence per line, no markdown, no BOM; LF or CRLF are both fine."
metadata:
  node_type: memory
  type: feedback
---

**Keep `docks/changelog.txt` up to date as game changes land.** Every commit that fixes a bug or adds an enhancement a player will notice also adds a line under `unrelease:` at the top of the file.

**Why:** The dev's standing rules, adopted for this project on 2026-10-19. The changelog ships beside the game, so players read it by screen reader.

**How to apply:**
- **Format:**
  - A heading is one word ending in a colon, on a line of its own: `unrelease:`, or a version like `26.10.19-1:`.
  - Every other line is an entry: one plain sentence or two, with no bullets, numbers or markdown.
  - A blank line separates one heading's block from the next.
- **Line endings do not matter** (the dev: "I don't mind if everything is CRLF"). Write it without a BOM.
- **New lines go at the top of the `unrelease:` block**, so the block reads newest first. A reworded line goes back to the top too. If there is no `unrelease:` heading, add it at the very top.
- **Only what a player notices:** fixes, enhancements, removed features. Leave out notes, docs, tests, refactors and build internals, and anything only developers see.
- **Wording:** write for a player, say what is now true, and avoid contractions.
- **Every sentence ends with a period** (the dev: "Please make sure change logs and todo list entries contain periods at the end of each centince"), the last one in an entry included. A period inside a closing quote counts. Check the whole `unrelease:` block for it before a release.
- **No credit lines.** Entries say what changed, not who changed it.
- **Released entries stay as they are.** Never edit an entry that already has a version heading.
- **Release size:**
  - A release aims for 50 to 100 entries and never holds more than 100.
  - Fewer than 5 does not make a release unless the dev overrides it.
  - A heading is never counted as an entry. Count the lines from the file each time, and say so when the block nears 100.
- **Never give an entry count without counting it from the file first** (the dev: "Please record that rule in your memmory"). Read the block, or count its lines with a command, just before saying the number. Leave out the heading and blank lines. Never count from memory or from line numbers. The releaser's count is the one that matters, so the two must agree.
