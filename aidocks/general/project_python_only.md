---
name: project_python_only
description: "The port is written entirely in Python, with pygame for the window, keyboard and frame loop, FMOD through pyfmodex for all sound, and the NVDA client or Prism for speech. The dev converts audio to MP3; Claude never runs a conversion."
metadata:
  node_type: memory
  type: project
---

The port is written entirely in Python:
- pygame (not pygame-ce) for the window, the keyboard and the frame loop; it plays no sound
- FMOD Engine through `pyfmodex` for all sound ([[project_fmod]])
- `prismatoid` (Prism) for speech through any screen reader or a Windows voice
- NVDA's own controller client, `vendor/nvda/nvdaControllerClient64.dll`, through ctypes

Don't propose moving parts to another language or engine.

**Why:** On 2026-10-19 the dev agreed to adopt the reference repo's working rules, which use pygame and Prism, and then chose FMOD for the sound ("Yes please."), the engine the original itself used. `vendor/nvda/` already holds the NVDA client.

**Audio formats:**
- Every recording is MP3, converted by the dev on their own machine on 2026-10-19, the WAV and `.m4a` files included ([[project_original_findings]]). Claude never runs a conversion.
- FMOD could play the WAV and AAC files too, but the MP3s are what is on disk.

**How to apply:**
- Write any new code in Python, inside the port's package.
- No OpenAL binding. Sound goes through FMOD only.
- Don't move, rename, convert or delete sound files unless the dev asks.
