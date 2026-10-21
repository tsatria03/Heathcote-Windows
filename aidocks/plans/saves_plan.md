---
name: saves_plan
description: "Plan 6: what the game remembers between runs, in %APPDATA%\\Heathcote: the story's progress (variables, heard spiels, action counts, where to continue, the lanes playing) and the settings, written safely as the original wrote every change."
metadata:
  node_type: memory
  type: project
---

**Status:** being built, from 2026-10-20, after its review (the dev: "I like your recommendations. Let's start section 1."). Section 1 is built, with nothing to test by ear, and waits for the dev's word.

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

## What plan 4 built for it

The story engine, finished 2026-10-20 ([[story_engine_plan]]), left these ready for the saves:
- **The state:** `StoryState` in `heathcote/game/state.py` holds the variables, heard spiels and action counts by softRef.
  - `snapshot()` copies all three as one dict.
  - `restore()` puts one back, dropping what the story does not know, so an old save still loads.
  - `reset()` is Restart story's.
- **The spiel's start:** `StoryPlayer.on_spiel(soft)` is called as each spiel begins, the moment to take Continue story's snapshot, with `player.lanes.opening` for the lanes. A scene's end marks its spiel heard, the other moment to write.
- **Continue story:** a story screen made with `state=` the restored state and `start_at=` the saved spiel begins there.

## What plan 5 built for it

The menus plan, finished 2026-10-20 ([[menus_plan]]), left these for the saves:
- **Continue story within a run:** Return to menu keeps the paused story screen as `app.paused_story`, and the main menu's first row is "Continue story: <location>." while it is set (`MainMenu.rows()` and `continue_text()` in `heathcote/game/menus.py`). The saves plan makes the row appear at start too, when `progress.json` has a story under way, and Continue then builds a story screen from the save instead of putting a kept one back.
- **Restart story** is `StoryScreen.restart()`, and **the end's reset** is `StoryScreen.end_story()`, both calling `state.reset()`. Each is the moment to write the reset progress.
- **The first-run notice** sets `first_run_notice_shown` in `config\settings.json` already, through `Settings`, which writes on every change.
- **`on_spiel`** is free on the game's story screen (only `story_check.py` sets it), so it can take the snapshot.

## What section 1 built

Built 2026-10-20 and 21:
- **`heathcote/game/progress.py`:** `Progress`, the file `saves\progress.json`, through the same safe `JsonFile` as the settings. It holds `version` (1), `started`, `spiel`, `chapter`, `lanes` and `state`, in that order.
  - `begin(spiel, state, lanes)` takes the snapshot as a spiel begins and writes it.
  - `mark_heard(spiel)` adds a scene's spiel to the snapshot's heard spiels.
  - `set_chapter(text)` keeps `location` apart, written whenever it changes once a story is under way.
  - `clear()` leaves no story under way.
  - `under_way`, `spiel`, `chapter`, `lanes` and `state` read it back.
- **Reading is forgiving:** another version, a spiel the story does not have, or `started` that is not true leave no story under way. A lane naming an unknown recording starts silent, and counts that are not whole numbers are dropped. A damaged file is set aside as `.damaged`, the backup read and written back.
- **`app.progress`** reads it when first wanted, and `Heathcote.py` reads it at start, so the log says whether a story is under way. Nothing writes it yet; section 2 does.
- **The settings file** needed nothing: plan 2 already reads and writes it safely, with the first-run notice in it.
- **Tests:** `tests/case/test_progress.py`, ten of them; 176 in all.
- **Nothing to test by ear:** the save is not used until section 2.

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
- **The chapter is saved apart from the snapshot** (agreed at the review, 2026-10-20). Each scene sets `location` 0.1 seconds in, after the snapshot is taken as its spiel begins, so the snapshot holds the chapter before. The save keeps the current chapter as `chapter` too, written whenever `location` changes, and Continue story's row names it: "Continue story: <chapter>.".
- **Debug mode's jumps never write the save** (agreed at the review). After F3 or `--spiel`, that story writes no progress for the rest of the run, until Restart story or a new Start story, so testing never overwrites real progress.
- **The by-ear tool** for section 2 is `menus_check.py`, which already keeps its own save, grown with a key to clear the progress file ([[feedback_grow_check_tools]]).
- **No import of a save from the original app.**
- **Tests use a throwaway save folder** and never touch the real one ([[feedback_dont_run_or_build]]).

## Open questions

None.
