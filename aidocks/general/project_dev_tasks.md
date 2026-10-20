---
name: project_dev_tasks
description: "The developer tasks (repository, tools, tests, build and docs), open and finished, kept out of docks/todo list.txt, which is for players only."
metadata:
  node_type: memory
  type: project
---

The developer tasks, which `docks/todo list.txt` leaves out because it ships to players ([[feedback_todo_list_format]]). Same style: newest at the top, one or two short sentences each. An item moves to Finished only when the dev confirms it.

## Unfinished

- `docks/readme.txt` needed the keys and how to use the F1 screen (Enter rebinds, A adds a key, Delete unbinds, R twice resets), since the screen does not explain itself each time. It was written on 2026-10-19, when the dev asked for every doc to be brought up to date ("updating all docks where possible, including the player facing ones."), and waits for the dev's word.

## Finished

- The 220 story recordings, all MP3 after the dev's conversion, have their English names in six folders by kind under `game/data/Audio/story/`, committed one folder at a time, with the old ids in [[project_audio_names]] (2026-10-19).
- The dev's reorganization of `game/` into `game/data/`, `game/certificate/` and `game/scripts/` is committed as five pure renames, with no file changed (2026-10-19).
