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
- **`vendor/fmod/fmod.dll` is gitignored** (the dev, 2026-10-19: "I change my mind about the fmod dll. I want it git ignored so I can give this game release out to people."). It stays on the dev's machine for builds and ships only inside the built game; `license.txt` stays tracked. It was committed once, in 6ef2d33, before the dev changed their mind, and stays in the history: the dev, 2026-10-19: "As for the dll, you can leave that be. I do not want a history rewrite." The repo is private and will stay so ("I'm not planning to make this repository public. RIght now it's private, and will remain there.").
- **A fresh clone has no `fmod.dll`.** Install FMOD Engine 2.02.35 and copy `api\core\lib\x64\fmod.dll` into `vendor/fmod/`. The game says so plainly if the file is missing, rather than crashing.
- **The binding:** `pyfmodex` 0.7.2 (MIT, March 2024). It ships no DLL. It loads the file named by `PYFMODEX_DLL_PATH` if that is set before the import, so the game sets it to `vendor/fmod/fmod.dll` (or the build's copy) first. Which FMOD version pyfmodex was built against is not stated anywhere; 2.02 was chosen as the line current during its releases.
- **The licence** (`vendor/fmod/license.txt`, last updated 17 June 2024):
  - Free for personal, educational or non-commercial use, with no "monetisation, sponsorship or promotion" (clause 1.2).
  - The engine may be passed on only inside the game, never on its own or as part of an engine or tool set.
  - **The game must show a credit line containing "FMOD" and "Firelight Technologies Pty Ltd."** (clause 3; examples at www.fmod.com/attribution). It goes into the credits ([[project_later_topics]]).
  - `license.txt` ships beside the game, since it carries the Ogg Vorbis notice that must go with the binaries.
- **Tests stay silent** by starting FMOD with its no-sound output, so nothing is heard and no device is opened ([[feedback_dont_run_or_build]]).
- A build carries `fmod.dll` and `license.txt`, the way it carries the NVDA client.
