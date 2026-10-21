---
name: menu_sounds_plan
description: "Plan 11: the original's click-good plays as you move, choose and go back in every menu, with a Menu sounds setting to turn it off."
metadata:
  node_type: memory
  type: project
---

**Status:** being built, 2026-10-21, on the dev's word, with one change ("Yes. Also, rename the setting to click sounds because when you press left/right arrow in the story, it plays for seaking, witch by the way should be effected if the sounds are disabled. As in the click sounds will not play there."):
- **The setting is "Click sounds"**, saved as `click_sounds`, and it governs every `click-good` and `click-bad` in the game, not only the menus': rewind and fast-forward, opening the actions menu or hearing it refused, pausing refused in the grace, and Enter or a wrong key at the opening and the first-run notice. Off, none of them plays; the story's other sounds, such as `menu-open`, `menu-unavailable` and the pause sounds, stay.
- It is checked in one place, `App.play_sound()`, which every click goes through.

Plan 11. Chosen by the dev from a list of small ideas, 2026-10-21: "I want the menu click sounds in the other menus as well, also a setting to disable it if the user does not want it." It changes plan 2's spoken menu (`heathcote/ui/menu.py`, [[foundation_plan]]) and [[settings_plan]]'s Settings screen.

## What the original did

Every gesture the original accepted played `click-good` (`click.mp3`), and one it refused played `click-bad` ([[project_original_behaviour]]): moving through its menus, choosing, going back, opening the actions menu, rewinding. The port plays them already for the story's keys, the opening and the first-run notice, but its menus are silent but for speech.

## Decided

- **`click-good` plays in every menu** as you move (all four arrows, Home and End), choose with Enter, and go back with Escape or Back:
  - the main menu, Settings and its lists of levels, Credits and the end credits, the pause menu and the Restart question
  - the F1 key bindings screen, as you move and choose, but not while it waits for the key to bind, so the key you press is never clicked
  - the actions menu, as you move between choices, under each choice's clip, as in the original. Opening, accepting and closing it keep their own sounds, `menu-open`, `menu-accepted` and `menu-close`.
- **A key a menu has no use for,** which says the row again, plays nothing, since saying the row again is not an error.
- **Click sounds,** a Settings row after Skip opening screens: "Click sounds, currently on". Enter turns it on or off at once, and says the row again. On by default. Saved as `click_sounds` in `config\settings.json`. Off, no click plays anywhere, as above.
- **The clicks follow the interface volume,** as every interface sound does.
- **Ear tests:**
  1. Mandatory: moving, choosing and going back click in the main menu, Settings, Credits and the pause menu.
  2. Mandatory: Click sounds turned off silences the clicks at once, in the menus and for Left and Right in the story, and on brings them back.
  3. Optional: the actions menu clicks as you move between choices, under each choice's clip.
  4. Optional: the F1 screen clicks as you move, but not when you press the key to bind.

## What was built

Built 2026-10-21, waiting for the dev's ear tests:
- **`App.play_sound()`** plays `click-good` and `click-bad` only while `click_sounds` is on; `App.click()` plays `click-good`.
- **`ui/menu.py`:** moving clicks, and choosing and going back too, unless a menu sets `click_on_choose` or `click_on_back` off, as the actions menu does. A key the menu has no use for plays nothing.
- **`ui/keybind_screen.py`:** clicks on moving, Enter, Escape and F1, never on the key being bound.
- **Settings:** the Click sounds row after Skip opening screens; `click_sounds` on by default.
- **Tests:** two new, in `test_menus.py`; 223 in all, the whole suite passing.

## Built in sections

One section.

## Open questions

None.
