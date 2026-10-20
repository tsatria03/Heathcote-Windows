---
name: menus_plan
description: "Plan 5: the screens around the story: the opening, the first-run notice, the title, the main menu with Start or Continue and Restart, Settings, the pause menu, the end and its credits, read from the original's own credit cards, with FMOD's credit line."
metadata:
  node_type: memory
  type: project
---

**Status:** planned. Being written; open questions below are still being answered.

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
- **Restart asks first,** as the original did, with No as the first row.
- **The main menu** (the dev, 2026-10-19: "I like that."), with the same navigation as every menu, all four arrows, wrapping, and Home and End, which the dev checked ("This will have the same menu functions right? I mean the arrow/home nav, plus menu wrapping"):
  1. **Start story,** or once started, **"Continue story from chapter: <location>."**, the original's own words, where <location> is the story variable `location`. It comes first, so one Enter gets back into the story.
  2. **Settings.**
  3. **Credits.**
  4. **Quit,** its way out, so it has no Back row ([[feedback_back_first]]).
  - **No Restart here** (the dev, 2026-10-19: "Also get rid of it from the main menu."). The original's title menu had one, but the port's Restart is in the pause menu instead.

- **The opening** (the dev, 2026-10-19: "Agreed."):
  1. The `ident` sound, the original's police radio, with "Heathcote" spoken.
  2. The first time only, a notice from the original's tutorial: "Heathcote is a responsive story told through sound. Headphones are strongly recommended. For the most immersive experience, try playing with your eyes closed." Enter continues, and the game remembers it has been shown, as the original's `tutor-preflight` did. The line "Control the story by swiping, not tapping." is left out, since it does not fit a keyboard.
  3. Then the `title` music and the main menu, with no 4-second title wait.

- **The pause menu** (the dev, 2026-10-19: "I like this, but what about the restart button?", then "Yes."). Escape during the story pauses every channel and opens it:
  1. **Resume,** first and opened on; Escape does the same.
  2. **Restart:** "Restart the story? Your progress will be lost.", with No first. Yes resets the story's variables, the heard spiels and the actions' counts, and starts again at `start`, as the original's restart did (`-[ViewController resetGameState]`, 0x100011068). Settings and the first-run notice stay as they were. The original had no restart in its pause screen, only on its title menu.
  3. **Settings,** the same screen as the main menu's.
  4. **Return to menu,** leaving the story paused, so Continue picks it up exactly where it stopped, as the original did. It does not ask, since nothing is lost.

## Open questions
1. What happens at the end? Proposed: the `ending` music plays on, the credits menu opens, and leaving it resets the story and returns to the main menu, as the original did. The "Want more?" link to the developer's website is left out.
