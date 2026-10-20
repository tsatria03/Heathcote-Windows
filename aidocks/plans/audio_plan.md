---
name: audio_plan
description: "Plan 3: playing Heathcote's sound through FMOD, as the original did: the spiel, the music and three ambience lanes with their timed crossfades, the idle loop, the system sounds and spoken choices, rewind, fast-forward with its pitch kept, the hush and the volumes, matched to the original's numbers."
metadata:
  node_type: memory
  type: project
---

**Status:** planned, with every question answered (2026-10-19). Waiting for the go-ahead to build.

Plan 3 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]] and serves the story engine. Every number below comes from [[project_original_behaviour]], which cites the original's code.

## Built in sections

Each section is confirmed by the dev before the next starts.
1. Starting FMOD, finding recordings, and the channels: playing, stopping, looping, fading and the volumes.
2. The spiel: streaming, its position, pausing, rewind and fast-forward.
3. The lanes: the music, the three ambiences and the idle loop, with their timed crossfades, the hush, and setting them up again after a jump back.
4. `tests/interact/audio_check.py`, a tool to hear any spiel with its lanes by ear, with its own save.

## Decided

- **FMOD plays everything, through `pyfmodex`** (the dev, 2026-10-19: "Yes please."), the engine the original used ([[project_fmod]]). pygame plays nothing. The game sets `PYFMODEX_DLL_PATH` to `vendor/fmod/fmod.dll`, or the build's copy, before importing `pyfmodex`. With no sound device, or in the tests, FMOD starts with its no-sound output and the game carries on silent.
- **A recording is found as [[project_audio_names]] says**: through its file record's `original.name`, in the folders for its category, the way `tools/story.py` already finds it. The game and the tool share that rule.
- **The original's channel groups and channels, kept as they were** (`+[Sound initEngine]`, 0x1000203f0):
  - Two groups, "story" and "system". The story group fades as a whole.
  - **spiel:** the story recording, opened as an FMOD stream so it can seek.
  - **bgm, ambience1, ambience2, ambience3:** the four background lanes, each looping, with a second channel each so one recording can crossfade into the next.
  - **idleLoop:** the loop after a spiel ends with nothing to follow.
  - **titleBgm:** the title music.
  - **sfx:** the system sounds, such as `click-good` and `menu-open`.
  - **systemVoice:** the recorded choices in `speech/`.
- **The plain `ambience` lane is never played**, as in the original, which never reads it. So the fades listed there in `start`, `cells` and `offices` are skipped.
- **The lanes follow each spiel's timed events,** with FMOD fade points:
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
- **Fast-forward, as the original** (`-[SoundChannel startFastForward]`, 0x10002f348):
  - The spiel plays at 1.75 times its speed for 90 ticks (1.5 seconds), then plays on. Starting it again while it runs restarts the 90 ticks.
  - FMOD's pitch shift effect is attached while it runs, with its pitch at 1/1.75, so voices keep their pitch.
  - The timed sets and lane events it passes fire on the way, as in normal play.
  - If the spiel ends during it, it stops there; if a next spiel starts during it, that spiel fast-forwards too.
- **The hush, as the original** (`-[SoundChannel hush]`, 0x10002f4e0): FMOD's parametric EQ on the music and the three ambiences, centred on 1250 Hz with a bandwidth of 5, going to -12 dB. It is a counter, so nested hushes need as many unhushes, and it never touches the spiel or the idle loop. The speed of its ramp is checked in the code before it is built.
- **Other fades, as the original has them:**
  - The title music fades out over 3 seconds when the story starts.
  - The story group fades out over 2 seconds and in over 1 second (`+[Sound fadeOutStoryChannelGroup]`, 0x1000225d4; `fadeInStoryChannelGroup`, 0x100022690).
- **Pausing pauses every channel together**, and resumes them together.
- **Lengths and positions come from FMOD**, which knows a stream's length and position exactly.
- **Three volumes** (the dev, 2026-10-19: "I like that."):
  - **Master,** Shift+Home louder and Shift+End quieter: everything together ([[foundation_plan]]). The spiel follows only this one, so the story's voices are never quieter than its backgrounds.
  - **Backgrounds,** Page Up louder and Page Down quieter: the music, the three ambiences and the idle loop.
  - **Interface,** Shift+Page Up louder and Shift+Page Down quieter: the system sounds and the recorded choices.
  - Each press says the new level, and the game remembers all three. The original had no volume settings.

## Open questions

None.
