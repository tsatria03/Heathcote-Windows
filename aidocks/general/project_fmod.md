---
name: project_fmod
description: "Heathcote plays its sound through FMOD Engine 2.02.35, the original's own audio engine, via pyfmodex; the DLL is in vendor/fmod/ but gitignored, shipping only in the built game, and the licence needs a credit line in the game."
metadata:
  node_type: memory
  type: project
---

**The game plays all its sound through FMOD**, the audio engine the original used (FMOD 1.7 there), through the Python binding `pyfmodex`. pygame still runs the window, the keyboard and the frame loop, but plays nothing ([[project_python_only]]).

**Why:** pygame's mixer cannot change a recording's speed or filter it live, so it could only approximate the original's 1.75 times fast-forward and its 1250 Hz muffle. FMOD does both, and its fade points match the original's crossfades. The dev asked, 2026-10-19: "does python have an fmod module?", then, asked whether to switch: "Yes please."

**How to apply:**
- **The engine:** FMOD Engine 2.02.35 for Windows, from `fmodstudioapi20235win-installer.exe` (not the UWP one), 64-bit. The dev installed it at `C:\Program Files (x86)\FMOD SoundSystem\FMOD Studio API Windows\`.
- **`vendor/fmod/`** holds `fmod.dll` (from `api\core\lib\x64\`, version 2.2.35, build 164197, checked to be x64) and `license.txt` (from `doc\LICENSE.TXT`). Never `fmodL.dll`, the logging build, and nothing else from the install: the licence lets only the run-time libraries be passed on.
- **`vendor/fmod/fmod.dll` is gitignored** (the dev, 2026-10-19: "I change my mind about the fmod dll. I want it git ignored so I can give this game release out to people."). It stays on the dev's machine for builds and ships only inside the built game; `license.txt` stays tracked. It was committed once before the dev changed their mind, and was then **removed from the whole history** of `main` on 2026-10-19, before any push, since FMOD's licence allows passing it on only inside the game (the dev: "Is it possible to rewrite the history since the fmod dev does not want the dll in the repo?", then "Yes, create a backup branch first."). That reversed the dev's earlier "I do not want a history rewrite." The commit that added `vendor/fmod/` is now 95b5431, holding only `license.txt`, though its message still describes the DLL. The old history was kept on a local branch, `backup/before-fmod-rewrite`, until the dev had it deleted the same day ("Also delete the backup branch if you didn't already do so."), so no branch holds the DLL ([[feedback_git_commits]]).
- **The repo is going public** (the dev, 2026-10-19: "I'm going to make this reposiory public. ... The fmod dll can still be packaged with the game at build time."). Earlier the same day the dev had said it would stay private; that no longer holds. The DLL is still packaged into every build from the dev's own `vendor/fmod/`.
- **A fresh clone has no `fmod.dll`.** Install FMOD Engine 2.02.35 and copy `api\core\lib\x64\fmod.dll` into `vendor/fmod/`. The game says so plainly if the file is missing, rather than crashing.
- **The binding:** `pyfmodex` 0.7.2 (MIT, March 2024). It ships no DLL. It loads the file named by `PYFMODEX_DLL_PATH` if that is set before the import, so the game sets it to `vendor/fmod/fmod.dll` (or the build's copy) first. Which FMOD version pyfmodex was built against is not stated anywhere; 2.02 was chosen as the line current during its releases. **Checked on 2026-10-19:** pyfmodex 0.7.2, installed with `pip install pyfmodex==0.7.2` for Python 3.12, drives the 2.02.35 DLL. With the no-sound output it reported the version, streamed `Title.mp3` and read its length, changed a channel's frequency, attached the pitch shift effect, made a channel group, and closed cleanly.
- **The licence** (`vendor/fmod/license.txt`, last updated 17 June 2024):
  - Free for personal, educational or non-commercial use, with no "monetisation, sponsorship or promotion" (clause 1.2).
  - The engine may be passed on only inside the game, never on its own or as part of an engine or tool set.
  - **The game must show a credit line containing "FMOD" and "Firelight Technologies Pty Ltd."** (clause 3; examples at www.fmod.com/attribution). It goes into the credits ([[project_later_topics]]).
  - `license.txt` ships beside the game, since it carries the Ogg Vorbis notice that must go with the binaries.
- **pyfmodex's quirks with FMOD 2.02,** found building plan 3 on 2026-10-20:
  - New sounds default to 3D, so the game passes `MODE.TWOD`.
  - Its enum puts the pitch shift's "Max channels" at 4, but the DLL has it at 3. And every pitch shift setting is a float in 2.02, so setting the channel count as an int is refused (`UNSUPPORTED`). The game finds effect settings by name and sets them as floats.
  - `get_parameter_float()` returns a pair: the value, then its text.
- **Tests stay silent** by starting FMOD with its no-sound output, so nothing is heard and no device is opened ([[feedback_dont_run_or_build]]).
- A build carries `fmod.dll` and `license.txt`, the way it carries the NVDA client.
