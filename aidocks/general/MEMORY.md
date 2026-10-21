# Memory index

## Project
- [Original findings](project_original_findings.md): the dev's layout of game/, what the iOS bundle contains, the JSON script grammar, the runtime read from the binary, and what to drop.
- [Original behaviour](project_original_behaviour.md): how the original plays, read from the binary: story rules, sound channels, rewind and fast-forward, lockout, the actions menu, gestures, reminders, title flow and saving, each with its address.
- [Audio names](project_audio_names.md): every story recording's English name and folder, mapped back to the id the data names it by.
- [No downloads](project_no_downloads.md): every recording ships with the game; no pack, download screen or release asset.
- [Python only](project_python_only.md): pygame for the window and keys, FMOD for sound, Prism and the NVDA client for speech; the dev converts audio, Claude never does.
- [FMOD](project_fmod.md): FMOD Engine 2.02.35 through pyfmodex for all sound; vendor/fmod/fmod.dll gitignored, shipped only in the build; a credit line is required.
- [Windows only](project_windows_only.md): no Linux, macOS or GitHub Actions workflow.
- [Solo project](project_solo.md): tsatria03 alone; credits name Fabulae Obscurae for the original.
- [Later topics](project_later_topics.md): ideas and requirements for plans not yet written, such as FMOD's credit line.
- [Developer tasks](project_dev_tasks.md): repository, tools, tests, build and docs tasks, kept out of the player todo list.

## Plans
- [Choice text](../plans/choice_text_plan.md): plan 9, built, waiting for the dev's ear tests. In the actions menu, a choice's text is spoken after its clip, the first time only, and Space's choice_text action goes.

## Completed projects
- [Settings](../plans/settings_plan.md): plan 8, FINISHED 2026-10-21. A row for each of the four volumes, opening a list of levels, and Volume speed for the held volume keys; 218 silent tests.
- [Build and release](../plans/build_release_plan.md): plan 7, FINISHED 2026-10-21. compiler.py, a folder build or a single exe with a silent --test; releaser.py, the release from this machine with gh; the story's recordings in an encrypted data\story.dat beside the exe (platform/pack.py, AES-256-GCM, played from memory, its bytes kept while FMOD streams them); tools/build_pack.py; 212 silent tests.
- [Saves](../plans/saves_plan.md): plan 6, FINISHED 2026-10-21. progress.py, saves\progress.json with the spiel's snapshot and the chapter apart; Continue story from the save at the start of the spiel the player was in, after Return to menu or quitting; Restart story and the end clearing it; debug jumps writing nothing; Tab saying the chapter; menu_check.py's Control+D; 182 silent tests.
- [Menus](../plans/menus_plan.md): plan 5, FINISHED 2026-10-20. opening.py, the police radio and the first-run notice; the title music with the original's story fades; the main menu with Start story or Continue story, Settings, Credits and Quit; credits.py; the pause menu with Restart story and Return to menu (since plan 6, ending the story for Continue story from the save); the end credits over the story's last moments; menus_check.py, now menu_check.py; 166 silent tests.
- [Story engine](../plans/story_engine_plan.md): plan 4, FINISHED 2026-10-20. state.py, the variables, heard spiels and action counts; player.py, the original's rules; the story screen; lockout and the actions menu with its clips; the keys during play with a stand-in pause; debug mode's F2 to F4 and --spiel; story_check.py; 154 silent tests.
- [Audio](../plans/audio_plan.md): plan 3, FINISHED 2026-10-20. FMOD through pyfmodex; the original's channels; even 6 dB volume steps; the spiel with rewind and fast-forward at pitch; the hush and the original's pause; the four lanes with crossfades, rebuilt after a rewind; the idle loop; the story fades; audio_check.py; 101 silent tests.
- [Foundation](../plans/foundation_plan.md): plan 2, FINISHED 2026-10-19. Heathcote.py, paths, logs and crash file; speech and the timer loop; settings, the grouped key map, the screens, the spoken menu and the F1 screen; the four volumes; and 65 silent tests.
- [Reading the original](../plans/reading_original_plan.md): plan 1, FINISHED 2026-10-19. tools/macho64.py, dis64.py, story.py and script_text.py; analysis/script/Heathcote.txt; and [Original behaviour](project_original_behaviour.md).

## Feedback
- [Memory in aidocks](feedback_memory_in_aidocks.md): all memory lives in aidocks/, general/ for notes and plans/ for plans.
- [Plans first](feedback_record_plans_first.md): an agreed plan gets its own note, committed first; finished only on the dev's word.
- [Completed projects](feedback_completed_projects.md): a finished plan stays in plans/; only its index line moves.
- [Don't run or build](feedback_dont_run_or_build.md): never build unless told; ask before running anything that plays sound or speaks.
- [Git commits](feedback_git_commits.md): one commit per change, commit without asking, push only when a plan is finished and its docs updated; git commit -F from PowerShell.
- [GitHub usernames](feedback_use_github_usernames.md): tsatria03 and the noreply address, never real names.
- [No other games](feedback_no_other_games.md): never name the game in user/ anywhere in this repo.
- [Questions are checks](feedback_questions_are_checks.md): a question from the dev is answered in chat, with no edits.
- [One question at a time](feedback_one_question_at_a_time.md): one question per reply, with a recommendation.
- [No question pickers](feedback_no_question_pickers.md): ask in plain text, never through the picker tool.
- [No release records](feedback_no_release_records.md): never record individual releases in notes or the README.
- [Changelog](feedback_changelog.md): the unrelease: block, newest first, one plain sentence per line ending in a period.
- [Todo list format](feedback_todo_list_format.md): ##Unfinished. and ##Finished., players only, bugs stated as what happens.
- [Back first](feedback_back_first.md): Back is the first row of every menu with a way back, and it opens on it.
- [Say ear tests ahead](feedback_say_ear_tests_ahead.md): before each section, list the by-ear tests (sound and speech), each optional or mandatory; remind the dev of a mandatory one not reported on.
- [Docs after each plan](feedback_docs_after_each_plan.md): when a plan is finished, bring every developer doc (aidocks included) and player doc up to date, then push.
- [Progress summary](feedback_progress_summary.md): after each plan, a brief overall percentage, by agreed weights per plan; 100 percent after plan 7.
- [Review plan sections](feedback_review_plan_sections.md): before building any plan, review it section by section with the dev; never start the next plan alone.
- [Next section on a pass](feedback_next_section_on_pass.md): when the dev says a section's tests passed, mark and commit it, then build the next section without asking; not across plans.
- [Grow check tools](feedback_grow_check_tools.md): a plan's by-ear tool starts in its first audible section and grows with each section.
- [Test tools in interact](feedback_test_tools_in_interact.md): by-ear tools go in tests/interact/, never in the game's menus.

## User
- [Screen reader](user_screen_reader.md): the dev uses NVDA; headings, lists and short lines, no wide tables, no noise from tools.
