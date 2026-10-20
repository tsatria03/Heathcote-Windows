---
name: saves_plan
description: "Plan 6: what the game remembers between runs, in %APPDATA%\\Heathcote: the story's progress (variables, heard spiels, action counts, where to continue, the lanes playing) and the settings, written safely as the original wrote every change."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, with every question answered (2026-10-19). Waiting for the go-ahead to build.

Plan 6 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]]'s paths and safe JSON files, and keeps what [[story_engine_plan]] and [[menus_plan]] hold in memory. What the original saved comes from [[project_original_behaviour]].

## What the original saved
- Five stores in the iOS settings, each change written at once under "<store>/<name>" (`-[Vars applySetForVar:val:]`, 0x100030a34):
  - **story:** every story variable, as text.
  - **heard:** whether each spiel has been heard.
  - **actioned:** how many times each action has been chosen.
  - **teller:** whether the story has started, the spiel to continue from, and the four background lanes playing when that spiel opened (`opening-bgm` and `opening-ambience1` to `3`), plus the tutorial's flags and counts.
  - **config:** four developer switches, all off.
- **Continue replays the last spiel an action opened, from its beginning,** with its lanes as they were when it opened (`+[Story startTape]`, 0x10001a898; `+[StoryView newTape:]`, 0x100024020). A spiel reached through next is never the resume point.
- Restart reset story, heard and actioned, and left the rest.

## What plan 3 built for it

The audio plan, finished 2026-10-20 ([[audio_plan]]), left these ready for the saves:
- **The lanes at a spiel's start:** `Lanes.opening` is what the four lanes held as the current spiel began, by softRef, for the snapshot.
- **Restoring them:** `Lanes.restore(held)` starts them again with the original's 0.5-second fade-in when the story opens.
- **The settings:** the title volume is the fourth volume in `config\settings.json`.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. The progress file and the settings file, read on start and written safely.
2. Continue story, Restart story and the end's reset, using them.

## Decided

- **Everything is kept in `%APPDATA%\Heathcote`**, or `HEATHCOTE_USER_DIR` when set ([[foundation_plan]]):
  - `saves\progress.json`: the story's variables, the heard spiels, the actions' counts, whether the story has started, where to continue, and the lanes playing there.
  - `config\settings.json`: the four volumes (master, backgrounds, interface and title), debug mode, and whether the first-run notice has been shown.
  - `config\keys.json`: the key bindings ([[foundation_plan]]).
- **Every file is written safely,** a temporary file first, then a `.bak` of the old one, then a swap; a damaged file is kept as `.damaged` and the backup read instead ([[foundation_plan]]).
- **Saved by softRef id, not by label,** since the ids never change while a label could be shared or edited.
- **Restart story and the end reset** the variables, the heard spiels and the actions' counts, and go back to `start`, leaving the settings and the first-run notice alone, as the original did.
- **Continue story picks up at the start of the spiel the player was in** (the dev, 2026-10-19: "I like the option 2 method."), whether a choice or a next led there, unlike the original, which only ever saved the spiel a choice opened. The save keeps that spiel's softRef and a snapshot taken as it began: the story's variables, the heard spiels, the actions' counts and the four lanes playing. Continue restores the snapshot and plays the spiel from its beginning, so its timed sets apply once, not twice, and its fades line up as they did. Closing the game mid-spiel replays at most that one spiel.
- **When progress is written** (the dev, 2026-10-19: "agreed"): as each spiel begins, when its snapshot is taken, and when a spiel is marked heard. Timed sets are not written as they fire, as the original's were, since Continue replays the spiel from its snapshot anyway. Settings are written whenever one changes.
- **No import of a save from the original app.**
- **Tests use a throwaway save folder** and never touch the real one ([[feedback_dont_run_or_build]]).

## Open questions

None.
