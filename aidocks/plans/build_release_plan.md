---
name: build_release_plan
description: "Plan 7: compiler.py builds Heathcote.exe with PyInstaller, carrying the audio, the story data, FMOD and the NVDA client; releaser.py versions, files the changelog, zips and publishes a release from the dev's own machine. Windows only, no downloads, no workflow."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, with every question answered (2026-10-19). It needs no section review, having nothing to test by ear (the dev, 2026-10-21: "for plan 7, no section review is required, as there are no actual hering tests for it."). Being built from 2026-10-21, on the dev's word ("For plan 7, make the compiler script first."); section 1, `compiler.py`, is finished; section 2, `releaser.py`, is built; and section 3, the story pack, asked for after it, is built and waiting for the dev's builds.

Plan 7, the last ([[reading_original_plan]] lists the order). It packages what plans 2 to 6 build.

## What plan 3 built for it

The audio plan, finished 2026-10-20 ([[audio_plan]]), means a build must carry:
- `vendor\fmod\fmod.dll` and `license.txt`, which `heathcote/paths.py` looks for under the build's `vendor\fmod\`
- the `pyfmodex` package, from `requirements.txt`

Without the DLL, the game stops with a message saying where to copy it from, so `compiler.py --test` will show a missing DLL at once.

## What plans 4 to 6 built for it

The story engine, the menus and the saves, finished 2026-10-20 and 21 ([[story_engine_plan]], [[menus_plan]], [[saves_plan]]), add nothing a build must carry beyond `game/documents/`, and leave these for `--test` to rely on:
- **The game opens on its opening,** the police radio, and with `--exit-after` closes on its own; the log's "game data:" line and "progress: no story is under way" show a build found its data and its save on a fresh throwaway save.
- **Everything the game writes** is in the save folder: `config\settings.json`, `config\keys.json`, `saves\progress.json` and `logs\`, each under `HEATHCOTE_USER_DIR` when set, so `--test` never touches the dev's own save.
- **The by-ear tools in `tests/interact/`** are for the repository, never the build.

## What section 1 built

Built 2026-10-21, adapted from the reference material's compiler without naming it ([[feedback_no_other_games]]):
- **`compiler.py`** at the root, with the numbered menu and the same command lines: the folder build, `--embed`, `--test`, `--clean`, `--console`, `--onefile`, `--no-game` and `--dry-run`.
- **What it carries:** `vendor/nvda/nvdaControllerClient64.dll` and `vendor/fmod/fmod.dll` as binaries into the same folders inside the build, which `heathcote/paths.py` finds under `sys._MEIPASS`; Prism with `--collect-all` and its `_native` module; pyfmodex with `--collect-submodules`, since `platform/audio.py` imports it only once the DLL is found; and `game/documents/Audio` and `game/documents/text` whole, 830 files and 159 MB on 2026-10-21, beside the exe or inside it with `--embed`.
- **The licences,** 18 files in `licenses\`: FMOD's and the NVDA client's from `vendor\`, Prism's and cffi's from their dist-info `licenses\` folders, pyfmodex's from the `LICENSE` at the top of its dist-info, and pygame's LGPL.
- **A missing `fmod.dll`** stops the build with where to get it.
- **`--test`** runs the build on a throwaway save with `HEATHCOTE_SILENT`, `HEATHCOTE_NOSOUND` and SDL's dummy drivers for 6 seconds, within 180, and needs the log's "game data:" line, an "FMOD" line, "Heathcote closed", no `crash.txt` and exit code 0.
- **Checked without building:** `--dry-run --test` lists the command and everything above, with the changelog's `unrelease:` warning. `tests/case/test_compiler.py` has nine tests; 191 in all. Claude never builds; the dev runs the first build.
- **The menu** says itself again on Enter with nothing typed (the dev, 2026-10-21: "Please make it so pressing enter repeats the menu if you do not type a number").
- **The dev's builds passed `--test`,** both kinds, 2026-10-21: the single exe, menu choice 4 ("The compiler tests past."), 159 MB with `fmod.dll` inside it and none loose beside it, and the folder build, choice 2 ("Option 2 also past as well."). **Section 1 is finished.**
- **Found on the way:** the README's counts were stale. The folders hold 206 story recordings and 16 interface sounds, and `tools/story.py` finds every recording the story names.

## What section 2 built

Built 2026-10-21, adapted from the reference material's releaser without naming it:
- **`releaser.py`** at the root, with a numbered menu of the full release and its seven steps, each asking Y or N: check, prepare, build, zip, commit, tag and upload. The reference's separate upload of a recordings pack is left out, since every recording ships in the zip ([[project_no_downloads]]).
- **The check** adds Heathcote's own changelog rule: every entry under `unrelease:` must end in a full stop, a full stop inside a closing quote counting ([[feedback_changelog]]). With 1 to 4 entries it asks whether to release anyway, only when nothing else is in the way.
- **The zip** stores the MP3s as they are, since they barely shrink, and compresses the rest; it is written as `.part` and renamed once whole, and holds one `Heathcote-Windows` folder.
- **Enter with nothing typed** says its menu again, and the build choice's too, as the compiler's does.
- **Checked without releasing:** `tests/case/test_releaser.py` has nine tests, one of them checking the changelog as it is now. Step 2 alone was run against the real repository on 2026-10-21: it found the GitHub CLI signed in and 34 changes waiting, all with full stops. 201 tests in all. Claude never releases; the dev runs it.

## Section 3, the story pack

**Built 2026-10-21, waiting for the dev's builds:**
- **`heathcote/platform/pack.py`** holds the format as below, with a random 256-bit key, `write_pack()`, `Pack` and `fingerprint()`. `PREFIX`, `story.dat:`, names a packed recording where a path would be, such as `story.dat:scene/start.mp3`.
- **`StoryData`** opens `paths.story_pack()` when `game/documents/Audio/story/` is not there (`open_pack()`), checks its size against `game\story_pack.json` when a build carries one, and gives packed paths for the story's categories; the interface sounds stay files. It logs "story recordings: <path>". A missing pack, a damaged one or one of the wrong size stops the game with a message saying to extract the whole folder again.
- **`Audio.source()`** turns a packed path into its decrypted bytes and a `CREATESOUNDEXINFO` with their length, and `Slot.play()` opens them with `OPENMEMORY`, as a sample or a looping stream, so the spiel, the lanes and the title music all play from memory.
- **`compiler.py`** makes `story.dat` into `build\stage\` before PyInstaller runs, reads every recording back, writes `story_pack.json` into the build's `game\` (staged for `--embed`), leaves `Audio/story` out of `game\`, and moves `story.dat` beside the exe. `--test` also needs "story recordings: …story.dat" in the log. A dry run of the single exe on 2026-10-21: 624 files and 1 MB inside the exe, and 206 recordings, 158 MB, into `story.dat`.
- **`tools/build_pack.py`** makes `dist\story.dat` on its own, in about 3 seconds, every recording read back.
- **`releaser.py`** stores `.dat` files in the zip, as it stores MP3s.
- **`cryptography`** is in `requirements.txt`, named outright to PyInstaller, its three licence files in `licenses\`, 21 in all.
- **Tests:** `tests/case/test_pack.py`, eight, including FMOD playing a packed recording as a sample, as a stream and as the spiel, and StoryData playing from a pack with the story folder absent; two more in the compiler's and the releaser's. 210 in all.
- **The dev's tests,** to come:
  1. Mandatory: build the single exe with `--test`, choice 4; it passes, and `story.dat` sits beside a much smaller `Heathcote.exe`. **Passed** (the dev, 2026-10-21: "test 1 past."): `Heathcote.exe` 21.7 MB and `story.dat` 150.8 MB beside it.
  2. Mandatory: play a little of the built game: the opening, the title music, the start of the story and a choice, sounding as from source.
     - **First try, 2026-10-21: it failed.** The dev: "when it goes to the main menu, it quits after a few seconds. No title music plays." The log stopped at "opened main menu", with no crash file. Reproduced silently from source with the build's `story.dat`: a Windows access violation on FMOD's stream thread. FMOD streams a sound opened with `OPENMEMORY` straight from the bytes it is given, but `Slot.play()` let Python free them once the sound was made. Short sounds survived, being decoded at once, so the title music, the first long stream, was the first to crash. The pack's test had passed by luck, ending before the memory was reused.
     - **The fix:** `Slot.memory` keeps a packed recording's bytes while its sound lives; a fading-out sound carries them in `fading_out` until `_free()` releases it; `_release()` drops them only after the sound is released. A new test plays a packed stream for 2 seconds after a garbage collection. The silent reproduction then ran the title music and 30 seconds of the story cleanly.
  3. Optional: the folder build with `--test`, choice 2.
  4. Optional: move `story.dat` away from a build and start it: the game says the recordings were not found.

**The plan as agreed:**

Asked for by the dev, 2026-10-21: "Can you please bring the pack encription feature from the other port into this game? ... I wanted the sounds found in the audio/story folder to be packed into story.dat. The entire story folder. Everything else can be embedded as normal. The story.dat file will be located outside the game folder when compiled. I chose this option because I did not want the exe file to be too big if embedded." Adapted from the reference material's pack, never naming it ([[feedback_no_other_games]]).

- **`heathcote/game/pack.py`:** the format and its reader and writer.
  - The file is a magic `HEATHPK1`, the index's length, the index, then each recording.
  - Everything is encrypted with AES-256-GCM, through the `cryptography` package: the index, and each recording on its own, with a fresh nonce each and its own name as associated data, so one part cannot pass for another.
  - The index maps each recording's path inside `game/documents/Audio/story/`, such as `scene/start.mp3`, to its place.
  - No compression, since MP3s barely shrink.
  - The key ships inside the game, so this keeps out casual copying, not a determined person, as the reference's notes say too.
- **Every file of `game/documents/Audio/story/` goes in,** 206 recordings, about 150 MB. The interface sounds in `Audio/System/` and the story's text stay as they are, embedded as normal.
- **Playing from it:** the game reads one recording at a time, decrypts it in memory, and hands the bytes to FMOD with `OPENMEMORY`, which copies them. Nothing decrypted is ever written to disk. `StoryData` names a packed recording by its path in the pack, so the lanes, the spiel and the rewind work as now.
- **Where the game looks:**
  - From source, the loose `Audio/story/` folder wins.
  - Without it, `dist\story.dat` from source, or `story.dat` beside `Heathcote.exe` in a build.
  - A build with no `story.dat`, or a damaged one, stops with a spoken message and `crash.txt`, saying what is missing.
- **`compiler.py` makes the pack** as part of each build, into the build's folder beside the exe, and checks every recording reads back. It leaves `Audio/story/` out of the build's `game\`. The repository is never changed. The fingerprint, the pack's size and SHA-256, goes inside the build, so a `story.dat` from another build is caught at once.
- **`tools/build_pack.py`** makes `dist\story.dat` on its own, for a source run without the loose folder.
- **`--test`** also needs the log to say the story's recordings came from `story.dat`.
- **The release zip** carries `story.dat` beside the exe, stored, not compressed, so nothing is downloaded ([[project_no_downloads]]).
- **`requirements.txt`** gains `cryptography`; its licence goes into `licenses\`, and the compiler names its cipher module outright.
- **Tests** for the format, damaged and foreign packs, reading from memory, the fallback order, the compiler leaving the folder out, and the zip.
- **Nothing to test by ear beyond a build:** the dev builds with `--test` and plays a little of the built game, the story sounding as it does from source.
- **Where `story.dat` sits in a build:** beside `Heathcote.exe`, inside the release zip (the dev, 2026-10-21: "That's exactly what I mean.").

## Built in sections

Each section is confirmed by the dev before the next starts.
1. `compiler.py`, the build, with its silent test.
2. `releaser.py`, the release.

## Decided

- **Windows only,** with no GitHub Actions workflow and no Linux or macOS parts ([[project_windows_only]]).
- **No downloads** ([[project_no_downloads]]): every recording ships inside the game, so there is no pack, no pack builder and no release step that uploads one. The audio is about 152 MB, so the zip is about that size.
- **Two scripts at the repo's root, adapted from the reference material in the gitignored `user/` folder,** never naming where they came from ([[feedback_no_other_games]]):
  - `compiler.py` builds the game with PyInstaller into `dist\Heathcote-Windows\`, around `Heathcote.exe`. It only builds: it never zips and never changes the repository. Run with no options, it shows a numbered menu, each choice one command line.
  - `releaser.py` makes a release on the dev's own machine, asking Y or N before each step: check the changelog and the repo, set `VERSION` to today's date and that day's number (such as `26.10.19-1`), file the changelog's `unrelease:` lines under it, build with the compiler, zip the build, commit "Release <version>", tag `V<version>`, and upload the zip with `gh`. A failed build puts `VERSION` and the changelog back. It never moves or replaces a tag, a release, or a file already on one.
- **What a build carries:**
  - From `game/`, only what the game reads: `game/documents/Audio/` and `game/documents/text/`. Not the binary, the images, the certificates, the stray source files or the rest of the iOS bundle.
  - `vendor/fmod/fmod.dll` and `vendor/nvda/nvdaControllerClient64.dll`, with Prism's own native part. `fmod.dll` is gitignored ([[project_fmod]]), so the compiler stops with a plain message if it is missing from `vendor/fmod/`.
  - Beside the exe: `docks\` (the readme, changelog and todo list, the changelog without an empty `unrelease:`), `VERSION` and the port's licence as `license.txt`.
  - The third-party licences, as `licenses\`: FMOD's (`vendor/fmod/license.txt`, which carries the Ogg Vorbis notice that must go with the binaries, [[project_fmod]]), the NVDA client's, Prism's, pygame's and pyfmodex's.
- **`compiler.py --test` starts a finished build silently** for a few seconds with `--exit-after`, on a throwaway save, with speech off and FMOD's no-sound output, and reads its log ([[foundation_plan]]).
- **The changelog's release rules** (5 to 100 entries, never more than 100) are in [[feedback_changelog]]. Releases are never recorded in notes or the README ([[feedback_no_release_records]]).
- **Claude never builds or releases**; the dev runs both ([[feedback_dont_run_or_build]]).

- **Players download releases from this repo's GitHub releases page,** since the repo is public (the dev, 2026-10-19: "I'm going to make this reposiory public. ... The fmod dll can still be packaged with the game at build time."). The releaser uploads each zip there, with `fmod.dll` inside it.

- **Both kinds of build, chosen each time** (the dev, 2026-10-19: "I like being able to choose, so yes, both builds."): the folder build, the default, and the single exe, each one choice in `compiler.py`'s numbered menu and one command line. `--test` checks either.

## Open questions

None.
