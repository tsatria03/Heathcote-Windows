---
name: story_engine_plan
description: "Plan 4: playing the story by the original's rules: the variables, the timed sets, the first matching next, the idle loop, lockout and its grace, the actions menu and its recorded choices, heard spiels, the end, the keys during play, and debug mode's keys."
metadata:
  node_type: memory
  type: project
---

**Status:** planned. Being written; open questions below are still being answered.

Plan 4 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]] and [[audio_plan]], and reads the story data directly as `tools/story.py` does. Every rule below comes from [[project_original_behaviour]], which cites the original's code.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. The story's state: the variables, heard spiels and how many times each action was chosen, kept in memory for now (the saves plan writes them to disk).
2. Playing spiels: starting at `start`, the timed sets, the lane events, the first matching next, the idle loop, the silent spiels, and the end.
3. Lockout and the actions menu, with its recorded choices.
4. The keys during play: rewind, fast-forward, pause, the menu and the description of where you are.
5. Debug mode's keys, and `--spiel`.
6. `tests/interact/story_check.py`, a tool to play the story from any spiel by ear, with its own save.

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
  - In the actions menu: Up and Down, or Left and Right, move through the choices; Enter accepts; Escape closes.
  - Tab says where you are, as the two-finger tap did: "Story is playing.", "Story is at end of scene." or "Actions menu is open."
  - **Every one of them is rebindable on the F1 screen, the arrows included** ([[foundation_plan]]). Each is an action in `config/keys.json`, never a key fixed in code; only the F1 screen's own F1 and Escape stay fixed, so there is always a way out of it.
- **Two things are checked in the code before section 2 is built:** whether a spiel reached through next is marked heard, and whether timed sets fire again after a rewind.

## Open questions
1. Which key speaks the selected choice's text through the screen reader, the idea kept in [[project_later_topics]]? Proposed: Space.
2. Debug mode's keys? Proposed: F2 skips to the end of the current spiel, F3 asks for a spiel's label and jumps to it, and F4 speaks every variable that is not "0".
