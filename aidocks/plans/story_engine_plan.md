---
name: story_engine_plan
description: "Plan 4: playing the story by the original's rules: the variables, the timed sets, the first matching next, the idle loop, lockout and its grace, the actions menu and its recorded choices, heard spiels, the end, the keys during play, and debug mode's keys."
metadata:
  node_type: memory
  type: project
---

**Status:** being built (the dev, 2026-10-20: "Perfect! Now you can start."). Section 1 is confirmed ("Section 1 looks good. Please continue"), and so is section 2, after the dev's ear tests ("all 3 hering tests past."). Section 3 is confirmed too, after the dev's ear tests ("all 4 tests past perfectly!"). Section 4 is built and waits for the dev's word (the dev: "Ready for section 4.").

## Progress

- **Section 4, built 2026-10-20, waiting for the dev's word:**
  - **The player gains the keys during play:**
    - **`rewind()` and `fast_forward()`,** each with `click-good`, never under the menu or while a choice waits. A rewind of an ended scene stops its idle loop and plays it again from 1 second before its end.
    - **`pause()`,** as the original: `pause-pause`, the backgrounds hushed and playing on, and the spiel stopped. It is refused with `click-bad` in the grace after a refused menu.
    - **`resume()`** plays `pause-unpause`.
    - **`where()`,** Tab's words: "Story is playing.", "Story is at end of scene.", "Actions menu is open.", "Story is paused." or "Story has ended."
    - **No reminder while paused.** `close_menu(quietly=True)` leaves out `menu-close`, and leaving the story undoes a pause silently.
  - **`StoryScreen`:**
    - It takes the story group's actions: the actions menu, rewind, fast-forward, pause and where.
    - **Escape pauses** with a stand-in `PauseMenu`, until plan 5. Its rows are Resume, first, as Escape is too, and Return to menu, which leaves the story.
    - **Losing the window** plays `lost focus` and pauses with the pause menu. From the actions menu, it closes the menu quietly first.
  - **`ActionsMenu`:** Tab says "Actions menu is open.", and losing the window closes it.
  - **`story_check.py`** has the game's keys. Its own status moves from Tab to S, and quitting from Escape to Q. Return to menu in the pause menu quits the tool.
  - **`tests/case/test_keys.py`, 10 tests:**
    - rewind and fast-forward with `click-good`, and none under the menu
    - rewinding an ended scene
    - pause and resume, and pausing refused in the grace
    - Tab's words, and no reminder while paused
    - Escape and the pause menu, the keys and Tab through the screen, and losing the window
    
    The main menu test now leaves the story through the pause menu. The suite passes, 144 tests.
  - **A bug the dev found:** `story_check.py` quit as it opened ("it quits as soon as I open it").
    - **The cause:** `StoryScreen` set the rewind sound on `audio.spiel` as the screen was made, but the tool makes its screen before `App.run()` starts FMOD, when `audio.spiel` is still None. The game itself makes the screen only after FMOD has started, so it never met it.
    - **The fix:** the rewind sound is set when the screen opens. A test makes a screen before FMOD starts, and the tool now writes `crash.txt` and speaks on any error.
    - **Checked:** the tool, started silently through its own entry point, played `start` with its ambience. The suite passes, 145 tests.
  - **To test by ear:**
    - **Mandatory:**
      - Left and Right in the story
      - Escape's pause and Resume
      - Tab's three messages
      - switching windows playing `lost focus` and pausing
    - **Optional:** a key rebound on F1, and Escape refused right after a locked menu.

- **Section 3, confirmed by the dev 2026-10-20, whose ear tests passed** ("all 4 tests past perfectly!"): the choices' recordings, lockout refusing, accepting, and Space.
  - **`heathcote/game/player.py` gains lockout and the menu:**
    - **`open_menu()`** opens when `lockout` is "0" or the spiel was heard before: `click-good`, the hush, the spiel paused, and `menu-open`. Otherwise it is refused, with `click-bad`, `menu-unavailable` and a 1.5-second grace (`in_grace`).
    - **`close_menu()`** plays `menu-close`, unhushes, and the spiel plays on.
    - **`accept(action)`** plays `menu-accepted`, unhushes, stops the old spiel, and chooses the action. Its spiel starts 0.25 seconds later through the timer loop, and nothing opens while it waits.
    - **`choice_clip()` and `choice_text()`:** a choice's clip, and its text, the recording's transcript.
    - **`menu-lockout-ended`** plays when a timed set turns `lockout` to "0".
    - **`menu-reminder`** plays every 7 seconds after a scene ends. `poke()` restarts the count on any key.
  - **`heathcote/platform/audio.py` gains `play_oneshot(path)`:** each interface sound on its own channel at the interface volume, freed when it ends, so `click-good` and `menu-open` sound together. `app.play_sound()` uses it.
  - **`heathcote/game/actions_menu.py`, `ActionsMenu`,** is plan 2's spoken menu:
    - it opens on the first choice, playing its clip
    - each move plays the clip, or the screen reader says a choice with none
    - after 7 seconds without a move, the clip plays again
    - Space speaks the choice's text, Enter accepts, and Escape closes
    - it takes the story's volume keys
  - **`StoryScreen`:**
    - Its actions menu key, Up or Enter, opens the menu.
    - Any key pokes the reminder.
    - The menu, not the screen, pauses and resumes the spiel under it.
  - **`story_check.py` now runs the game's own App and story screen,** with the tool's keys added in a `CheckScreen` subclass, so F1, the volumes and the menu are the game's own.
    - Starting again moves from Enter to R, as Enter opens the menu.
    - Tab says when the spiel is locked out, and when the menu is open.
  - **For the lockout test, the story's own path works:** `start`'s only choice is "landline", whose spiel, "call opening", locks the menu from 0.1 to 44.7 seconds, then plays `menu-lockout-ended`. 40 spiels lock the menu at 0.1 seconds.
  - **`tests/case/test_actions.py`, 10 tests:**
    - refusing with the grace, opening a heard spiel, opening, closing, and accepting with its delay
    - `menu-lockout-ended`, and the reminder with a poke
    - every choice having a clip
    - the menu screen's clips, wrapping, Space and accepting, and the screen reader for a made-up clipless choice, with Escape
    
    One interface sound test follows `play_oneshot`. The suite passes, 134 tests.
  - **To test by ear:**
    - **Mandatory:**
      - each move plays the right recorded choice
      - "call opening" refuses the menu before 44.7 seconds
      - accepting plays the chosen spiel
      - Space speaks the choice's text
    - **Optional:** the 7-second repeat, the reminder, and `menu-lockout-ended` at 44.7 seconds.

- **Section 2, confirmed by the dev 2026-10-20, whose ear tests passed** ("all 3 hering tests past."): a chain playing by itself, backgrounds in context, and a scene's end. (Section 3 later turned `story_check.py` into a layer over the game's own screen.)
  - **`heathcote/game/player.py`, `StoryPlayer(audio, story, state, play_sound)`,** the one place the story's rules are played. The game's story screen and `story_check.py` both drive it.
    - **Starting:** `start()` plays `start`, and `play(soft)` plays any spiel.
    - **Each frame, `update()`:**
      - applies the timed sets as playback passes them, firing again after a jump back, as the original
      - moves the lanes on
      - and, at a spiel's end, plays the first `next` that holds in the same frame, or ends the scene
    - **The end of a scene:** the idle loop starts, `lockout` is set to "0", the spiel is marked heard, and `menu-available` plays.
    - **A spiel with no recording,** or one missing on disk, passes straight on.
    - **The end of the story:** `end` set to anything but "0" ends it, once.
    - **Hooks:** `on_spiel`, `on_scene_end`, `on_story_end` and `on_changed`.
  - **`heathcote/game/story_screen.py`, `StoryScreen`:**
    - It plays the story from `start`, with the story's volume keys.
    - The window shows the spiel's label and up to 16 lines of its transcript.
    - Another screen on top, such as F1, pauses the spiel until it is back on top.
    - Escape leaves for the main menu until section 4's pause.
    - The end of the story says "The story has ended." and returns to the main menu 2 seconds later, until plan 5.
  - **The stand-in main menu gains "Start story"** as its first row, so the menu tests now expect it.
  - **`tests/interact/story_check.py` starts here, with its own save:**
    - Enter starts the story from its beginning.
    - Comma and Full stop choose any spiel, saying "leads on" when it has `next` spiels, 10 at a time with Shift, and 3 plays it with the state as it is.
    - Tab says where the story is, and V turns the spiel labels said as each begins on or off.
    - It has the story's three volumes.
    - Choosing a spiel was added because `start` has no `next`: its scene ends by itself after 12 seconds, so a chain can only be heard from a spiel that leads on, such as "check email", 15 of 104, which goes on to "commercial" and "commercial reflection".
  - **`tests/case/test_player.py`, 9 tests:** reading timed sets, `start` and its set, the lanes following, a scene's end, a chain not marking heard, a silent spiel, sets firing again after a jump back, the end, and the main menu's Start story with Escape. The suite passes, 124 tests. The tool was driven silently.
  - **To test by ear:**
    - **Mandatory:**
      - "check email" chains through "commercial" to "commercial reflection" by itself
      - the backgrounds change in context
      - at a scene's end, the idle loop and `menu-available` play
    - **Optional:** Start story in the game's stand-in main menu plays `start`.
- **Section 1, confirmed by the dev 2026-10-20 ("Section 1 looks good."):**
  - **`heathcote/game/state.py`, `StoryState(story)`:**
    - **The variables,** by softRef, each starting as "0". `apply()` takes a set and reports what changed. `holds()` matches a condition exactly, as text.
    - **By label:** `ended`, `locked_out` and `set_by_label()` go through the variables' labels.
    - **For F4:** `non_default()` gives the variables that are not "0", by label.
    - **Heard spiels** and **action counts.** `burnt()` is burn after reading, and `offered()` gives the actions on offer by `order`, with the index's order breaking ties.
    - **`choose()`** returns the action's spiel, `actionSpiels[count]` capped at the last, adds 1 to the count, and applies its set.
    - **`next_spiel()`** gives the first `next` entry whose condition holds, or None.
    - **`snapshot()`, `restore()` and `reset()`.** Restore drops what the story does not know, so an old save still loads.
  - **`tests/case/test_state.py`, 14 tests,** on the real story data. The suite passes, 115 tests.
  - The first run of the tests showed that no action in the story sets anything; every variable changes through spiels' timed sets, as [[project_original_findings]] already said. The rule still applies an action's set, as the original does, and a test checks it with a made-up action.
  - **Nothing to test by ear.**

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
  - Each move plays the choice's recorded clip from `speech/`. A choice with no clip is spoken by the screen reader, since the original's stub said nothing. **Found while building, 2026-10-20:** "next room" and "just stop", the two recordings with no file, are used by no action, so every choice in the story has its clip. The screen reader's part is kept as a safety net.
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
