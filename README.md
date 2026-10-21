# Heathcote-Windows

A Windows port, in Python, of **Heathcote** (`com.fabulaeobscurae.heathcote` 1.01,
Fabulae Obscurae), an interactive audio adventure for iPhone and iPad, "told through
sound". You follow a presenter exploring an abandoned asylum while he is on the phone to
his producer, and you choose what he does next from an actions menu.

The original was played by swiping. This port is for the keyboard and for screen
readers, so the whole game can be played without sight.

**Headphones are recommended.** The original says so itself: "Heathcote is a responsive
story told through sound. Headphones are strongly recommended."

## Status

**The port is being built. The whole game can now be played,** from its opening and main
menu, through the story by the original's rules, to its end credits, with the progress kept
between runs. The built game is still to come. The work is split into seven plans, in
`aidocks/plans/`:

1. **Reading the original: finished.** Tools that read the original's binary and story
   data, a readable script of the whole story, and a note of how the original behaves,
   with every number taken from its code.
2. **The foundation: finished.** In it:
   - `Heathcote.py`, with its logs and crash file
   - speech through your screen reader, and a timer loop that can pause
   - the settings and key bindings, every key rebindable with F1
   - the four volumes
   - the spoken menus, with a stand-in main menu until plan 5's
   - 65 silent tests
3. **The audio: finished.** Every sound plays through FMOD, the engine the original used:
   - the original's channels, and four volumes in even steps of 6 decibels
   - the spiel, with the original's rewind, and its fast-forward at 1.75 times with
     voices kept at their pitch
   - the hush, which muffles the backgrounds, and the original's pause, in which the
     backgrounds play on muffled while the voice stops
   - the four background lanes, crossfading on each spiel's cues and set up again after
     a rewind, the idle loop, and the story's fades
   - `tests\interact\audio_check.py` to hear all of it
4. **The story engine: finished.** The story plays by the original's rules:
   - the variables, timed sets, `next` and the end, with only a scene's last spiel marked
     heard, and timed sets firing again after a rewind, as in the original
   - lockout, and the actions menu with each choice's recording, Space speaking its text
   - the keys during play: rewind, fast-forward, the original's pause, Tab, and pausing
     when the window loses the keyboard, with a stand-in pause menu until plan 5's
   - debug mode's F2 to F4, and `--spiel`
   - `tests\interact\story_check.py` to play it by ear, and 154 silent tests in all
5. **The menus: finished.** The screens around the story:
   - the opening, with the original's police radio, and the first-run notice
   - the main menu, with Start story or Continue story, Settings, Credits and Quit, and the
     title music under it, played and faded as the original did
   - the pause menu, with Resume, Restart story, Settings and Return to menu, which leaves
     the story paused for Continue story
   - the end credits over the story's last moments, the original's credit cards as text
   - `tests\interact\menu_check.py` to hear it all, and 166 silent tests in all
6. **Saving: finished.** The story's progress between runs:
   - `saves\progress.json`, written safely as each spiel begins, with a snapshot of the
     story and its background sounds then, and the chapter kept apart
   - Continue story, from the save, plays the spiel you were in again from its start,
     whether you left by Return to menu or by quitting
   - Restart story starts the save afresh, the end clears it, and debug mode's jumps never
     write it
   - Tab says the chapter, such as "Story is playing: working late."
   - `menu_check.py`'s Control+D to clear its progress, and 182 silent tests in all
7. **Building and releasing:** next.

What was found in the original:

- The game is driven almost entirely by data. The story is JSON exported from the
  original's authoring tool. It is made of choices with conditions, and recordings
  ("spiels") that set variables at timed points and lead on to the next. Music and three
  ambience lanes crossfade at timed points too.
- The port reads that JSON directly, as it is. `tools/story.py` checks it the way the game
  reads it, and finds no problems that would break the game.
- The binary, `game/Heathcote`, is not encrypted, so the original's behaviour could be
  read from its code with `tools/dis64.py`, down to its exact timings.

## Requirements

To run it from source, the port needs 64-bit Python 3.12 or newer on Windows 10 or later,
and three packages:

    pip install -r requirements.txt

- `pygame`: the window, the keyboard and the frame loop. It plays no sound.
- `prismatoid`: Prism, which speaks through any screen reader other than NVDA, or through
  a Windows voice when none is running.
- `pyfmodex` 0.7.2: the connection to FMOD, which plays every sound.

FMOD itself is not in the repository, since its licence lets it be passed on only inside
the game. Install the FMOD Engine 2.02.35 for Windows from fmod.com (a free account is
needed), and copy `api\core\lib\x64\fmod.dll` from its install into `vendor\fmod\`.
Without it, the game says so and where to copy it from, rather than starting silently.

`vendor/nvda/nvdaControllerClient64.dll` ships with the repository, so NVDA speaks through
its own client.

## Running it

From the repository's folder:

    python Heathcote.py

It opens with the original's police radio, which Enter skips, then, the first time only,
the original's advice to wear headphones, which Enter passes. Then the main menu, spoken
through your screen reader, with the title music under it:

- **Start story** plays the story from its start. While the save has a story under way,
  it is **Continue story** instead, said with the story's chapter, such as "Continue story:
  approaching Heathcote.", and plays the spiel you were in again from its start, with the
  story's state and background sounds as they were as it began.
- **Settings** has Back, Debug mode (from source only) and Key bindings.
- **Credits** reads the original's credits a row each, Back first, with the port's row and
  FMOD's credit line.
- **Quit**, or Escape, closes the game.

During the story, each key rebindable with F1:

- **Up or Enter** opens the actions menu: the arrows, Home and End move through the
  choices, each playing its recording; Enter accepts, Escape closes, and Space speaks the
  choice's text. While a spiel is locked out, the menu is refused.
- **Left and Right** rewind and fast-forward.
- **Escape** pauses, the backgrounds and the idle loop playing on muffled, with the pause
  menu: Resume; Restart story, which asks first; Settings; and Return to menu, which ends
  the story, its progress saved for Continue story.
- **Tab** says where you are: playing, at the end of a scene, or in the actions menu, then
  the chapter, the story variable `location`, once a scene has set it.
- Switching to another window pauses, and coming back resumes by itself, unlike the
  original; a pause made with Escape stays.
- In debug mode, **F2** skips to the end of the spiel, **F3** jumps to any spiel by part
  of its label, and **F4** says the variables that are not 0.

When the story ends, the end credits open while its last moments play on, with the ending
music. Back or Escape leaves them, resetting the story, and the main menu offers Start
story again.

Every menu moves with all four arrows, wrapping round at either end, with Home and End
for the first and last row, Enter to choose, and Escape to go back. Back is the first row
of every menu that has one. F1 opens the key bindings from anywhere.

The volume keys, each step 10 percent, which is 6 decibels, so every step sounds the
same, with 0 silent, and each level spoken:

- Shift with Home and End: the master volume, from anywhere.
- Page Up and Page Down: the title volume wherever the title music plays, and the
  background volume during the story and its end credits.
- Shift with Page Up and Page Down: the interface volume, during the story: the game's own
  sounds. The recorded choices follow only the master, as the story's voices do.

Everything the game keeps is in `%APPDATA%\Heathcote`:

- `config\settings.json` and `config\keys.json`: the settings and the key bindings, each
  written safely with a backup;
- `saves\progress.json`: the story's progress, written the same way;
- `logs\log.txt`, with the run before as `log.old.txt`, and `logs\crash.txt` when an error
  stops the game, which is spoken too.

The options:

- `--debug`: debug mode for this run. From source, the Settings screen's Debug mode row
  turns it on for good, and the window's title says "Heathcote (debug)". It gives F2 to
  F4 during the story.
- `--spiel LABEL`: in debug mode, the first Start story begins at any spiel by its label, such as
  `--spiel cells`. The labels are the "Spiel:" headings of
  `analysis/script/Heathcote.txt`.
- `-v`: a more detailed log.
- `--exit-after SECONDS`: quit by itself.

## Tests

    python tests\suite.py

runs every test in `tests\case`, several at once, writing the results to `tests\results`.
Some files can be run by name, such as `python tests\suite.py keymap menus`, and any file
runs on its own too, such as `python tests\case\test_keymap.py`. The tests never speak,
never play a sound, never open a window, and never touch your save.

FMOD runs in every test with its no-sound output, so the sound code is tested for real
without a sound device.

`tests\interact` holds tools to try the game by ear instead. Each keeps its own save, so
none changes your settings or keys.

- `python tests\interact\speech_check.py` tries the speech and the timer loop.
- `python tests\interact\audio_check.py` plays the game's sound through FMOD:
  - the title music, any ambience and the interface sounds
  - all four volumes
  - any spiel with its own background lanes and idle loop, found with S by part of its
    label, with rewind, fast-forward and the original's pause
  
  It says its keys as it opens, and lists them all at the top of the file.
- `python tests\interact\story_check.py` plays the story by its rules, on the game's own
  screens, in debug mode for that run only:
  - the game's keys, and F2 to F4
  - R to start again, Comma and Full stop to choose any spiel, and 3 to play it
  - S for where the story is, V for the spiel labels as they begin, C for each variable
    as it changes, H for what has been heard, and A for the actions on offer
  - Q to quit
  
  If it stops on an error, it writes `crash.txt` in its logs folder and says so.
- `python tests\interact\menu_check.py` runs the game itself from its opening, with keys of
  its own, each with Control:
  - Control+N forgets the first-run notice and starts again from the police radio
  - Control+T says whether the title music is playing, and whether the story's sound is
    faded in or out
  - Control+S says where the story is: playing, paused, over under the end credits, or in
    the save to continue
  - Control+E jumps the story to 7.5 seconds before its end, to hear the end credits
  - Control+D clears the tool's progress file
  - Control+Q quits

## Building

`compiler.py` builds the game with PyInstaller (`pip install pyinstaller`) into
`dist\Heathcote-Windows\`, around `Heathcote.exe`. It only builds: it never zips and never
changes the repository. First copy `fmod.dll` into `vendor\fmod\`, as for running from
source; without it the compiler stops and says where to get it.

Run `python compiler.py` with nothing after it, or double-click it, for a numbered menu, or
give the choice on the command line:

- `python compiler.py`: the folder build, the exe with its files and `game\` beside it
- `python compiler.py --embed`: a single exe, the game's data inside it
- `--test` with either: start the finished build silently for a few seconds, on a
  throwaway save, and check its log found the game data, started FMOD and closed cleanly
- `--clean`, `--console`, `--onefile`, `--no-game` and `--dry-run`, which says what a
  build would do and builds nothing

A build carries `game\documents\Audio` and `game\documents\text` and nothing else of
`game\`, both DLLs, Prism and pyfmodex, the third-party licences in `licenses\`, and
beside the exe `docks\`, `VERSION` and the port's licence as `license.txt`.

## Layout

```
game/                    the original app bundle, reorganised (see below)
vendor/nvda/             NVDA's controller client, with its license
vendor/fmod/             FMOD's licence, and fmod.dll, which you copy in yourself
Heathcote.py             the entry script
compiler.py              builds the game with PyInstaller
heathcote/               the port's Python package
docks/                   readme.txt, changelog.txt and todo list.txt, for players
aidocks/general/         the notes for AI-assisted work (see CLAUDE.md)
aidocks/plans/           every plan, planned or finished
analysis/                what the tools write from the original, such as the script
tools/                   the tools that read the original (see tools/README.md)
tests/case/              the tests, one plain script each
tests/suite.py           runs them all
tests/interact/          tools to try the game by ear
requirements.txt         the three packages it needs
VERSION                  the version, as year, month, day and that day's number
```

### `game/`: the original's data

`game/` holds the original app bundle, reorganised into folders. The port never writes to
it.

- `game/documents/text/system/Heathcote v1.01.bundle.json` is the story's master index: every
  record's label, and each kind's records.
- `game/documents/text/story/` holds the story's records, one JSON file each, named by its id.
- `game/documents/Audio/story/` holds the story's 206 recordings, one folder per kind, each
  under its English name. The original named them by id;
  `aidocks/general/project_audio_names.md` maps each name back.
- `game/documents/Audio/System/` holds the 16 interface sounds, in `menu/` and `misc/`.
- Every recording is MP3, converted from the original's files.
- `game/Heathcote` is the original's binary, read by the tools and never shipped.

## Version numbers

A version is the date and that day's number: `26.10.19-1` is the first version of the 19th
of October 2026.

## Credits

**[tsatria03](https://github.com/tsatria03)** makes the port, on their own.

Heathcote itself is Fabulae Obscurae's game:

- Story: Christian Francis, Ben Meares
- David Scott, Fausto Kaufer, Joe Banks: Hunter Davis
- Martin Fellows: Robert Dunne
- Announcer: Mark Hamilton
- Music: Jason Martin Castillo
- Design and Engineering: Mike Dean
- Producing and Directing: Lisa Wong
- Audio Consultant: Alex Ruger
- Special thanks to Nowell Valeri

The original uses many sounds from freesound, listed at fabulaeobscurae.com/heathcote.

FMOD Studio by Firelight Technologies Pty Ltd.

## Licence

The port's code is under the MIT License, in `LICENSE`. Everything under `game/` is
Fabulae Obscurae's and is not covered by it.

The third-party pieces keep their own licences:

- FMOD Engine, Firelight Technologies Pty Ltd.'s own licence, in `vendor/fmod/license.txt`
- the NVDA controller client, LGPL 2.1: <https://github.com/nvaccess/nvda/blob/master/extras/controllerClient/license.txt>
- Prism (`prismatoid`), MPL 2.0: <https://github.com/ethindp/prism>
- CFFI, which Prism uses, MIT: <https://github.com/python-cffi/cffi/blob/main/LICENSE>
- pygame, LGPL 2.1: <https://github.com/pygame/pygame/blob/main/docs/LGPL.txt>
- pyfmodex, MIT: <https://github.com/tyrylu/pyfmodex>
