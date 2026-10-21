---
name: skip_opening_plan
description: "Plan 10: a Skip opening screens setting, after Debug mode in Settings; when on, the game starts straight at the main menu, without the police radio or the first-run notice."
metadata:
  node_type: memory
  type: project
---

**Status:** built 2026-10-21 on the dev's word ("Exactly right, and yes."), waiting for the dev's ear test.

## What was built

- **`heathcote/game/opening.py`:** `first_screen(app)` gives the opening, or with `skip_opening` on the main menu, setting `first_run_notice_shown` as it skips. `Heathcote.py` and `menu_check.py`'s own start use it; the tool's Control+N still resets to the opening.
- **`heathcote/ui/settings_screen.py`:** the row after Debug mode, toggled by `toggle_skip_opening()`.
- **`heathcote/platform/settings.py`:** `skip_opening`, off by default.
- **Tests:** one new; the Settings tests now find their rows by their words, not their places, so a new row no longer moves them. 221 in all, the whole suite passing. Started silently both ways: the opening by default, the main menu with the setting on.

Plan 10. Asked for by the dev, 2026-10-21: "Please add a setting called skip opening screens. Put it after the debug setting. You can probbably guess what that will do." It changes [[menus_plan]]'s opening and [[settings_plan]]'s Settings screen.

## Decided

- **The row:** "Skip opening screens, currently off", right after Debug mode in Settings, so in a built game, where Debug mode is not shown, it comes right after Back. Enter turns it on or off at once and says the row again, as Debug mode does. Off by default.
- **What it does when on:** the game starts straight at the main menu, with the title music, leaving out the opening screens: the police radio with "Heathcote.", and the first-run notice. The main menu still says "Heathcote." as it opens.
- **The notice:** skipping counts as having shown it, so turning the setting off again later never brings the notice back.
- **Saved** in `config\settings.json` as `skip_opening`, on or off.
- **Elsewhere:** `menu_check.py`'s Control+N, which forgets the notice and starts again from the police radio, still shows the opening whatever the setting, so the opening can always be heard there.
- **Ear tests:**
  1. Mandatory: turn the setting on, quit, start again: the game opens straight on the main menu with the title music, with no police radio.
  2. Optional: turn it off again: the police radio comes back on the next start, and the first-run notice does not.

## Built in sections

One section.

## Open questions

None, unless the guess above is not what the dev meant.
