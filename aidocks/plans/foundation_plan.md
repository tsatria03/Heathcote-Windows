---
name: foundation_plan
description: "Plan 2: the heathcote package, the Heathcote.py entry script and screen loop, save-folder paths, logs and crash files, screen reader speech, the timer loop, settings and keys files, the F1 screen and the spoken menu."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, with every question answered (2026-10-19). Waiting for the go-ahead to build.

Plan 2 ([[reading_original_plan]] lists the order). Everything else stands on it: the audio, the story engine, the menus and the saves all use its paths, speech, timers and screen loop.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. The entry script, paths, logs and the crash file.
2. Speech and the timer loop.
3. The settings and keys files, the screen stack, the spoken menu and the F1 screen.
4. The silent test setup, `tests/case/_quiet.py` and `tests/suite.py`.

Until the menus plan is built, the game opens on a small stand-in menu, Settings and Quit, so its speech, keys and window can be tried by ear.

## Decided

- **The name is "Heathcote" everywhere,** following the stub folders the dev made:
  - the window title: Heathcote
  - the entry script: `Heathcote.py` at the repo root
  - the package: `heathcote/`
  - the built game: `Heathcote.exe`
  - the save folder: `%APPDATA%\Heathcote`, or `HEATHCOTE_USER_DIR` when set
- **The package is split in three:**
  - `heathcote/platform/`: the parts that talk to Windows (speech, timers, files, settings, keys)
  - `heathcote/ui/`: keyboard input, menus and screens
  - `heathcote/game/`: the story and what is particular to Heathcote
- **Windows only, Python 3.12 or newer, 64-bit** ([[project_windows_only]], [[project_python_only]]).
- **Adapted from the reference material in the gitignored `user/` folder,** renamed and cut down, never naming where it came from ([[feedback_no_other_games]]). These are the dev's standing choices there, carried over as they are:
  - **Speech:** NVDA through its own client first, then any other screen reader through Prism, then a Windows voice. It has `speak(text, interrupt)` and `stop()`, rechecks which screen reader is running every few seconds, and loads Prism only when NVDA is not running. `HEATHCOTE_SILENT` turns it off for tests.
  - **Timer loop:** delayed calls and repeating timers, pumped once a frame on wall-clock time, with `hold()` and `resume()` that shift every waiting timer by the pause. The timed variable sets, the lockout grace, the reminders and the fades will all run on it.
  - **Settings files:** short JSON files written safely (a temporary file first, then a `.bak` of the old one, then a swap). A damaged file is kept as `.damaged` and the backup loaded instead. Every setting is written from the first start, and a bad value is put back to its default.
  - **Logs:** every run writes `logs/log.txt` in the save folder and keeps the run before as `log.old.txt`. An error that stops the game writes `logs/crash.txt` and is spoken aloud, so a blind player knows why the game closed.
  - **Screen loop:** a stack of screens at 60 frames a second. A screen can open another on top, close itself, or replace the stack. Switching away from the window is passed to the top screen, so the story can pause.
  - **The spoken menu:** rows are read without their place, such as "1 of 2"; Up, Down, Left and Right all move, wrapping round; Back is the first row of any menu with a way back ([[feedback_back_first]]).
  - **F1 key bindings screen:** every action rebindable, spoken in full, from anywhere in the game, with the timers held while it is open. F1 and Escape are fixed, so there is always a way out. A binding is one key with exact modifiers, saved in `config/keys.json`.
  - **Master volume:** Shift+Home raises it and Shift+End lowers it.
- **A debug mode, for source runs only** (the dev, 2026-10-19: "a debug mode would be extremely useful for this game for skipping to any part of the story I want"). It is turned on by `--debug` or by a Debug mode row in Settings, shown only when running from source, remembered between runs, and switched on or off at once without a restart. It never exists in a built game. The window title says "Heathcote (debug)" while it is on. Its keys skip the current spiel, jump to any spiel by its label, and speak every variable's value; the exact keys are settled in the story engine plan.
- **The window shows plain text for a sighted helper** (the dev, 2026-10-19: "Yes."): in a menu, its rows; during the story, the transcript line of the spiel playing and the actions on offer. It is secondary: the speech and the audio are the real interface, and nothing is only in the window.
- **Four command-line options** (the dev, 2026-10-19: "I agree."):
  - `--debug` turns on debug mode.
  - `--spiel LABEL`, in debug mode only, starts the story at any spiel by its label, such as `--spiel "east wing (blocked 1)"`.
  - `-v` writes a more detailed log.
  - `--exit-after SECONDS` quits by itself after that many seconds, so the build test can start a built game silently and check it runs.
- **What interrupts what** (the dev, 2026-10-19: "I agree."). These cover screen reader speech only; the recorded menu choices in `speech/` are settled in the menus plan ([[project_later_topics]]).
  - Each move in a menu cuts off what was being said, so fast arrowing never builds a backlog.
  - A key the player presses, such as a volume change, speaks at once, cutting off earlier speech but never the story audio, which keeps playing underneath.
  - Important messages, such as an error, are never cut off by background events, only by the player pressing a key.
  - Speech never pauses the story. Only the pause key does.
- **Tests stay silent and off the real save** ([[feedback_dont_run_or_build]]): every test imports `_quiet.py` first, which points the save at a throwaway folder, turns speech off, gives pygame a dummy video driver, and has FMOD start with its no-sound output ([[project_fmod]]).

## Open questions

None.
