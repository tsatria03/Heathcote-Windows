---
name: player_feedback_plan
description: "Plan 12: a forum player's requests after the second release: clicks on choosing in the actions menu and on pausing, and the idle loop fading out when the next spiel begins."
metadata:
  node_type: memory
  type: project
---

**Status:** section 1 built and passed 2026-10-22 (the dev: "The 3 click sound test past. Ready for section 2."); section 2 built 2026-10-22, waiting on its ear test. No section review, on the dev's word ("Please write this plan, then fix the first 2 things the player requested. No section review is required.").

Plan 12. From a player's post on the forum after the second release, which the dev passed on, 2026-10-22: "When selecting something, the click sound should also play over the whistle cue. Also when pausing, it should also play the click over the pause sound." and "when you select something, the ambiance doesn't come back, leaving the game to just play the audio track of whatever choice without the ambiance over it."

## What the original did

- **Accepting a choice** played `menu-accepted` alone (+[StoryView acceptFromActionsDial], 0x10002477c); [[menu_sounds_plan]] kept the actions menu's Enter and Escape free of the click for that reason.
- **Pausing** played `pause-pause` alone (+[StoryView pause], 0x1000252cc).
- **The ambience.** Opening the actions menu hushes the music and the three ambiences, which play on muffled; accepting unhushes them. That works. What goes quiet after a choice is the **idle loop**, which plays only once a scene has ended with nothing to follow, such as `idle loop (footsteps)`, and stops the moment the next spiel begins (+[Sound playSpiel:], 0x100021af0), with no fade. The story data has 15 idle loops but only 36 ambience fades in 605 records, so many scenes have no ambience under the voices at all, by the original's design ([[project_original_behaviour]]).

## Decided

- **Section 1, the clicks:**
  - Enter in the actions menu plays `click-good` with `menu-accepted`, and Escape, closing it, plays it with `menu-close` (the dev, 2026-10-22, after the first build left closing silent: "It should also click when close a menu with choices.").
  - Escape pausing the story plays `click-good` with `pause-pause`. A pause made by losing the window plays no click, as no key was pressed; it keeps `lost focus`.
  - Resuming clicks with `pause-unpause`, whether by Enter on Resume or by Escape in the pause menu ("Same for if you resume the game with escape."). It already did, as the pause menu clicks like any menu ([[menu_sounds_plan]]); a test now holds it.
  - Click sounds in Settings turns these clicks off with every other.
- **Section 2, the idle loop:** it fades out over 2 seconds when the next spiel begins, rather than stopping at once, so the quiet comes on gently. It does not play on under the next spiel, as several would clash with what follows, such as `idle loop (dual calls (answer landline))` and the Judith loops. A rewind of an ended scene still stops it at once.

## Ear tests

Section 1:
1. Mandatory: choosing in the actions menu plays the click with the whistle, and Escape closing it plays the click with its close sound.
2. Mandatory: Escape pausing the story plays the click with the pause sound, and Escape resuming plays it with the unpause sound.
3. Optional: with Click sounds off, none of these clicks plays, and the story's own sounds stay.

Section 2:
1. Mandatory: after a scene ends and its idle loop plays, choosing fades the loop out over about 2 seconds as the next part begins.

## What was built

Section 1, 2026-10-22:
- `actions_menu.py`: `click_on_choose` and `click_on_back` are on, as in every other menu.
- `player.py`: `pause(click=False)`; with `click`, `click-good` plays before `pause-pause`. `story_screen.py`'s `StoryScreen.pause()`, Escape's, passes it; `focus_lost()` does not.
- Tests: two new, in `test_actions.py` and `test_keys.py`.

Section 2, 2026-10-22:
- `lanes.py`: `IDLE_FADE = 2.0`; `stop_idle(fade_out=0.0)`, and `begin_spiel()` passes `IDLE_FADE`. The slot is free at once and the loop fades on its own channel, as a lane's crossfade does, so a scene ending soon after can start its own idle loop. A rewind and leaving the story still stop it at once.
- Tests: the idle loop test in `test_lanes.py` now checks the fade, and that `stop_idle()` alone is still at once.

## Built in sections

1. The clicks.
2. The idle loop's fade.

## Open questions

None.
