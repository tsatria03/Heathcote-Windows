---
name: project_python_only
description: "The port is written entirely in Python, with pygame for the window, keyboard and audio, and the NVDA client or Prism for speech. The dev converts any .m4a to MP3; Claude never runs a conversion."
metadata:
  node_type: memory
  type: project
---

The port is written entirely in Python:
- pygame (not pygame-ce) for the window, the keyboard, the frame loop and the audio
- `prismatoid` (Prism) for speech through any screen reader or a Windows voice
- NVDA's own controller client, `vendor/nvda/nvdaControllerClient64.dll`, through ctypes

Don't propose moving parts to another language or engine.

**Why:** On 2026-10-19 the dev agreed to adopt the reference repo's working rules, which use this stack. `vendor/nvda/` already holds the NVDA client.

**Audio formats:**
- Every recording is MP3, converted by the dev on their own machine on 2026-10-19, the WAV and `.m4a` files included ([[project_original_findings]]). Claude never runs a conversion.
- pygame's mixer cannot decode AAC in `.m4a` files, which is why they were converted.

**How to apply:**
- Write any new code in Python, inside the port's package.
- No OpenAL binding, as in the reference rules, unless the dev decides otherwise.
- Don't move, rename, convert or delete sound files unless the dev asks.
