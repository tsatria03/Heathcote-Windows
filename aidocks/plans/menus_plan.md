---
name: menus_plan
description: "Plan 5: the screens around the story: the opening, the first-run notice, the main menu with Start story or Continue story, Settings, the pause menu with Restart story, the end and its credits, read from the original's own credit cards, with FMOD's credit line."
metadata:
  node_type: memory
  type: project
---

**Status:** being built, from 2026-10-20, on the dev's word ("you can jump to starting section 1."). Section 1 is finished; section 2 is built and waiting for the dev's tests.

Plan 5 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]], [[audio_plan]] and [[story_engine_plan]]. What the original did comes from [[project_original_behaviour]].

## What the original had
- **A developer splash** (`IdentState`): the `ident` system sound, a police radio, over Fabulae Obscurae's logo; swipe up skipped it.
- **A first-run tutorial** (`PreflightState`), shown until `tutor-preflight` was set, with these texts: "Heathcote is a responsive story told through Sound. Headphones are strongly recommended.", "For the most immersive experience, try playing with your eyes closed.", "Control the story by swiping, not tapping." and "Double-tap to continue." Its three cards then taught the swipes.
- **The title** (`TitleState`) over the `title` music, moving on by itself after 4 seconds.
- **The title menu** (`TitleMenuState`): START ("Start story"), or CONTINUE ("Continue story from chapter: '<location>'.", where <location> is the story variable `location`), and RESTART, which asked "RESTART THE STORY?" and "If you tap RESTART, your progress will be lost."
- **Pausing:** swipe up resumed; swipe down went back to the title menu, leaving the story paused, so CONTINUE picked it up exactly there.
- **The end:** the credits, then the title menu after swiping down, the story reset, and "Want more?" with "Nah" or "Yes please!", which opened a web page.
- **Online and phone parts:** a bug report button, a rate-me alert, analytics, crash reporting and location services. None of it is ported.

## The original's credits

The credits were two pictures, `credits-1` and `credits-2`, so a screen reader never read them. Read from the images on 2026-10-19, they say:
- Card 1, under the Heathcote title, version 1.01:
  - Story: Christian Francis, Ben Meares
  - David Scott, Fausto Kaufer, Joe Banks: Hunter Davis
  - Martin Fellows: Robert Dunne
  - Announcer: Mark Hamilton
  - Music: Jason Martin Castillo
- Card 2, under the Fabulae Obscurae logo:
  - Design and Engineering: Mike Dean
  - Producing and Directing: Lisa Wong
  - Audio Consultant: Alex Ruger
  - Special thanks to Nowell Valeri
  - "This app uses many sounds from freesound. For the full list see fabulaeobscurae.com/heathcote"
  - "FMOD Studio by Firelight Technologies"

## What plan 3 built for it

The audio plan, finished 2026-10-20 ([[audio_plan]]), left these ready for the menus:
- **The title music:**
  - It plays on the `titleBgm` slot: `audio.slot('titleBgm').play(path)`, with the path from `StoryData.sound_path('bgm', 'title')`.
  - It fades out with `stop(fade_out=3.0)`.
  - It follows the title volume. `Title.mp3` fades out by itself in its last seconds before each loop, as the original's did.
- **`app.title_music` is still a stand-in flag** set by the stand-in main menu. The menus plan sets it while the title music really plays, so the title volume's keys follow the music.
- **The pause menu** uses `audio.pause_story()` and `resume_story()`, the original's pause, with `pause-pause` and `pause-unpause` played by `app.play_sound()`.
- **The ending music** is `StoryData.sound_path('bgm', 'ending')`.

## What plan 4 built for it

The story engine, finished 2026-10-20 ([[story_engine_plan]]), left these for the menus plan to replace or use:
- **Stand-ins to replace:**
  - the stand-in main menu's Start story row, in `heathcote/game/menus.py`
  - the stand-in `PauseMenu` (Resume, Return to menu) in `heathcote/game/story_screen.py`
  - the end, which says "The story has ended." and returns to the main menu, in `StoryScreen.story_ended()`
- **The story screen:**
  - `StoryScreen(app, state=None, story=None, start_at=None)` plays the story; `start_at` begins at a spiel.
  - Its player's `on_story_end` is the place for the end credits.
  - `player.pause()` and `resume()` pause as the original, the idle loop muffled too, and play `pause-pause` and `pause-unpause`. Pausing is refused in the grace after a refused menu.
  - `player.stop()` leaves the story.
- **Restart story** can use `state.reset()` and `player.start()`.
- **`--spiel`:** `app.start_spiel` holds its spiel, which Start story takes the first time.

## Read from the binary for section 1

Found 2026-10-20, with `tools/dis64.py`:
- **The splash** (`-[IdentState tick]`, 0x10003e6bc) plays `ident` on the `sfx` channel (`playSystemSound:onChannel:`, the channel made after "sfx" in `+[Sound initEngine]`, 0x10002073c). It moves on when that channel stops playing (`isPlaying`, 0x10003e790), not after a set time.
- **Skipping it** (`-[IdentState up]`, 0x10003e974) plays `click-good`, stops the `sfx` channel and moves on at once.
- **Starting the title music** (`-[GameView titleMusicShouldBePlaying]`, 0x100019594) plays it at once, with no fade, looping, and fades the story group out over 2 seconds (`fadeOutStoryChannelGroup`). A flag keeps it from starting twice. Stopping it fades it out over 3 seconds and fades the story group in over 1 second. So after Return to menu, a paused story's muffled backgrounds fade out under the title music, and they fade back in when the story is entered again.

## What section 1 built

Built 2026-10-20, waiting for the dev's ear tests:
- **`heathcote/game/opening.py`:**
  - `OpeningScreen` plays `ident` on `sfx` with "Heathcote." spoken, and moves on when it ends, about 11 seconds. Enter skips it with `click-good`; any other key gives `click-bad`.
  - `NoticeScreen` speaks the notice, then "Press Enter to continue.", naming the first key bound to Menus: choose. Enter sets `first_run_notice_shown`; any other key says it again.
  - `Heathcote.py` opens on `OpeningScreen`.
- **`App.start_title_music()` and `stop_title_music()`** in `heathcote/app.py`, with the original's story group fades, and `app.title_music` now true only while the music is meant to play. The stand-in main menu starts it as it opens; the story screen stops it.
- **`tests/interact/menus_check.py`** runs the game from its opening, with its own save and three keys of its own: Control+N forgets the notice and starts again, Control+T says whether the title music is playing and at what volume, and whether the story's sound is faded in, faded out or fading (reworded at the dev's word: "SOmething clearer."), and Control+Q quits.
- **Tests:** four new ones, and the main menu's story test now checks the title music too. 158 in all.
- **The dev's ear tests passed,** all five, 2026-10-20 ("all 5 tests past, including the optional ones."):
  1. Mandatory: the police radio, with "Heathcote." spoken.
  2. Mandatory: the notice the first time, Enter continuing, and not shown again.
  3. Mandatory: the title music under the main menu, with Page Up and Page Down.
  4. Mandatory: Start story fading the title music out, and Return to menu bringing it back.
  5. Optional: Enter skipping the police radio.
- **Also during section 1,** at the dev's word: the recorded choices in `speech/` follow only the master volume, no longer the interface volume ([[audio_plan]]). Its ear test, mandatory, is still to come: in the actions menu, Shift+Page Down makes the clicks quieter while the recorded choices stay as loud.

**Section 1 is finished,** on the dev's word.

## What section 2 built

Built 2026-10-20, straight after section 1 passed ([[feedback_next_section_on_pass]]), waiting for the dev's ear tests:
- **`heathcote/game/credits.py`:** `CreditsMenu`, titled "Credits.", Back first and opened on, then a row for each of the original's credits in its cards' order (`ORIGINAL`), the port's row, "Windows port: tsatria03", and FMOD's line, "Made with FMOD Engine, by Firelight Technologies Pty Ltd.". Enter on a credit says it again. Section 4's end credits will open the same menu.
- **The main menu** (`heathcote/game/menus.py`) has its four rows: Start story, Settings, Credits and Quit. Start story still starts afresh each time; section 3 brings Continue story.
- **Settings** is unchanged: Back, Debug mode from source, and Key bindings. Nothing new was decided for it; section 3 opens it from the pause menu too.
- **The title music plays on** through Settings and Credits, with Page Up and Page Down, since both cover the main menu without stopping it.
- **`menus_check.py`** needs no new keys for this section; its description now lists it.
- **Tests:** two new ones for the credits, and the main menu's tests now have four rows. 160 in all.
- **The dev's ear tests,** to come:
  1. Mandatory: the main menu's four rows, all four arrows moving and wrapping, Home and End.
  2. Mandatory: Credits opening on Back, each credit its own row, and Back or Escape returning.
  3. Mandatory: the title music playing on through Credits, with Page Up and Page Down.
  4. Optional: the title music playing on through Settings.
  5. Mandatory, still from section 1's volume change: in the actions menu, Shift+Page Down makes the clicks quieter while the recorded choices stay as loud.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. The opening, the first-run notice and the title.
2. The main menu, Settings and Credits.
3. The pause menu.
4. The end of the story and its credits.

## Decided

- **The original's credits become text**, spoken as a menu, Back first, one row each, such as "Story: Christian Francis, Ben Meares", followed by a row for the port, by tsatria03, and FMOD's credit line, which names "FMOD" and "Firelight Technologies Pty Ltd." as its licence requires ([[project_fmod]], [[project_later_topics]]). The original's own credits already named FMOD.
- **Every menu follows the standing rules:** Back first and opened on ([[feedback_back_first]]), all four arrows moving and wrapping, Home and End to the first and last row, and no position readouts ([[foundation_plan]]).
- **The bug report, the rate-me alert, analytics, crash reporting and location services are left out.**
- **Restart story asks first,** as the original did, with No as the first row.
- **The rows are named "Start story", "Continue story" and "Restart story"** (the dev, 2026-10-19: "Also rename continue to continue story. Same for restart."), never "Continue" or "Restart" alone.
- **The main menu** (the dev, 2026-10-19: "I like that."), with the same navigation as every menu, all four arrows, wrapping, and Home and End, which the dev checked ("This will have the same menu functions right? I mean the arrow/home nav, plus menu wrapping"):
  1. **Start story,** or once started, **Continue story**, said with its chapter as the original did: "Continue story, from chapter: <location>.", where <location> is the story variable `location`. It is one row whose name changes, so the two are never offered together. It comes first, so one Enter gets back into the story.
  2. **Settings.**
  3. **Credits.**
  4. **Quit,** its way out, so it has no Back row ([[feedback_back_first]]).
  - **No Restart story here** (the dev, 2026-10-19: "Also get rid of it from the main menu."). The original's title menu had one, but the port's is in the pause menu instead: Continue story, then Escape, then Restart story.

- **The opening** (the dev, 2026-10-19: "Agreed."):
  1. The `ident` sound, the original's police radio, with "Heathcote" spoken.
  2. The first time only, a notice from the original's tutorial: "Heathcote is a responsive story told through sound. Headphones are strongly recommended. For the most immersive experience, try playing with your eyes closed." Enter continues, and the game remembers it has been shown, as the original's `tutor-preflight` did. The line "Control the story by swiping, not tapping." is left out, since it does not fit a keyboard.
  3. Then the `title` music and the main menu, with no 4-second title wait.
- **The title music plays under the main menu,** as the original's did under its title menu ([[project_original_behaviour]], "Where the title music plays"):
  - It fades out over 3 seconds when Start story or Continue story enters the story.
  - It stays silent in the pause menu.
  - It starts again whenever the main menu comes back: from Return to menu in the pause menu, and after leaving the end credits.
  - It has a volume of its own, the title volume, which Page Up and Page Down set while it plays ([[audio_plan]]).

- **The pause menu** (the dev, 2026-10-19: "I like this, but what about the restart button?", then "Yes."). Escape during the story pauses as the original did, the spiel stopping and the backgrounds playing on under the hush ([[audio_plan]]), and opens it:
  1. **Resume,** first and opened on; Escape does the same.
  2. **Restart story:** "Restart the story? Your progress will be lost.", with No first. Yes resets the story's variables, the heard spiels and the actions' counts, and starts again at `start`, as the original's restart did (`-[ViewController resetGameState]`, 0x100011068). Settings and the first-run notice stay as they were. The original had no restart in its pause screen, only on its title menu.
  3. **Settings,** the same screen as the main menu's.
  4. **Return to menu,** leaving the story paused, so Continue story picks it up exactly where it stopped, as the original did. It does not ask, since nothing is lost.
- **The end** (the dev, 2026-10-19: "Yes please."):
  1. When the story sets `end`, the `ending` music plays on and the credits menu opens: Back first, then the original's credits one row each, then the port's row and FMOD's credit line.
  2. Leaving the credits resets the story, as Restart story does, and returns to the main menu, which offers Start story again, as the original did (`+[StoryView lowerCredits]`, 0x1000264a8).
  3. The original's "Want more?" prompt, which opened the developer's website, is left out.
- The main menu's Credits row opens the same credits menu, without resetting anything.

## Open questions

None.
