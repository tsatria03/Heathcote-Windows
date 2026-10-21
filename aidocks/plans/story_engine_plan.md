---
name: story_engine_plan
description: "Plan 4: playing the story by the original's rules: the variables, the timed sets, the first matching next, the idle loop, lockout and its grace, the actions menu and its recorded choices, heard spiels, the end, the keys during play, and debug mode's keys."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, with every question answered (2026-10-19). Waiting for the go-ahead to build.

Plan 4 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]] and [[audio_plan]], and reads the story data directly as `tools/story.py` does. Every rule below comes from [[project_original_behaviour]], which cites the original's code.

## What plan 3 built for it

The audio plan, finished 2026-10-20 ([[audio_plan]]), left these ready for the story engine:
- **`audio.spiel`, the `SpielPlayer`:**
  - `play(path)`; `position`, `length` and `ended`
  - `rewind()`, `fast_forward()` and `stop_effects()`, the original's tap
  - `rewind_sound` takes the `rewind` interface sound's path
  - A spiel started during fast-forward fast-forwards too, with a frame's grace, so the engine can start the next spiel in the frame it sees the end.
- **`Lanes(audio, story)`:**
  - The engine calls `begin_spiel(record)` as each spiel starts, which also stops the idle loop.
  - It passes `update(spiel.position)` each frame, which fires the lane events and rebuilds after a rewind.
  - It calls `start_idle(soft)` when a spiel ends with nothing to follow.
  - `holding` and `opening` give what each lane holds by softRef, for the saves.
- **Pausing and the hush:**
  - `audio.pause_story()` and `resume_story()` pause as the original did, the backgrounds hushed and playing on, and only the spiel stopped. The caller plays `pause-pause` and `pause-unpause`.
  - `audio.hush_backgrounds()` and `unhush_backgrounds()` nest, so the actions menu's hush opened over a pause needs its own unhush.
- **Interface sounds:** `app.play_sound(label)` plays them by label on the sfx channel.
- **The story fades:** `audio.fade_story(level, seconds)`.

## Built in sections

Each section is confirmed by the dev before the next starts. **`tests/interact/story_check.py` starts in section 2 and grows with every section,** with its own save ([[feedback_grow_check_tools]]; the dev, 2026-10-20: "Yes. It should."):
1. The story's state: the variables, heard spiels and how many times each action was chosen, kept in memory for now (the saves plan writes them to disk). Nothing to hear.
2. Playing spiels: starting at `start`, the timed sets, the lane events, the first matching next, the idle loop, the silent spiels, and the end. `story_check.py` starts here, playing the story from `start`.
3. Lockout and the actions menu, with its recorded choices. `story_check.py` gains the menu.
4. The keys during play: rewind, fast-forward, pause, the menu and the description of where you are. `story_check.py` uses the game's own keys.
5. Debug mode's keys, and `--spiel`. `story_check.py` gains F2 to F4 and starting at any spiel.
6. `story_check.py` is rounded off as the whole tool.

## Reviewed

Reviewed section by section with the dev on 2026-10-20 ([[feedback_review_plan_sections]]). Section 1 was approved on its own ("Yes"), then sections 2 to 6 were reviewed together ("review all of the sections in 1 chat"). What the review found:
- **Both checks were settled first** from the code (see Decided).
- **`heathcote/game/state.py`** holds the state, by softRef, built on `storydata.py`. It snapshots and restores as one, for the saves. What the lanes hold stays in plan 3's `Lanes`.
- **The story screen is `heathcote/game/story_screen.py`,** built on plan 3's `audio.spiel`, `Lanes`, pause and hush.
- **Until plan 5:**
  - the end says "The story has ended." and returns to the main menu
  - the stand-in main menu gains a "Start story" row
  - a stand-in pause has Resume and Return to menu
  
  Plan 5 replaces all three.
- **The 7-second repeat in the actions menu plays only the clip.** The original's swipe hint does not fit a keyboard.
- **The actions menu is plan 2's spoken menu,** with `moved()` playing the clip.
- **F3 reuses `audio_check.py`'s spoken search.** A jump keeps the variables as they are.

## Decided

- **The story starts at the spiel labelled `start`** (`+[Story justStart]`, 0x10001a6e0).
- **Every story variable starts as "0"**, and every condition is an exact match of text.
- **Timed sets** fire when playback passes their `at` time, applying their values. Going backwards undoes nothing, as in the original.
- **When a spiel ends,** its next entries are tried in order and the first whose conditions all hold plays (`+[Sound tick]`, 0x100020930). If none holds, its idle loop starts.
- **A spiel with no recording**, such as "east wing dispatch", makes no sound and goes straight to its next, as in the original, whose synthesizer was a stub.
- **When a spiel ends with nothing to follow**, `lockout` becomes "0", `menu-available` plays, and the spiel is marked heard (`-[PlayState startPlayed]`, 0x1000336bc).
- **When a timed set turns `lockout` to "0"**, `menu-lockout-ended` plays (`+[StoryView spielJustSetVariables:]`, 0x1000256f4).
- **Opening the actions menu** (`+[StoryView raiseActionsDial]`, 0x100024204):
  - It opens when `lockout` is "0", or when the spiel last played has been heard before.
  - Otherwise it plays `click-bad` then `menu-unavailable`, and a 1.5-second grace starts, during which pausing is refused with `click-bad`.
  - When it opens: `click-good`, the backgrounds are hushed, the spiel pauses, and `menu-open` plays.
- **The actions menu's choices** (`+[Story actionsMenu]`, 0x10001aaa8):
  - Every action whose conditions all hold, minus those that burn after reading once chosen as often as they have spiels.
  - In `order`, lowest first. It opens on the first and wraps round.
  - Each move plays the choice's recorded clip from `speech/`. A choice with no clip, such as "next room" or "just stop", is spoken by the screen reader, since the original's stub said nothing.
  - After 7 seconds with no move, the current choice is played again.
- **Choosing an action** (`+[Story respondToDecision:]`, 0x10001b2e8): `menu-accepted` plays, the backgrounds unhush, the action's count goes up by 1, its `set` applies, and its spiel starts 0.25 seconds later.
- **Closing the menu** without choosing: the backgrounds unhush and the spiel plays on.
- **After a spiel ends**, `menu-reminder` plays every 7 seconds until something happens (`-[PlayState tick_played]`, 0x100033194).
- **The end:** when the variable labelled `end` becomes anything but "0", the story ends and the end credits begin (`-[Vars setString:to:]`, 0x100030f48).
- **Losing the window's focus** plays `lost focus` and pauses, closing the actions menu if it is open.
- **The keys during play,** following the original's swipes (the dev, 2026-10-19: "I want the arrow keys to be rebindable, so yes."):
  - Up arrow or Enter opens the actions menu (swipe up).
  - Left arrow rewinds (swipe right) and Right arrow fast-forwards (swipe left): the arrow that points back goes back.
  - Escape pauses (swipe down).
  - In the actions menu: all four arrows move through the choices, Up and Left back and Down and Right on, wrapping round; Home jumps to the first choice and End to the last; Enter accepts; Escape closes. Each move plays the choice's clip, as in the original. These are the same keys as every other menu ([[foundation_plan]]; the dev, 2026-10-19: "this game should be like [the other game] where you can press all the arrow keys for menu choices, plus home/end.").
  - Tab says where you are, as the two-finger tap did: "Story is playing.", "Story is at end of scene." or "Actions menu is open."
  - **Every one of them is rebindable on the F1 screen, the arrows included** ([[foundation_plan]]). Each is an action in `config/keys.json`, never a key fixed in code; only the F1 screen's own F1 and Escape stay fixed, so there is always a way out of it.
- **Space speaks the selected choice's text through the screen reader** (the dev, 2026-10-19: "I like that. Space is fine."), the idea the dev raised earlier ("you should be able to press a key to here the screen reader version of those choices if you hover over one"). It reads the transcript of the choice's `systemVoice` record, or its label when there is none, without moving or accepting. It is rebindable like the rest.
- **Debug mode's keys** (the dev, 2026-10-19: "I like that."), in debug mode only ([[foundation_plan]]), rebindable like the rest:
  - F2 skips to the end of the current spiel. The timed sets and lane events left in it fire on the way, so the story stays as it would have been.
  - F3 asks for a spiel's label and jumps to it, taking the same labels as `--spiel` and the "Spiel:" headings of `analysis/script/Heathcote.txt`.
  - F4 speaks every story variable that is not "0", by label, such as "fear is clowns, flashlight is hint", or "Every variable is 0." when none is.
- **The two checks, settled from the code on 2026-10-20** ([[project_original_behaviour]]):
  - Only the spiel that ends with nothing to follow is marked heard. A spiel passed through by `next` never is.
  - Timed sets fire again after a rewind, on the way forward, since the original stores the new position as the last position even after a jump back.

## Open questions

None.
