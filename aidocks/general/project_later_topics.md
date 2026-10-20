---
name: project_later_topics
description: "Ideas and requirements for plans not yet written, kept here until that plan is written; each moves into its plan's Decided or Open questions and is struck from here."
metadata:
  node_type: memory
  type: project
---

Ideas the dev has raised that belong to a plan not yet written. When that plan is written, each idea goes into it, and its line here is removed.

**Why:** the dev raises ideas while other plans are being written ("We can talk about that later."). Kept here, they are not lost when the context is compacted.

**How to apply:** Before writing a plan, read this note and bring in every item that belongs to it.

## For the story engine plan

- Moved into [[story_engine_plan]], since the actions menu belongs to play: **a screen reader version of each recorded choice.** The actions menu speaks its choices with the recorded clips in `game/data/Audio/story/speech/`. The dev wants a key that, while a choice is selected, speaks that choice's text through the screen reader (the dev, 2026-10-19: "Since the stuff found in the speech folder are prerecorded menu choices, you should be able to press a key to here the screen reader version of those choices if you hover over one. We can talk about that later."). Each clip's text is its record's `transcript`. This line goes once the plan settles the key.

## For the menus plan

- **FMOD's credit line in the credits.** FMOD's licence requires an in-game credit containing "FMOD" and "Firelight Technologies Pty Ltd." ([[project_fmod]]; examples at www.fmod.com/attribution). The player readme's credits and licences sections name it too, and `vendor/fmod/license.txt` ships beside the game.
