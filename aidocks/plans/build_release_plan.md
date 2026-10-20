---
name: build_release_plan
description: "Plan 7: compiler.py builds Heathcote.exe with PyInstaller, carrying the audio, the story data, FMOD and the NVDA client; releaser.py versions, files the changelog, zips and publishes a release from the dev's own machine. Windows only, no downloads, no workflow."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, with every question answered (2026-10-19). Waiting for the go-ahead to build.

Plan 7, the last ([[reading_original_plan]] lists the order). It packages what plans 2 to 6 build.

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
