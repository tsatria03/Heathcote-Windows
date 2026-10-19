---
name: project_dev_tasks
description: "The developer tasks (repository, tools, tests, build and docs), open and finished, kept out of docks/todo list.txt, which is for players only."
metadata:
  node_type: memory
  type: project
---

The developer tasks, which `docks/todo list.txt` leaves out because it ships to players ([[feedback_todo_list_format]]). Same style: newest at the top, one or two short sentences each. An item moves to Finished only when the dev confirms it.

## Unfinished

- Once the dev says the `.m4a` conversion is done, rename each story recording to its English name from its record's `original.name`, and sort them into the empty folders already made under `game/data/Audio/story/`: `spiels/`, `voice/`, `ambience/`, `idle/`, `music/` and `interface/`, one folder per bundle category. Drop the `?` from `what was the question?`. Commit one folder at a time, and write the old-to-new name list into a note (agreed 2026-10-19: "Yes. Let's do it that way. I'll convert the files, then you can create the folder stubs with no files in them untill I tell you I'm done.").

## Finished

- The dev's reorganization of `game/` into `game/data/`, `game/certificate/` and `game/scripts/` is committed as five pure renames, with no file changed (2026-10-19).
