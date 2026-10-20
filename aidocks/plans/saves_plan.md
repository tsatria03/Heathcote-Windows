---
name: saves_plan
description: "Plan 6: what the game remembers between runs, in %APPDATA%\\Heathcote: the story's progress (variables, heard spiels, action counts, where to continue, the lanes playing) and the settings, written safely as the original wrote every change."
metadata:
  node_type: memory
  type: project
---

**Status:** planned. Being written; open questions below are still being answered.

Plan 6 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]]'s paths and safe JSON files, and keeps what [[story_engine_plan]] and [[menus_plan]] hold in memory. What the original saved comes from [[project_original_behaviour]].

## What the original saved
- Five stores in the iOS settings, each change written at once under "<store>/<name>" (`-[Vars applySetForVar:val:]`, 0x100030a34):
  - **story:** every story variable, as text.
  - **heard:** whether each spiel has been heard.
  - **actioned:** how many times each action has been chosen.
  - **teller:** whether the story has started, the spiel to continue from, and the four background lanes playing when that spiel opened (`opening-bgm` and `opening-ambience1` to `3`), plus the tutorial's flags and counts.
  - **config:** four developer switches, all off.
- **Continue replays the last spiel an action opened, from its beginning,** with its lanes as they were when it opened (`+[Story startTape]`, 0x10001a898; `+[StoryView newTape:]`, 0x100024020). A spiel reached through next is never the resume point.
- Restart reset story, heard and actioned, and left the rest.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. The progress file and the settings file, read on start and written safely.
2. Continue story, Restart story and the end's reset, using them.

## Decided

- **Everything is kept in `%APPDATA%\Heathcote`**, or `HEATHCOTE_USER_DIR` when set ([[foundation_plan]]):
  - `saves\progress.json`: the story's variables, the heard spiels, the actions' counts, whether the story has started, where to continue, and the lanes playing there.
  - `config\settings.json`: the three volumes, debug mode, and whether the first-run notice has been shown.
  - `config\keys.json`: the key bindings ([[foundation_plan]]).
- **Every file is written safely,** a temporary file first, then a `.bak` of the old one, then a swap; a damaged file is kept as `.damaged` and the backup read instead ([[foundation_plan]]).
- **Saved by softRef id, not by label,** since the ids never change while a label could be shared or edited.
- **Restart story and the end reset** the variables, the heard spiels and the actions' counts, and go back to `start`, leaving the settings and the first-run notice alone, as the original did.
- **No import of a save from the original app.**
- **Tests use a throwaway save folder** and never touch the real one ([[feedback_dont_run_or_build]]).

## Open questions
1. Where does Continue story pick up after the game has been closed? Proposed: as the original, the start of the spiel the last chosen action opened, with its lanes as they were. The alternative is the exact second the story was left, which the original never saved.
2. When is progress written? Proposed: as the original, at every change: each timed set, each choice and each heard spiel, so closing the window at any moment loses nothing.
