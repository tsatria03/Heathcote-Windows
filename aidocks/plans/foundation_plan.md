---
name: foundation_plan
description: "Plan 2: the heathcote package, the Heathcote.py entry script and screen loop, save-folder paths, logs and crash files, screen reader speech, the timer loop, settings and keys files, the F1 screen and the spoken menu."
metadata:
  node_type: memory
  type: project
---

**Status:** being built (the dev, 2026-10-19: "I'm ready for section 1 of plan 2."). Section 1 is confirmed ("it looks good."), and so is section 2 ("Section 2 is good."); section 3 is built and waits for the dev to confirm it.

Plan 2 ([[reading_original_plan]] lists the order). Everything else stands on it: the audio, the story engine, the menus and the saves all use its paths, speech, timers and screen loop.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. The entry script, paths, logs and the crash file.
2. Speech and the timer loop.
3. The settings and keys files, the screen stack, the spoken menu and the F1 screen.
4. The silent test setup, `tests/case/_quiet.py` and `tests/suite.py`.

Until the menus plan is built, the game opens on a small stand-in menu, Settings and Quit, so its speech, keys and window can be tried by ear.

## Progress

- **Section 3, built 2026-10-19, waiting for the dev's word:**
  - `heathcote/platform/files.py`: the safe JSON files. One change from the reference: a damaged file with no backup is still marked for rewriting, so it is replaced with the defaults at once rather than left damaged.
  - `heathcote/platform/settings.py`, writing `config/settings.json`:
    - the three volumes, `master_volume`, `backgrounds_volume` and `interface_volume`, from 0 to 100
    - `debug`
    - `first_run_notice_shown`
  - **The volume step is 10 percent**, a default chosen in the build, since no plan named one. A level that is not a multiple of 10 is put back to its default.
  - `heathcote/platform/keymap.py`, writing `config/keys.json`.
    - **Each action has a group:** menu (every spoken menu, the actions menu included), story, or everywhere (the volumes).
    - **Clashes:** a key clashes only within its group or with an everywhere key. So Up can both move in a menu and open the actions menu, and Escape can both go back and pause.
    - **The menu keys are actions too, so they are rebindable**, as the story engine plan says of the arrows. Space, which says a choice's text, is in the menu group.
  - **The F1 screen** (`heathcote/ui/keybind_screen.py`) reads its own keys directly, never from the key map, so a player who unbinds the menu keys can always come back and put them right. F1 and Escape can never be bound.
    - Enter rebinds, A adds a key, Delete unbinds, and R twice resets.
    - Rebinding says what a binding was taken from.
  - `heathcote/ui/screens.py` and `heathcote/ui/menu.py`: the screen stack and the spoken menu. A menu's `moved()` says the row; the actions menu will play its clip there instead.
  - `heathcote/app.py`: the main loop at 60 frames a second.
    - F1 from anywhere, holding the timers.
    - The volume keys from anywhere, each saying "Master volume, 90 percent.", for example, and repeating while held.
    - Focus changes are passed to the top screen.
    - The window shows the top screen's lines and the last line spoken.
    - `--exit-after` runs on the timer loop.
  - **Debug mode:** `--debug` turns it on for one run. The Settings row turns it on or off at once and remembers it, and the window title follows. `--spiel` now checks the App's debug mode, so the remembered setting counts too.
  - **The stand-in menus,** to be replaced by the menus plan:
    - the main menu, `heathcote/game/menus.py`: "Heathcote.", with Settings and Quit, and Escape saying the row
    - Settings, `heathcote/ui/settings_screen.py`: Back, Debug mode (source runs only) and Key bindings
  - Checked silently by key name:
    - moving and wrapping, Home and End, Escape and other keys on the main menu
    - Settings, the debug toggle, and the volumes, including at 100
    - the F1 screen's rebind, add, refusing Escape, a clash with an everywhere key, reset, and F1 closing it and resuming the timers
    - Quit
    - a damaged settings file, and bad values
    - a full silent run of `Heathcote.py`
- **Section 2, confirmed by the dev 2026-10-19 ("Section 2 is good."):**
  - `heathcote/platform/speech.py`: NVDA's own client first, then Prism's screen readers, then a Windows voice, as decided. The prismatoid package, 0.18.2, is installed.
  - `heathcote/platform/runloop.py`: `after`, `every`, `cancel`, `hold`, `resume` and `remaining`, on `time.perf_counter`. The stand-in window pumps it once a frame.
  - **One change from the reference:** a call made while the loop is held counts its delay from the moment the clock stopped. In the reference it counted from when it was made, so a hold already under way when it was made was added on top. Without the fix, a timed set scheduled during the pause would come late.
  - `tests/interact/speech_check.py` tries both by ear:
    - Enter says what is speaking.
    - 1 speaks a line that interrupts, and 2 a line that waits.
    - T counts down on the timer loop.
    - P holds and resumes it.
    - S stops speech.
    - Escape quits.
  - Checked silently with `HEATHCOTE_SILENT`: ordering, repeats skipping missed beats, an error in a call being logged, hold and resume, calls made during a hold, and cancelling.
- **Section 1, confirmed by the dev 2026-10-19 ("it looks good."):**
  - `Heathcote.py` takes the four options, starts the log and writes `crash.txt`.
  - `heathcote/paths.py` finds the game data, the vendored DLLs, `VERSION` and the save folder.
  - The `platform/`, `ui/` and `game/` packages exist, empty.
  - The data counts as found only when `game/data/text/system/Heathcote v1.01.bundle.json` is there. If it is missing, the player is told where the game looked.
  - `--spiel` is checked against the bundle's labels, and a label it doesn't have is logged and ignored. The story engine will use it later.
  - Until section 3 built the screen loop, the game opened a plain window titled "Heathcote", or "Heathcote (debug)", which Escape or closing the window shut.
  - The crash message is spoken once section 2's speech is there; `Heathcote.py` loads it lazily and carries on without it if it cannot start.
  - Checked silently with a dummy video driver and a throwaway save folder: the log and `log.old.txt`, the debug title, `--spiel` with and without debug mode, `--exit-after`, and `crash.txt` for both missing data and an unexpected error.

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
  - **The spoken menu:** rows are read without their place, such as "1 of 2"; Up, Down, Left and Right all move, Up and Left back and Down and Right on, wrapping round; Home jumps to the first row and End to the last (the dev, 2026-10-19: "this game should be like [the other game] where you can press all the arrow keys for menu choices, plus home/end."). Shift+Home and Shift+End stay the master volume. Back is the first row of any menu with a way back ([[feedback_back_first]]). The story's actions menu uses the same keys ([[story_engine_plan]]).
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
