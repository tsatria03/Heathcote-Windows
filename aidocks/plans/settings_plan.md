---
name: settings_plan
description: "Plan 8: the Settings screen gains a row for each of the four volumes, opening a list of levels, and a Volume speed row for how fast a held volume key repeats; adapted from the reference material's Settings, without its volume step or seek settings."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, 2026-10-21, waiting for the dev's word to build.

Plan 8, after the first release. Asked for by the dev, 2026-10-21: "I found that the settings screen barely has anything in it besides key bindings. Can you look at the other port to see what settings it had?" Adapted from the reference material's Settings screen, never naming it ([[feedback_no_other_games]]). It stands on [[foundation_plan]]'s settings and menus and [[audio_plan]]'s four volumes.

## Decided

- **What comes over** (the dev, 2026-10-21: "I want the volume rows for sure, plus volume speed, but we can discard volume step."):
  - a row for each of Heathcote's four volumes
  - Volume speed
- **Left out:** Volume step, since Heathcote's steps stay 10 percent, each 6 decibels, so every press sounds the same ([[audio_plan]]); Seek step and Seek speed, since rewind and fast-forward stay the original's; and speech recognition, which Heathcote never had.
- **The rows, in order,** Back first ([[feedback_back_first]]):
  1. Back
  2. Debug mode, from source only, as now
  3. "Master volume, 100 percent"
  4. "Background volume, 100 percent"
  5. "Interface volume, 100 percent"
  6. "Title volume, 100 percent"
  7. "Volume speed, 100 milliseconds"
  8. Key bindings, as now
- **A volume row** opens a list of its levels, titled with its name, such as "Master volume.": Back first and opened on, then 100 percent down to 0 percent in 10 percent steps. Enter picks a level, which takes effect at once, is saved, and returns to Settings saying the row, such as "Master volume, 70 percent". Escape, or Enter on Back, keeps the volume as it was. The names are the ones the volume keys already speak (`VOLUME_LABELS`).
- **Every volume can be set from Settings,** from the main menu or the pause menu, wherever its keys work or not. The keys stay as they are.
- **Volume speed** opens the same kind of list: 50 to 500 milliseconds in steps of 50, default 100, the ends said as "50 milliseconds, fastest" and "500 milliseconds, slowest". It sets how often a held volume key repeats. The 0.4-second wait before repeating starts stays fixed.
- **Saved** in `config\settings.json` as `volume_speed`; a value not in the list is put back to 100, as every setting is.
- **Nothing to test by ear** (the dev, 2026-10-21: "For these settings, we do not need interactive tests."). The silent tests cover the rows, the lists, Escape keeping a value, saving, and the held key repeating at the chosen speed.

## Built in sections

One section: the rows, the level lists and the repeat speed, with their tests and the docs.

## Open questions

None.
