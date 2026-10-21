---
name: build_release_plan
description: "Plan 7: compiler.py builds Heathcote.exe with PyInstaller, carrying the audio, the story data, FMOD and the NVDA client; releaser.py versions, files the changelog, zips and publishes a release from the dev's own machine. Windows only, no downloads, no workflow."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, with every question answered (2026-10-19). It needs no section review, having nothing to test by ear (the dev, 2026-10-21: "for plan 7, no section review is required, as there are no actual hering tests for it."). Being built from 2026-10-21, on the dev's word ("For plan 7, make the compiler script first."); section 1, `compiler.py`, is finished, and section 2, `releaser.py`, is being built.

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
