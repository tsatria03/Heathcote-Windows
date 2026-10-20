# Memory index

## Project
- [Original findings](project_original_findings.md): the dev's layout of game/, what the iOS bundle contains, the JSON script grammar, the runtime read from the binary, and what to drop.
- [Original behaviour](project_original_behaviour.md): how the original plays, read from the binary: story rules, sound channels, rewind and fast-forward, lockout, the actions menu, gestures, reminders, title flow and saving, each with its address.
- [Audio names](project_audio_names.md): every story recording's English name and folder, mapped back to the id the data names it by.
- [No downloads](project_no_downloads.md): every recording ships with the game; no pack, download screen or release asset.
- [Python only](project_python_only.md): pygame for the window and keys, FMOD for sound, Prism and the NVDA client for speech; the dev converts audio, Claude never does.
- [FMOD](project_fmod.md): FMOD Engine 2.02.35 through pyfmodex for all sound; vendor/fmod/, committed as the repo is private; a credit line is required.
- [Windows only](project_windows_only.md): no Linux, macOS or GitHub Actions workflow.
- [Solo project](project_solo.md): tsatria03 alone; credits name Fabulae Obscurae for the original.
- [Later topics](project_later_topics.md): ideas and requirements for plans not yet written, such as FMOD's credit line.
- [Developer tasks](project_dev_tasks.md): repository, tools, tests, build and docs tasks, kept out of the player todo list.

## Plans
- [Foundation](../plans/foundation_plan.md): plan 2, planned, all questions answered. The package, entry script, paths, logs, speech, timers, settings, keys, the F1 screen and the spoken menu.
- [Audio](../plans/audio_plan.md): plan 3, planned, all questions answered.
- [Story engine](../plans/story_engine_plan.md): plan 4, being written. The variables, timed sets, next, idle loops, lockout, the actions menu, the end, the keys during play and debug mode. The spiel, the four background lanes and their crossfades, the idle loop, system sounds, rewind, fast-forward, the hush and the volumes.

## Completed projects
- [Reading the original](../plans/reading_original_plan.md): plan 1, FINISHED 2026-10-19. tools/macho64.py, dis64.py, story.py and script_text.py; analysis/script/Heathcote.txt; and [Original behaviour](project_original_behaviour.md).

## Feedback
- [Memory in aidocks](feedback_memory_in_aidocks.md): all memory lives in aidocks/, general/ for notes and plans/ for plans.
- [Plans first](feedback_record_plans_first.md): an agreed plan gets its own note, committed first; finished only on the dev's word.
- [Completed projects](feedback_completed_projects.md): a finished plan stays in plans/; only its index line moves.
- [Don't run or build](feedback_dont_run_or_build.md): never build unless told; ask before running anything that plays sound or speaks.
- [Git commits](feedback_git_commits.md): one commit per change, commit without asking, raise pushing at 10 or more; git commit -F from PowerShell.
- [GitHub usernames](feedback_use_github_usernames.md): tsatria03 and the noreply address, never real names.
- [No other games](feedback_no_other_games.md): never name the game in user/ anywhere in this repo.
- [Questions are checks](feedback_questions_are_checks.md): a question from the dev is answered in chat, with no edits.
- [One question at a time](feedback_one_question_at_a_time.md): one question per reply, with a recommendation.
- [No question pickers](feedback_no_question_pickers.md): ask in plain text, never through the picker tool.
- [No release records](feedback_no_release_records.md): never record individual releases in notes or the README.
- [Changelog](feedback_changelog.md): the unrelease: block, newest first, one plain sentence per line ending in a period.
- [Todo list format](feedback_todo_list_format.md): ##Unfinished. and ##Finished., players only, bugs stated as what happens.
- [Back first](feedback_back_first.md): Back is the first row of every menu with a way back, and it opens on it.
- [Test tools in interact](feedback_test_tools_in_interact.md): by-ear tools go in tests/interact/, never in the game's menus.

## User
- [Screen reader](user_screen_reader.md): the dev uses NVDA; headings, lists and short lines, no wide tables, no noise from tools.
