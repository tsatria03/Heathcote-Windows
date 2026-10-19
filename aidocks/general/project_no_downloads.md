---
name: project_no_downloads
description: "Heathcote needs no downloadable files: every recording ships with the game, so there is no pack, download screen or release asset."
metadata:
  node_type: memory
  type: project
---

**Heathcote needs no downloadable files to play.** Every recording is in the original bundle and ships with the game.

**Why:** The dev said on 2026-10-19: "unlike in the other refferenced game, this one does not require any downloadable files to play."

**How to apply:**
- No encrypted pack, no download screen, no pack builder, and no release step that uploads one.
- No `cryptography` dependency for that purpose.
- The player readme has no download section.
- The build carries the game's audio itself.
