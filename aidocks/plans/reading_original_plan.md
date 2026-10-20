---
name: reading_original_plan
description: "Plan 1: tools to read the original's binary and story data, a readable script of the whole story in analysis/, and a note of the original's run-time behaviour with exact numbers, for every later plan to build on."
metadata:
  node_type: memory
  type: project
---

**Status:** being built (the dev, 2026-10-19: "Sure! Go ahead.", then "Please build the entire plann1. Section 1 looks good."). Section 1 is confirmed. Sections 2, 3 and 4 are built, not yet confirmed.

**Built so far:**
- Section 1, confirmed: `tools/macho64.py`, `tools/dis64.py` and `tools/README.md`. Beyond the plan, `dis64.py` also has `--find`, methods whose selector holds a word; `--refs`, the game's code that uses an address or calls a selector; and `--brief`, only the lines that carry meaning. `--refs` was needed straight away: the lockout grace timer is kept in a global, so the method that starts it could only be found by its uses.
- Section 2: `tools/story.py`. It reports no problems. Its notes, all as the original plays:
  - The broken recap record, in a category the original never reads.
  - Three records with no recording: the spiel "east wing dispatch", which only chooses its next, and the voices "next room" and "just stop".
  - Two actions the original never offers, since nothing sets the value they ask for: "where you at? (entering east wing)" and "where you at? (records room, light)". So the spiel "where you at? (records room - light)" is never reached.
  - "east wing dispatch" has three next entries, and "east wing (blocked 3)", listed first, can be true together with either of the others.
  - No two spiels, and no two actions, share a label, so `--spiel LABEL` is never ambiguous.
  - One recording's original name has a space before its extension, "idle loop (inside entrance) .mp3"; the lookup trims it, as the rename did.
- Section 4: [[project_original_behaviour]], read with the tools by a helper agent and spot-checked: the plain `ambience` key is never read, rewind steps back 1 second for 45 ticks, and fast-forward runs at 1.75 times. Reading it showed that listings stopped at a method's first `ret`, missing code after an early return, so `dis64.py` gained `--full`, and `--refs` now always reads in full; it then found a caller of `remindedThatSpielHasEnded` it had missed.
- What section 4 changed in the earlier tools: the first matching `next` wins, so `story.py` now notes overlapping entries as precedence, and it notes fades on the plain `ambience` lane as never played; the script says both.
- The dev moved the 14 interface sounds into `game/data/Audio/System/menu/` and `System/misc/` on 2026-10-19, so `story.py` now looks for a category's recordings in a list of folders.
- Section 3: `tools/script_text.py` and `analysis/script/Heathcote.txt`, 2234 lines. The walk tracks every value seen so far, defaults included, so an action opens as soon as its whole condition is possible; 103 spiels come in story order and the dead one comes after.

## Why

The story itself is readable JSON ([[project_original_findings]]). What the JSON does not say is how the original behaves while it plays, and those details are only in the binary. Examples:
- how the actions menu is ordered, announced and wrapped
- how long the lockout grace period lasts
- when the menu reminder and the "spiel has ended" reminder fire
- how far rewind and fast-forward jump
- how the fades, the muffle and the idle loops are timed
- what the two-finger "describe" tap says
- what is saved, and when

Every later plan needs those numbers so the port sounds like the original. This plan gets them first, with tools that can be rerun, and writes them down.

## Where this fits

The plans, in their intended order. Only this first one is written so far; each of the others gets its own note, with its own questions, before any code:
1. Reading the original (this plan).
2. Foundation: the package, the entry script, paths, logs, speech, settings, keys and the main loop.
3. Audio: the spiel channel, the ambience lanes, the music, the idle loops, the fades and the system sounds.
4. Story engine: the variables, the timed sets, the conditional next, lockout, the actions menu's choices and burning them after reading.
5. Menus and screens: the logo, the headphones notice, the title, the pause menu, the end and the credits.
6. Saves.
7. Build and release.

The order and the list can change as questions are answered.

## Built in sections

Each section is confirmed by the dev before the next starts.

### Section 1: reading the binary
- `tools/macho64.py`, adapted from the reference material in the gitignored `user/` folder.
  - Heathcote's binary is a thin arm64 file, with no fat header, so the tool reads it as it is instead of looking for a slice.
  - It lists the segments and sections, the Objective-C classes with their methods and instance variables, the selector references and the imported functions.
  - It checks `cryptid`, which is 0.
  - `HEATHCOTE_BINARY` sets the path of the binary; the default is `game/Heathcote`.
  - Standard library only.
- `tools/dis64.py`: disassembles a method by `Class selector:` or by `--at 0xADDR`, naming the selectors, imported functions, classes and strings each instruction refers to.
  - It needs `capstone`, which is installed (5.0.7). The game itself never needs it.
- FMOD 1.7 is linked into the binary, and most of its size is FMOD. The tools skip it, reading only the game's own classes.
- `tools/README.md` says what each tool does, with examples.

### Section 2: reading the story data
- `tools/story.py`: loads `game/data/text/system/Heathcote v1.01.bundle.json` and every record in `game/data/text/story/`, resolving each softRef to its record, its label and its file.
  - A recording is found the way [[project_audio_names]] says: its record's `original.name`, with `.mp3` in place of its extension and any character Windows does not allow dropped, in the folder for its bundle category. Graphics are still `<id>.png`.
  - It skips the broken recap record (`iRRuxKjogQweYZQWS.json`) with a warning.
- It checks the data and prints any problem:
  - every softRef in an action, a `next`, a `set`, an ambience, the music or an idle loop leads to a real record
  - every record's file exists
  - every variable read in an `if` is set somewhere, or has a known default
  - every spiel can be reached from the start
  - no spiel has two `next` entries that can both be true at once
- Standard library only. It only reads; it writes nothing under `game/`.

### Section 3: the readable script
- `tools/script_text.py` writes the whole story as plain text into one file, `analysis/script/Heathcote.txt`.
- For each spiel: its label, its transcript, each timed `set` with its time, its `next` and its idle loop.
- For each action: its spoken label, its condition, its order, whether it burns after reading, and the spiel it plays.
- Written for reading by screen reader: plain lines, no tables.

### Section 4: the original's behaviour
- Read the game's own classes with the tools, in this order:
  - `StateManager` and its states: `IdentState`, `PreflightState`, `TitleState`, `TitleMenuState`, `PlayState`, `ActionsDialState`, `PausedState`, `WaitState` and `EndState`.
  - `BundleManager`, which reads the bundle and the variables.
  - `Dial`, the actions menu.
  - The audio wrapper around FMOD.
- Write what they do, with exact numbers and the address of each method, into a new note, `aidocks/general/project_original_behaviour.md`.
- Split it into "confirmed from the code" and "not yet confirmed".
- Already found while testing section 1, to go into the note: `+[StoryView raiseActionsDial]` (0x100024204). With `lockout` at "1", the last spiel not heard before, and the `lockoutOverride` setting off, it plays `click-bad` and `menu-unavailable` and starts a 1.5-second grace timer (0x100024560). Otherwise it plays `click-good`, hushes the backgrounds once, pauses the spiel, and enters `ActionsDialState`.

## Decided
- `game/` is never written to; every tool only reads it.
- The tools are not part of the game, and are never shipped in a build.
- No tool plays sound or speaks, so they can be run without asking ([[feedback_dont_run_or_build]]).
- No save import from the original.
- **The game reads the original JSON directly** (the dev, 2026-10-19: "I want it to read it directly if possible."). There is no exported copy. The game's own loader reads `game/data/text/` as it is, and `tools/story.py` shares its rules so that the checks and the game agree. If something in the data cannot be read as it is, a fix is made in code at load time, never by editing `game/`, and it is raised with the dev first.

- **The readable script is one file**, `analysis/script/Heathcote.txt` (the dev, 2026-10-19: "I recommend one file because unlike [the other game], these are not episodes. It's just one long episode with branched choices in the middle if you think about it."). It runs in the order the story plays from the start, and each spiel begins with its label on a line of its own, so NVDA's find can jump to it.

- **The behaviour goes in `aidocks/general/project_original_behaviour.md`** (the dev, 2026-10-19: "Yes."), not in `analysis/`. `analysis/` holds only what the tools write and can write again; the behaviour is written by hand, cited by every later plan, and read by each session from `aidocks/`.

## Open questions

None.
