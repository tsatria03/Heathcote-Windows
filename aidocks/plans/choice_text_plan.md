---
name: choice_text_plan
description: "Plan 9: in the actions menu, a choice's text is spoken by the screen reader once its recorded clip has finished, the first time only, and Space's choice_text action is removed."
metadata:
  node_type: memory
  type: project
---

**Status:** built 2026-10-21 on the dev's word ("yes"), waiting for the dev's ear tests.

## What was built

- **`heathcote/game/actions_menu.py`:** `announce(with_text=True)` plays the clip and sets `text_due`; `update()` speaks the text once `systemVoice` falls silent, without interrupting, and the 7-second repeat calls `announce(with_text=False)`. Every announce clears `text_due` first, so a choice left early says nothing.
- **`heathcote/platform/keymap.py`:** `choice_text` is gone, and a saved action the game no longer has makes the key map rewrite `keys.json` without it.
- **Tests:** the actions test now checks the text after the clip, once, never on the repeat, and never for a choice left early; a key map test checks the old binding is dropped. 220 in all, the whole suite passing.

Plan 9, after the first release. Asked for by the dev, 2026-10-21: "There's one more thing I want changed, and it's space to read the text version of the prerecorded actions. I was thinking that if you hover over a choice in the menu, the text appears for that choice, but after the recording plays. ... That way you can take space off the list." It changes [[story_engine_plan]]'s actions menu.

## What is there now

- `heathcote/game/actions_menu.py`: each move plays the choice's clip on `systemVoice`; a choice with no clip, "next room" or "just stop", is said by the screen reader instead; after 7 seconds with no move the choice is announced again.
- Space, the key map's `choice_text` action, speaks the choice's text (`StoryPlayer.choice_text()`: its recording's transcript, or its label).
- The clips are short: 65 of them, 0.5 to 1.5 seconds, 0.9 on average, measured 2026-10-21.

## Decided

- **The text follows the clip:** landing on a choice plays its clip, as now, and once the clip has finished, the screen reader speaks the choice's text, without cutting anything off. The menu sees the clip end by the `systemVoice` slot falling silent, checked each frame.
- **Moving on before the clip ends** cancels the text, so it is never spoken for a choice already left.
- **Only the first time** (the dev, 2026-10-21: "I do not want it to respeak the text every 7 seconds after the audio recording."): the 7-second repeat replays the clip alone. Landing on the choice again, or any key the menu has no use for, which says the choice again, counts as a first time, clip then text.
- **A choice with no clip** is said by the screen reader at once, as now, and the 7-second repeat says it again, as now, since its text is its only announcement.
- **Space's `choice_text` action is removed** from the key map, so it leaves the F1 screen, and Space becomes a key the menu has no use for, which says the choice again. A saved binding for it in `config\keys.json` is dropped.
- **Docs:** the player readme, the changelog and the README say so.

## Built in sections

One section.

## Ear tests

1. Mandatory: landing on a choice plays its clip, then the screen reader speaks its text, without cutting the clip off.
2. Mandatory: waiting on a choice replays the clip after 7 seconds with no text.
3. Mandatory: arrowing quickly through the choices never speaks the text of a choice already left.
4. Optional: Space no longer appears in the F1 screen, and pressing it in the actions menu says the choice again.

## Open questions

None.
