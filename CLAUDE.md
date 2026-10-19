# CLAUDE.md

This file guides Claude Code when it works in this repository. **It is a lean dispatcher.** It says what the project is and how it is laid out, then points to focused memory files (`[[name]]`) for the detail. When you start work in an area, read its linked memory first.

**Memory location:** all memory files (the `[[name]]` links and the `MEMORY.md` index) live in the repo's **`aidocks/`** folder, in two folders. **`aidocks/plans/`** holds every plan, planned or complete, as `aidocks/plans/<name>_plan.md` with no `project_` prefix; a finished plan stays there, marked finished. **`aidocks/general/`** holds every other note, as `aidocks/general/<name>.md`. A `[[name]]` link resolves to whichever of the two holds it ([[feedback_completed_projects]]). Read memory from there and write new or updated memory there, never to the `~/.claude` memory store. `aidocks/general/MEMORY.md` is the index, so add a one-line pointer there for every new memory. Keep this file under 40,000 characters and move detail into memory ([[feedback_memory_in_aidocks]]).

## What this is

A Windows port of **Heathcote** (`com.fabulaeobscurae.heathcote` 1.01, Fabulae Obscurae), an iOS interactive audio adventure "told through sound". The player follows a presenter exploring an abandoned asylum while on the phone to his producer, choosing what he does next from an actions menu. The original was played by swipes; the port is for the keyboard and screen readers.

- **A solo project.** tsatria03 makes it alone ([[project_solo]]).
- **Windows only** ([[project_windows_only]]).
- **Python only**, with pygame, Prism and the NVDA client ([[project_python_only]]).
- **No downloads.** Every recording ships with the game ([[project_no_downloads]]).
- **Developer tasks**, open and finished, are in [[project_dev_tasks]].
- **The game is data-driven.** The story is JSON exported from the original's authoring tool: choices with conditions, recordings ("spiels") that set variables at timed points and chain on, and ambience and music lanes with timed fades. What the data, the binary and the original's behaviour say is in [[project_original_findings]].
- **Status:** the original has been surveyed. The first plan, reading the original, is being written ([[reading_original_plan]]).

## Layout

- **`game/`**: the original app bundle, reorganized by the dev, and never written to by Claude. The layout is in [[project_original_findings]]. The story records are in `game/data/text/story/`, with the master index `game/data/text/system/Heathcote v1.01.bundle.json`. The recordings are in `game/data/Audio/story/`, each named by its id plus an extension for its format; the story data names them by the bare id. Don't move, rename, convert or delete sound files unless the dev asks.
- **`heathcote/`**: the port's Python package, empty for now.
- **`tests/interact/`**: tools played by ear, not tests, run by the dev. A tool for testing goes here, never into the game's menus ([[feedback_test_tools_in_interact]]).
- **`tests/case/`**: silent test scripts, to come; results go in the gitignored `tests/results/`. Run only the files covering what changed, in the background, and the full suite only when the dev asks ([[feedback_dont_run_or_build]]).
- **`vendor/nvda/`**: `nvdaControllerClient64.dll` (x64) and its license.
- **`docks/`**: the documents a player reads: `readme.txt`, `changelog.txt` and `todo list.txt` ([[feedback_changelog]], [[feedback_todo_list_format]]).
- **`analysis/`**: data exported from the original for reference, to come.
- **`tools/`**: scripts for reading the original, to come.
- **`build/`** and **`dist/`**: build output, gitignored.
- **`user/`** is gitignored private reference material. Read it, but never edit it. Never name the dev's other games kept in it, in any of this repo's files ([[feedback_no_other_games]]).
- **`New File*.txt`** at the root is the dev's private scratchpad. It is gitignored; never read, edit, flag or delete it.

## Working here

- **The dev runs and builds, not Claude.** Ask before running the game or anything that plays sound or speaks ([[feedback_dont_run_or_build]]).
- **Plans first:** an agreed plan goes into its own note in `aidocks/plans/` before any code, and is marked finished only once the dev says it works ([[feedback_record_plans_first]], [[feedback_completed_projects]]).
- **Committing and pushing:** commit finished work without asking; ask about pushing only once 10 or more commits are unpushed; "commit/push" means both; history rewrites need a go-ahead ([[feedback_git_commits]]). Name people by GitHub username only ([[feedback_use_github_usernames]]).
- **Questions:** a question from the dev is a check, answered in chat ([[feedback_questions_are_checks]]). Ask one question per reply, in plain text ([[feedback_one_question_at_a_time]], [[feedback_no_question_pickers]]).
- **Releases** are never recorded in notes or the README ([[feedback_no_release_records]]).
- **Menus:** Back is always the first row ([[feedback_back_first]]).
- **Who you're working with:** [[user_screen_reader]]. The dev uses NVDA, so prefer lists and short lines, never wide tables, and never make noise from tools.

`CLAUDE.md` and `aidocks/` are committed, not gitignored.
