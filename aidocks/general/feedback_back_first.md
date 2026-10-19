---
name: feedback_back_first
description: "Every menu with a way back has a Back row, always the first row and the one it opens on, before anything else, Settings and the volume levels included."
metadata:
  node_type: memory
  type: feedback
---

Every menu that can be left by going back has a **Back** row, and it is **always the first row**. Anything else that should come first comes straight after it.

**Why:** The dev's standing rule, adopted for this project on 2026-10-19: "The back button should always appear first in any menu, including settings."

**How to apply:**
- It holds for screens not built on the shared menu code too, such as an F1 key bindings screen: Back is its first row and it opens on it, with Enter there going back as Escape does.
- The menu opens on Back, never on another row, even where landing on the current choice would save a key press. A volume's levels open on Back, not on the level it is at.
- Menus whose first row is already their way back keep it: the main menu (Quit), the pause menu (Resume), a yes-or-no question (No) and a headphones notice (Continue).
