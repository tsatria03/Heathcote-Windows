---
name: feedback_test_tools_in_interact
description: "A tool for trying something by ear, such as a spiel chooser, goes in tests/interact/ as its own script, never into the game's menus."
metadata:
  node_type: memory
  type: feedback
---

A tool the dev uses to try a feature by ear goes in `tests/interact/` as its own script, never into the game itself or its menus.

**Why:** The dev's standing rule, adopted for this project on 2026-10-19: "I wanted the chooser in tests/interact. Not in the main game."

**How to apply:** When the dev asks for a way to test or try something, make a `tests/interact/` script with its own save folder under `%APPDATA%\Heathcote`, so the game's volumes and keys are untouched. Leave the game's screens as their plans say ([[feedback_dont_run_or_build]]).
