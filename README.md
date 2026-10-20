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

**The port is being built, and the story cannot be played yet.** The work is split into
seven plans, in `aidocks/plans/`:

1. **Reading the original: finished.** Tools that read the original's binary and story
   data, a readable script of the whole story, and a note of how the original behaves,
   with every number taken from its code.
2. **The foundation: finished.**
   - `Heathcote.py`, with its logs and crash file
   - speech through your screen reader, and a timer loop that can pause
   - the settings and key bindings, every key rebindable with F1
   - the four volumes
   - the spoken menus, opening for now on a stand-in main menu with Settings and Quit
   - 65 silent tests
3. **The audio:** reviewed, and next to be built. All sound plays through FMOD, the engine
   the original used, so fast-forward keeps voices at their pitch and the backgrounds are
   muffled as the original muffled them.
4. **The story engine:** the original's rules, the actions menu, and the keys during play.
5. **The menus:** the opening, the main menu, Settings, the pause menu, the end and the
   credits.
6. **Saving:** progress, Continue story and Restart story.
7. **Building and releasing.**

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

`vendor/nvda/nvdaControllerClient64.dll` ships with the repository, so NVDA speaks through
its own client.

## Running it

From the repository's folder:

    python Heathcote.py

For now it opens on a stand-in main menu, spoken through your screen reader:

- **Settings** has Back, Debug mode (from source only) and Key bindings.
- **Quit** closes the game.

Every menu moves with all four arrows, wrapping round at either end, with Home and End
for the first and last row, Enter to choose, and Escape to go back. Back is the first row
of every menu that has one. F1 opens the key bindings from anywhere.

The volume keys, each step 10 percent, each level spoken:

- Shift with Home and End: the master volume, from anywhere.
- Page Up and Page Down: the title volume wherever the title music plays, and the
  background volume during the story.
- Shift with Page Up and Page Down: the interface volume, during the story.

Everything the game keeps is in `%APPDATA%\Heathcote`:

- `config\settings.json` and `config\keys.json`: the settings and the key bindings, each
  written safely with a backup;
- `logs\log.txt`, with the run before as `log.old.txt`, and `logs\crash.txt` when an error
  stops the game, which is spoken too.

The options:

- `--debug`: debug mode for this run. From source, the Settings screen's Debug mode row
  turns it on for good, and the window's title says "Heathcote (debug)". Its keys, F2 to
  F4, come with the story engine.
- `--spiel LABEL`: start the story at any spiel by its label, in debug mode. The labels are
  the "Spiel:" headings of `analysis/script/Heathcote.txt`. It is checked now, and used once
  the story engine is built.
- `-v`: a more detailed log.
- `--exit-after SECONDS`: quit by itself.

## Tests

    python tests\suite.py

runs every test in `tests\case`, several at once, writing the results to `tests\results`.
Some files can be run by name, such as `python tests\suite.py keymap menus`, and any file
runs on its own too, such as `python tests\case\test_keymap.py`. The tests never speak,
never play a sound, never open a window, and never touch your save.

`tests\interact` holds tools to try the game by ear instead. `python
tests\interact\speech_check.py` tries the speech and the timer loop. Each tool keeps its
own save, so none changes your settings or keys.

## Layout

```
game/                    the original app bundle, reorganised (see below)
vendor/nvda/             NVDA's controller client, with its license
vendor/fmod/             FMOD's licence, and fmod.dll, which you copy in yourself
Heathcote.py             the entry script
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

- `game/data/text/system/Heathcote v1.01.bundle.json` is the story's master index: every
  record's label, and each kind's records.
- `game/data/text/story/` holds the story's records, one JSON file each, named by its id.
- `game/data/Audio/story/` holds the story's 220 recordings, one folder per kind, each
  under its English name. The original named them by id;
  `aidocks/general/project_audio_names.md` maps each name back.
- `game/data/Audio/System/` holds the 14 interface sounds, in `menu/` and `misc/`.
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
