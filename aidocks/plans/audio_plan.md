---
name: audio_plan
description: "Plan 3: playing Heathcote's sound through pygame's mixer: the spiel, the music and three ambience lanes with their timed crossfades, the idle loop, the system sounds and spoken choices, rewind, fast-forward, the hush and the volumes, matched to the original's numbers."
metadata:
  node_type: memory
  type: project
---

**Status:** planned. Being written; open questions below are still being answered.

Plan 3 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]] and serves the story engine. Every number below comes from [[project_original_behaviour]], which cites the original's code.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. Finding recordings, and the mixer: the channels, playing, stopping, looping, fading and the volumes.
2. The spiel: streaming, its position, pausing, rewind and fast-forward.
3. The lanes: the music, the three ambiences and the idle loop, with their timed crossfades, the hush, and setting them up again after a jump back.
4. `tests/interact/audio_check.py`, a tool to hear any spiel with its lanes by ear, with its own save.

## Decided

- **pygame's mixer plays everything, as MP3** ([[project_python_only]]). Nothing else opens the audio device. With no sound device, the game carries on silent.
- **A recording is found as [[project_audio_names]] says**: through its file record's `original.name`, in the folders for its category, the way `tools/story.py` already finds it. The game and the tool share that rule.
- **The original's channels, kept as they were** (`+[Sound initEngine]`, 0x1000203f0):
  - **spiel:** the story recording, streamed through `pygame.mixer.music`, the only pygame player that can start partway through a file. Rewind and fast-forward need that.
  - **bgm, ambience1, ambience2, ambience3:** the four background lanes, each a looping `pygame.mixer.Sound` on its own channel, with a second channel each so one recording can fade into the next.
  - **idleLoop:** the loop after a spiel ends with nothing to follow.
  - **titleBgm:** the title music.
  - **sfx:** the system sounds, such as `click-good` and `menu-open`.
  - **systemVoice:** the recorded choices in `speech/`.
- **The plain `ambience` lane is never played**, as in the original, which never reads it. So the fades listed there in `start`, `cells` and `offices` are skipped.
- **The lanes follow each spiel's timed events:**
  - `fadeTo {duration, softRef}` crossfades the lane to that recording over `duration` seconds, then loops it.
  - `fadeOut {duration}` fades the lane out over `duration` seconds and stops it.
  - An event fires when the spiel's playback passes its `at` time.
- **The lanes carry on from spiel to spiel.** A lane changes only when an event says so.
- **When the story opens**, the lanes that were playing when the resumed spiel began start again, each fading in over 0.5 seconds (`+[StoryView go]`, 0x100025ce8).
- **After a jump backwards**, each lane is set up again from what it held when the spiel opened, replaying its events up to the new position, so the right recording plays there.
- **Rewind** (`-[PlayState tick_rewind]`, 0x100033248):
  - The `rewind` sound plays.
  - Every 7 ticks the spiel jumps back 1 second, for 45 ticks (0.75 seconds), then plays on.
  - At the beginning it stops early, and the sfx channel fades out over 0.75 seconds.
  - Rewinding a spiel that has ended stops the idle loop and replays from just before its end.
- **Other fades, as the original has them:**
  - The title music fades out over 3 seconds when the story starts.
  - The whole story fades out over 2 seconds and in over 1 second (`+[Sound fadeOutStoryChannelGroup]`, 0x1000225d4; `fadeInStoryChannelGroup`, 0x100022690).
- **The hush** is a counter, as in the original: nested hushes need as many unhushes. It covers the music and the three ambiences, never the spiel or the idle loop (`+[Sound hushBackgrounds]`, 0x1000223b8).
- **Pausing pauses every channel together**, and resumes them together. pygame says a paused stream is not playing, so the game tracks pausing itself.
- **Lengths and positions:** pygame cannot give a streamed MP3's length, so it is read from the file's own headers (a Xing, Info or VBRI frame count, or else the bitrate). The spiel's position is kept by the game's own clock from where it last started.
- **Master volume:** Shift+Home raises it and Shift+End lowers it ([[foundation_plan]]).

## Open questions
1. The original fast-forwards by playing the spiel at 1.75 times its speed for 1.5 seconds. pygame cannot change a recording's speed. Should fast-forward instead jump forward, the way rewind jumps back: 1 second every 7 ticks for 45 ticks, with the timed sets and lane events it passes firing on the way?
2. The original's hush muffles the backgrounds with an EQ around 1250 Hz, by up to 12 dB. pygame has no live filters. Should the hush instead lower the backgrounds by 12 dB, to a quarter of their volume, over the same short ramp?
3. Which volumes are there besides the master? Proposed: Page Up and Page Down for the backgrounds (the music, the ambiences and the idle loop), and Shift with Page Up and Page Down for the interface (the system sounds and the recorded choices). Each press says the new level, and the game remembers them.
