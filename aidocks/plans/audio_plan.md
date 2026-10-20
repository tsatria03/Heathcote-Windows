---
name: audio_plan
description: "Plan 3: playing Heathcote's sound through FMOD, as the original did: the spiel, the music and three ambience lanes with their timed crossfades, the idle loop, the system sounds and spoken choices, rewind, fast-forward with its pitch kept, the hush and the volumes, matched to the original's numbers."
metadata:
  node_type: memory
  type: project
---

**Status:** being built (the dev, 2026-10-20: "yes", to starting section 1). Section 1 is confirmed ("Yes go ahead."); section 2 is built and waits for the dev's word.

## Progress

- **Section 2, built 2026-10-20, waiting for the dev's word:**
  - **`heathcote/platform/spiel.py`, the `SpielPlayer`, owned by `Audio` as `audio.spiel`:**
    - **The spiel:** opened as a stream, with its exact length, position, seek, pause and resume.
    - **Rewind:**
      - the `rewind` interface sound
      - a jump back of 1 second every 7 ticks for 45 ticks, the first at once, so 7 jumps
      - at the beginning, it stops early and fades the sound out over 0.75 seconds
    - **A finished spiel** restarts 1 second before its end. This was read on 2026-10-20: `-[SoundChannel setPositionBeforeEnd:]`, 0x10002eda0, adds -1000 milliseconds to the length.
    - **Fast-forward:**
      - 1.75 times speed for 90 ticks, with FMOD's pitch shift at 1/1.75 and 2 channels
      - pressing again starts its time over
      - it carries into a spiel started during it, and stops where a spiel ends, with one frame's grace so the story engine can start the next spiel first
    - Both hold their time through a pause. `stop_effects()` ends either and plays on, as the original's tap did.
  - **Two pitch shift findings,** checked against the DLL. pyfmodex numbers the effect's settings wrongly for 2.02: it puts Max channels at 4, but the DLL has it at 3. And every setting is a float in 2.02. So the game finds settings by name, and sets the channel count as a float.
  - **`Audio.pause_story()` and `resume_story()`** pause the story group, the spiel with the background lanes, and leave the system group, so the pause sounds can play. Whether pausing should instead hush the backgrounds and leave them playing, as the original did, is a question for the dev.
  - **`audio_check.py` gains the spiel:**
    - Comma and Full stop choose among the 103 recorded spiels, 10 at a time with Shift, and 3 plays or stops it.
    - Left rewinds and Right fast-forwards.
    - P pauses and resumes, with the pause sounds, and Tab says the position.
    - Choosing an interface sound moves to the bracket keys.
  - **`tests/case/test_spiel.py`, 11 tests.** They found two bugs, fixed before commit: rewind's 7-tick sum drifting a frame late, and the channel count set as a whole number. The suite passes, 87 tests.
  - **To test by ear:**
    - **Mandatory:**
      - fast-forward keeps voices at pitch
      - rewind sounds right, including at the beginning
      - pause and resume stop and bring back the spiel and the ambience together
    - **Optional:** a second fast-forward press restarts its time.
- **The data folder was renamed** by the dev on 2026-10-20, from `game/data/` to `game/documents/`. The game follows it through `DATA_FOLDER` in `heathcote/paths.py`.

- **Section 1, confirmed by the dev 2026-10-20 ("Yes go ahead."):**
  - **`heathcote/game/storydata.py` holds the rules for reading the story data and finding recordings**, moved out of `tools/story.py`, which now imports them. The game and the tool cannot disagree. The tool's report and the written script are unchanged. `sound_path(category, label)` finds a recording by label, such as `('bgm', 'title')`.
  - **`heathcote/platform/audio.py`:**
    - **Starting FMOD:** `load_pyfmodex()` sets `PYFMODEX_DLL_PATH` before the import. A missing `fmod.dll` stops the game with a message saying where to copy it from.
    - **No sound:** `HEATHCOTE_NOSOUND`, or no sound device, starts FMOD's no-sound output, and the game carries on.
    - **The groups and slots:** the master, story and system groups, and the nine slots of `SLOTS`, the original's channels. Each slot plays one recording at a time.
    - **Streams and samples:** the looping slots (music, ambiences, idle loop, title) open streams. The others load samples. All are 2D, and use FMOD's accurate time.
    - **Fades** are FMOD fade points on the mixer clock. A fade-out ends with FMOD stopping the channel to the sample, then it is freed.
    - **Volumes:** `gain()` makes 6 dB per 10 percent, with 0 as silence. The master sets the master group. Each slot follows one other volume: backgrounds, interface or title. The spiel follows only the master.
  - **`heathcote/app.py`:**
    - opens FMOD in `run()`, updates it every frame, and closes it at the end
    - `volumes_changed()` now applies the volumes
    - `play_sound(label)` plays an interface sound on the sfx channel
  - **`app.title_music` is still the stand-in flag the main menu sets.** The menus plan starts the title music and ties the flag to it.
  - **`tests/case/_quiet.py`** sets `HEATHCOTE_NOSOUND`.
  - **`tests/interact/audio_check.py`, at its section 1 stage:**
    - 1 starts or stops the title music, and 2 the ambience loop, each fading in and out.
    - Up and Down choose among the 21 ambiences.
    - Left and Right choose among the 14 interface sounds, and Space plays one.
    - Shift+Home and Shift+End set the master volume, and Page Up and Page Down the backgrounds.
    - Shift+Page Up and Page Down set the interface volume, and Control+Page Up and Page Down the title volume. The tool needs both title and background keys at once, so the title volume moves to Control here.
    - Enter says what is playing and every volume.
    - It keeps its own save.
  - **`tests/case/test_audio.py`, 11 tests:**
    - the steps, FMOD starting silently with the original's channels, and the missing-DLL message
    - every interface sound, both musics and every ambience found
    - the shared rule
    - looping, one recording per slot, each volume on its own channel, fade-outs stopping, and fade levels
    - the App's interface sounds and volumes
  - The whole suite passes, 76 tests. The tool's pieces were also driven silently.
  - **To test by ear,** with `python tests\interact\audio_check.py`:
    - **Mandatory:**
      - the volume steps sound even, and 0 is silent
      - each volume changes only its own sounds
      - the loops come round seamlessly
    - **Optional:** every interface sound plays.
  - **The dev's ear tests passed** (2026-10-20: "all 3 hering tests past. No silent gaps."): even steps, each volume on its own sounds, and seamless loops.
  - **`Title.mp3` fades out by itself in its last seconds.** The dev noticed it fading with no key pressed. Decoded silently and measured in 2-second stretches, it holds about -23 dB to 70 seconds, then falls to -40.6 dB by 74 seconds and -73 dB at its end, 75.96 seconds. So each loop fades away and starts again. The original looped the same whole file, with no loop points of its own (`-[GameView titleMusicShouldBePlaying]`, 0x100019594), so it is kept as it is.

Plan 3 ([[reading_original_plan]] lists the order). It stands on [[foundation_plan]] and serves the story engine. Every number below comes from [[project_original_behaviour]], which cites the original's code.

## Built in sections

Each section is confirmed by the dev before the next starts. **`tests/interact/audio_check.py` grows with every section,** so each has something to hear (the dev, 2026-10-19, at the plan's review: "Deffenatly. I do not want to wait untill we do section 4 to use the entire tool."):
1. Starting FMOD, finding recordings, and the channels: playing, stopping, looping, fading and the volumes. `audio_check.py` starts here, playing the system sounds, the title music and an ambience loop, with all four volume keys.
2. The spiel: streaming, its position, pausing, rewind and fast-forward. `audio_check.py` adds a spiel, with rewind, fast-forward and pause.
3. The lanes: the music, the three ambiences and the idle loop, with their timed crossfades, the hush, and setting them up again after a jump back. `audio_check.py` adds the lanes, the crossfades and the hush.
4. `audio_check.py` becomes the whole tool: any spiel, by its label, with its lanes, and its own save.

## Reviewed

Reviewed section by section with the dev on 2026-10-19 ([[feedback_review_plan_sections]]). What the review found:
- **The plan changed after it was written:**
  - There are four volumes, with the title volume.
  - The keys and settings are already built; `App.volumes_changed()` waits for FMOD.
  - `app.title_music` should become true only while the title music really plays.
  - `tests/case/_quiet.py` gains FMOD's no-sound output.
- **pyfmodex is installed and checked** (the dev: "can you try to install the fmod python module? I have python 3.12."). `pip install pyfmodex==0.7.2` worked. A silent check with the no-sound output then did all of these against `vendor/fmod/fmod.dll`:
  - reported version 2.02.35
  - opened `Title.mp3` as a stream and read its length, 76.08 seconds
  - set a channel's frequency to 1.75 times
  - attached the pitch shift effect
  - made a channel group
  - closed cleanly
- **Volumes move in even-sounding steps** (the dev, 2026-10-19: "I want even steps if possible."), not as a straight fraction of the signal:
  - Each 10 percent step is 6 decibels, and 6 decibels halves the signal.
  - So 100 percent is full, 90 percent is half the signal, 50 percent is -30 dB, and 10 percent is -54 dB.
  - 0 percent is silence, set outright rather than as -60 dB.
  - The level each channel gets is its own volume times the master, worked out in decibels.
- **Still to check before section 3:** how fast the hush ramps to -12 dB, in the original's code.

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
- **Four volumes** (the dev, 2026-10-19: "I like that.", then the title volume: "Since the title music plays in a lot of places, there should be a volume for it, called title volume. Page up/down can adjust this, but only when the music plays there. Also, the other volume keys should only work when you are in the actual game."):
  - **Master,** Shift+Home louder and Shift+End quieter: everything together ([[foundation_plan]]). The spiel follows only this one, so the story's voices are never quieter than its backgrounds.
  - **Backgrounds,** Page Up louder and Page Down quieter: the music, the three ambiences and the idle loop.
  - **Interface,** Shift+Page Up louder and Shift+Page Down quieter: the system sounds and the recorded choices.
  - **Title,** Page Up louder and Page Down quieter: the title music alone.
  - **Where the keys work:**
    - The master keys work everywhere, in every menu and in the story, since the master scales everything, the title music included (the dev, 2026-10-19: "you should be able to adjust the master volume from anywhere in the game, not just the story.").
    - The background and interface keys work only in the story, the actions menu included.
    - The title keys work only where the title music plays: the main menu, and Settings or Credits opened from it ([[menus_plan]]).
    - So Page Up and Page Down are the title volume in the menu, and the background volume in the story.
    - The F1 screen takes every key for itself, so none of them work there.
  - Each press says the new level, and the game remembers all four. The original had no volume settings.

## Open questions

None.
