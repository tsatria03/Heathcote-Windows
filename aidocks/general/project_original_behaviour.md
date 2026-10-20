---
name: project_original_behaviour
description: "How the original Heathcote behaves while it plays, read from the binary with tools/dis64.py: the story rules, the sound channels, rewind and fast-forward, lockout, the actions menu, every gesture in every state, the reminders, the title flow and the save. Each fact cites its method and address."
metadata:
  node_type: memory
  type: project
---

The original's run-time behaviour, read from `game/Heathcote` on 2026-10-19 with `tools/dis64.py` and `tools/macho64.py` (plan 1, section 4: [[reading_original_plan]]). The story data itself is described in [[project_original_findings]].

**Why:** the story JSON says what happens, but not how the game plays it: timings, sounds, gestures, lockout and saving live only in the code. Every later plan builds on these facts so the port sounds like the original.

**How to apply:**
- Cite a fact here by its method and address when a plan relies on it.
- Anything under "Not yet confirmed" must be checked with the tools before it is built on.
- Addresses are the binary's own virtual addresses. Rerun a method with `python tools/dis64.py --brief <Class> <selector>`.
- The game ticks 60 times a second, so "N ticks" below is N/60 seconds.

## The clock

### Confirmed from the code
- A `CADisplayLink` drives `-[ViewController tick:]`, set up in `-[ViewController viewDidLoad]` (0x100010cb0), with no frame interval set, so 60 times a second.
- Each tick adds 1/60 second (0.0166667) to the time in the current state: `-[StateManager issueTick]` (0x100022e54).
- `+[Sound tick]` (0x1000208a8) runs the spiel ending, the timed sets and the background lanes every tick.

## Variables and the save

### Confirmed from the code
- There are five stores, made in `+[Vars init]` (0x10002fff4): `config`, `teller`, `story`, `heard` and `actioned`.
- **config** (`+[Vars createConfigDefaults]`, 0x100031f0c), all off by default; developer switches:
  - `showSpielPos`: "Show the playback position of a spiel as it updates".
  - `lockoutOverride`: "Stop lockout from preventing menu openings".
  - `showState`: "Show current state and band count at top of screen".
  - `hideBugMenuButton`: hides the bug report button.
- **teller** (`+[Vars createTellerDefaults]`, 0x1000318a4):
  - `lastVersion` (int, 0), `started` (bool, off: "Has the story been started?").
  - `tutor-cards` (obsolete), `tutor-preflight` (bool, off), `tutor-paused` (bool, off).
  - `tutor-rwnd`, `tutor-ffwd`, `tutor-actions`: capped counts of rewinds, fast-forwards and menu choices, from "0".
  - `spiel`: the softRef of the spiel to resume, "" by default.
  - `opening-bgm`, `opening-ambience1`, `opening-ambience2`, `opening-ambience3`: the softRefs playing on each lane when that spiel opened.
- **story** (`+[Vars createStoryDefaults]`, 0x1000321e4): one string per entry in the bundle's `variables`, every one defaulting to "0".
- **heard** (`+[Vars createHeardDefaults]`, 0x100032460): one bool per `actionSpiels` entry, off.
- **actioned** (`+[Vars createActionedDefaults]`, 0x100032710): one int per `actions` entry, 0: how many times each action has been chosen.
- **Every change is saved at once.** `-[Vars applySetForVar:val:]` (0x100030a34) writes the value to `NSUserDefaults` under "<store>/<name>" and posts a `VarChanged` notification. `-[Vars loadFromSettings]` (0x1000307a8) reads them back on launch, using the default when one is missing.
- A missing variable reads as nothing and logs "Attempted read of nonexistent variable": `-[Vars getVar:]` (0x1000311e4).
- **Setting the story variable labelled `end` to anything but "0" raises the end credits at once**: `-[Vars setString:to:]` (0x100030f48) calls `+[StoryView raiseEndCredits]`.
- **Restart** (`-[ViewController resetGameState]`, 0x100011068) stops every channel, resets `heard`, `story` and `actioned` to their defaults, sets `teller/spiel` to the `start` spiel, empties the four opening softRefs, and sets `tutor-actions` to 0. It is reached from the title's RESTART button, after "RESTART THE STORY?" and "If you tap RESTART, your progress will be lost." (`-[RestartModal restartButtonPressed]`), and after the end credits (`+[StoryView lowerCredits]`).

### Not yet confirmed
- Exactly which stores are keyed by softRef and which by label: `-[Vars initWithPrefix:defaults:]` (0x100030454) sets a flag for `story`, `heard` and `actioned`.

## The story rules

### Confirmed from the code
- **The story starts at the spiel labelled `start`**: `+[Story justStart]` (0x10001a6e0), which also sets `teller/started`.
- **Continue** (`+[Story startTape]`, 0x10001a898): if `teller/started` is on, it replays `teller/spiel` from its beginning; otherwise it starts fresh.
- **The resume point is the last spiel an action opened.** `+[StoryView newTape:]` (0x100024020) saves `teller/spiel` only for a "resumable" tape, and only an action's tape (`+[Story respondToDecision:]`) and the very start are resumable. A spiel reached through `next` is not saved, so Continue goes back to the last chosen action's spiel.
- **The actions menu** (`+[Story actionsMenu]`, 0x10001aaa8):
  - It takes every entry of `actions`.
  - An action shows only if **every** variable in its `if` equals its value exactly, as text, in the `story` store.
  - An action with `burnAfterReading` is left out once its `actioned` count reaches the number of entries in its `actionSpiels`.
  - Each choice carries its `systemVoice` recording and that recording's `transcript`, or the label when there is no transcript.
  - The choices are sorted by `order`, lowest first.
- **Choosing an action** (`+[Story respondToDecision:]`, 0x10001b2e8):
  - It plays `actionSpiels[n]`, where n is the action's `actioned` count, capped at the last entry. Every action in the data has one entry, so it always plays that one.
  - It adds 1 to the action's `actioned` count, and applies the action's `set` to the `story` store.
- **When a spiel ends** (`+[Sound tick]`, 0x100020930 "processSpielEnding"):
  - Its `next` entries are tried **in order**, and **the first whose `if` all match wins**.
  - If none matches, its `idleLoop`, if any, starts looping on the idle loop channel.
- **Timed sets** (`+[Sound tick]`, from 0x100020e3c): each `{at, set}` fires when playback moves forward past `at` seconds. It applies the set to `story` and calls `+[StoryView spielJustSetVariables:]`. Going backwards logs "VAR COMMAND TICK: CAN'T HANDLE GOING BACKWARDS", and nothing is undone.
- **A spiel with no file** is sent to a speech synthesizer with its transcript (`+[Sound playSpiel:]`, 0x100021d4c). That synthesizer is a stub in this build: `+[Sound speak:forSoundChannel:]` (0x1000224b0) only stores the text, `+[Sound isSpeaking]` always says no, and `+[Sound stopSpeaking]` does nothing. So such a spiel makes no sound.
- **Spoken menu labels** (`+[Sound playSystemVoice:]`, 0x100021f38): when the story variable labelled `systemVoice` is "whisper" and the recording has a `whisper` file, that file plays instead. Nothing in the data sets that variable.
- **The `ambience` key is never read.** The lane code reads only `bgm`, `ambience1`, `ambience2` and `ambience3` (`+[Sound tick]`, 0x100020dd4 to 0x100020e30), and the binary holds no bare "ambience" string. Fades listed under a spiel's plain `ambience` key never played in the original.
- `+[Sound pushSpiel]` and `+[Sound popSpiel]` exist but nothing calls them: `python tools/dis64.py --refs pushSpiel` finds no caller, reading every method in full.

### Not yet confirmed
- Whether a spiel reached through `next` is marked heard. `-[PlayState startPlayed]` (0x1000336bc) marks only the last spiel, once nothing more follows.
- After a rewind, whether timed sets fire again on the way forward: the last position (0x100203b90) is compared with the new one, but where it is updated has not been traced.

## Sound channels

### Confirmed from the code
- `+[Sound initEngine]` (0x1000203f0) makes FMOD channel groups "system" and "story" and these channels: `titleBgm`, `spiel`, `bgm`, `idleLoop`, `ambience1`, `ambience2`, `ambience3`, `sfx`, `systemVoice`, `noPreempt` and `spielEnded`.
- **Background lanes** (helper at 0x1000210a8, called per lane each tick):
  - `fadeTo {duration, softRef}` crossfades to the new recording over `duration` seconds and loops it (`playFilePath:toFadeInWithDuration:`, `loop`).
  - `fadeOut {duration}` fades the lane out over `duration` seconds and stops it.
  - After a jump backwards, each lane is set up again cold (`coldConfigureWithFromFilePath:toFilePath:fadeDuration:fadeProgress:`), from the softRef that lane had when the spiel opened, so the right recording is playing at the new position.
- **Opening the story** (`+[StoryView go]`, 0x100025ce8) starts `teller/opening-bgm` and the three opening ambiences, each with a 0.5-second fade-in, looping.
- **Title music**: `-[GameView titleMusicShouldBePlaying]` (0x100019594) loops the `bgm` labelled `title` (`Title.mp3`) on the title channel. `-[GameView titleMusicShouldNotBePlaying]` (0x1000196dc) fades it out over 3 seconds and fades the story group in.
- **Where the title music plays** (found 2026-10-19, after the dev asked whether the menu had music):
  - **The rule:** both are called only from `+[GameView setCarouselPosition:duration:]` (0x100019400). Positions 0 and 1 play the title music, and any higher position fades it out (0x100019460 to 0x100019478).
  - **What sets each position:**
    - 0, the title: `+showTitleScreen` (0x100018fa0), and swiping down from the title menu (`TitleMenuState down`, 0x1000383a4).
    - 1, the title menu:
      - the title moving on after 4 seconds (`TitleState tick`, 0x1000071c8)
      - returning to the title menu from pause (`+[StoryView returnToTitle]`, 0x100025614)
      - leaving the end credits (`+[StoryView lowerCredits]`, 0x1000264d8)
    - 2, the pause screen: `+[StoryView pause]` (0x10002540c).
    - 3, the story: entering it from the title menu (`TitleMenuState up`, 0x100038464), and `+[StoryView unpause]` (0x100025564).
  - **So:** the title music plays under the title and the title menu, the original's main menu. It is silent while paused and during the story, and starts again whenever the player goes back to the title menu, from pause or from the credits.
- **Story group fades**: `+[Sound fadeOutStoryChannelGroup]` (0x1000225d4) goes from 1 to 0 over 2 seconds; `+[Sound fadeInStoryChannelGroup]` (0x100022690) goes from 0 to 1 over 1 second.
- **Hushing** (`+[Sound hushBackgrounds]`, 0x1000223b8; `+[Sound unhushBackgrounds]`, 0x100022434): a counter, so nested hushes need as many unhushes. The first hush calls `hush` on `bgm`, `ambience1`, `ambience2` and `ambience3`; the idle loop and the spiel are not hushed.
- **What `hush` does** (`-[SoundChannel hush]`, 0x10002f4e0): it adds an FMOD effect of type 12 (parametric EQ) with centre 1250 Hz, bandwidth 5 and gain 0, and stores -12 as a target. So the backgrounds are muffled around 1250 Hz, by up to 12 dB.
- **The hush's ramp** (confirmed 2026-10-20). `hush` stores a step of -0.796875 dB (0x10002f600) and its target of -12 (0x10002f618); `unhush` stores a step of +0.5 (0x10002f6bc) and a target of 0. Each tick, `-[SoundChannel tick]` (0x10002f6e0) works the ramp:
  - it adds the step to the gain (0x10002f750)
  - when the gain passes the target, it sets the gain to the target and the step to 0 (0x10002f794)
  - when that target is 0, it removes the EQ (0x10002f7d4)
  - it sets the EQ's gain, parameter 2 (0x10002f800)
  
  So hushing takes 16 ticks, about a quarter of a second, and unhushing 24 ticks, 0.4 seconds.
- **System sounds** play from `systemSounds` by label; a missing one logs "Missing systemSound": `+[Sound playSystemSound:onChannel:]` (0x10002219c).

### Not yet confirmed
- The channel volumes: no volume settings were found.

## Rewind and fast-forward

### Confirmed from the code
- **Rewind** (`-[PlayState startRewind]`, 0x1000333cc; `-[PlayState tick_rewind]`, 0x100033248):
  - It plays the `rewind` system sound.
  - Every 7 ticks it jumps back 1 second (`+[Sound spotRewind:]` with 1.0).
  - It stops after 45 ticks (0.75 seconds), about 7 jumps, then plays on.
  - If it reaches the beginning, it stops early and the `sfx` channel fades out over 0.75 seconds.
- **Rewinding a spiel that has ended** (`+[Sound spotRewind:]`, 0x1000222cc) stops the idle loop and replays the spiel from just before its end (`-[SoundChannel spotRewind:]`, 0x10002ee7c, uses `setPositionBeforeEnd:`).
- **Fast-forward** (`-[PlayState startFfwd]`, 0x100033544; `-[SoundChannel startFastForward]`, 0x10002f348):
  - The spiel plays at 1.75 times its speed (0x10002f3e0).
  - **Voices keep their pitch.** A pitch shifter, which the code's own log calls the "chipmunk-suppression DSP", is attached while it runs (0x10002f40c). It is made in `-[SoundChannel initWithName:channelGroup:streamer:muffler:pitchShifter:preempts:]` (0x10002e2fc) as FMOD effect type 13 (pitch shift), with its pitch at 0.571429, which is 1/1.75 (0x10002e4e4), and 2 channels (0x10002e514).
  - It stops after 90 ticks (1.5 seconds), then plays on.
  - Swiping again while it runs restarts the 90 ticks.
  - If the spiel ends during it, it stops and the spiel counts as ended.
  - If a `next` spiel starts during it, that spiel fast-forwards too (`+[Sound tick]`, 0x100020d9c).
- A tap during rewind or fast-forward stops it and plays on: `-[PlayState tap]` (0x100033c90).

## Lockout

### Confirmed from the code
- **Opening the menu** (`+[StoryView raiseActionsDial]`, 0x100024204):
  - It opens when `lockout` is "0", **or** when the spiel last played has been heard before.
  - Otherwise, with `lockoutOverride` off, it plays `click-bad` then `menu-unavailable`, raises the padlock, and starts a 1.5-second grace timer (0x100024560).
  - With `lockoutOverride` on, it plays `menu-unavailable` and opens anyway.
  - When it opens: `click-good`, the padlock lowers, the backgrounds are hushed (once), the spiel pauses, and the state becomes `ActionsDialState`.
- **During the 1.5-second grace**, swiping down does not pause: it plays `click-bad` and shows that lockout cannot be ended (`-[PlayState down]`, 0x100033a40; `+[StoryView isInLockoutGracePeriod]`, 0x1000245d0).
- **When a timed set changes `lockout`** (`+[StoryView spielJustSetVariables:]`, 0x1000256f4): going to "0" opens the padlock bolt and plays `menu-lockout-ended`; going to "1" closes it.
- **When a spiel ends with nothing to follow**, `lockout` is set to "0", `menu-available` plays, and the spiel is marked heard (`-[PlayState startPlayed]`, 0x1000336bc).

## The actions menu

### Confirmed from the code
- It is built from `+[Story actionsMenu]` each time it opens (`-[StoryView makeActionsDial]`, 0x100023c38). It plays `menu-open` when shown (`-[Dial show]`) and `menu-close` when hidden (`-[Dial hideAndDestroy]`).
- It opens on the first choice, the lowest `order` (`-[Dial configure:]`, 0x10000dac0, sets position 0).
- **It wraps**: the choice is the position modulo the number of choices (`-[Dial getDialChoiceIndex]`, 0x10000e984).
- **Each move announces the choice** (`-[Dial setDialPos:]`, 0x10000eda0, calls `announcePos`). `-[Dial announcePos]` (0x10000eb30) plays its `systemVoice` recording when it has a file; otherwise it sends the transcript to the stub synthesizer, which is silent.
- Gestures (`ActionsDialState`):
  - Swipe left: `click-good`, next choice (+1). Spoken description "To next action".
  - Swipe right: `click-good`, previous choice (-1). "To previous action".
  - Swipe up: `click-good`, accept. "To accept this action".
  - Swipe down: `click-good`, close the menu. "To close actions menu".
  - Tap: `click-bad`, then the choice is announced again with a hint (`showSwipeHint`, 0x1000381a8).
  - Two-finger tap: "Actions menu is open."
- **After 420 ticks (7 seconds) with no move**, the choice is announced again with the hint, and the count starts over (`-[ActionsDialState tick]`, 0x100037de0).
- **Accepting** (`+[StoryView acceptFromActionsDial]`, 0x10002477c): `menu-accepted` plays (`-[Dial accept]`, 0x10001004c), the backgrounds are unhushed, the action is applied, its spiel starts as a new tape, and play resumes after 0.25 seconds in `WaitState`.
- **Closing** (`+[StoryView lowerActionsDial]`, 0x10002462c): the backgrounds are unhushed, the spiel unpauses, and the state is `PlayState` again.
- Losing focus with the menu open closes it, plays `lost focus`, and pauses (`-[ActionsDialState blur]`).

## Playing (PlayState)

### Confirmed from the code
- Sub-states: play, rewind, fast-forward, ended ("played") and paused.
- Gestures:
  - Swipe up: open the actions menu. "To open actions menu if available".
  - Swipe down: `click-good` and pause, except during the lockout grace. "To pause. Again to exit."
  - Swipe left: `click-good` and fast-forward. "To fast forward".
  - Swipe right: `click-good` and rewind. "To rewind".
  - Tap: during rewind or fast-forward, stop it; otherwise `click-bad`. After an ended spiel, the 3rd tap hints that the menu can be raised, and the 4th opens the pause instructions (`-[PlayState tap]`, 0x100033c90).
  - Two-finger tap: "Story is at end of scene." once the spiel has ended, otherwise "Story is playing." (`-[PlayState voiceover]`, 0x100033de8).
- **After a spiel ends**, `menu-reminder` plays every 420 ticks (7 seconds) until something happens (`-[PlayState tick_played]`, 0x100033194).
- Losing focus: `lost focus` plays and the story pauses (`-[PlayState blur]`, 0x100033d98; `-[AppDelegate applicationWillResignActive:]`).

## Paused (PausedState)

### Confirmed from the code
- Pausing (`+[StoryView pause]`, 0x1000252cc): the backgrounds are hushed (once), `pause-pause` plays, the spiel pauses, and `tutor-paused` is set.
- Swipe up: `click-good` and unpause. "To unpause". Unpausing (`+[StoryView unpause]`, 0x100025484) unhushes, plays `pause-unpause`, and resumes the spiel.
- Swipe down: `click-good` and back to the title menu, the story left paused. "To exit story".
- Swipe left, swipe right or tap: `click-bad`.
- Two-finger tap: "Story is paused."

## Opening, title and end

### Confirmed from the code
- **Developer splash** (`IdentState`): plays the `ident` system sound. Swipe up skips it with `click-good`; other gestures give `click-bad` (0x10003e6bc onwards).
- After it, if `tutor-preflight` is not yet set, the first-run tutorial (`PreflightState`) shows; otherwise the title shows (0x10003e7c4).
- **Tutorial texts**: "Heathcote is a responsive story told through Sound. Headphones are strongly recommended.", "For the most immersive experience, try playing with your eyes closed.", "Control the story by swiping, not tapping.", and "Double-tap to continue."
- **Title** (`TitleState`): moves to the title menu by itself after 240 ticks (4 seconds) (`-[TitleState autoAdvanceAfterDelay]`, 0x100007304). Swipe up or tap moves at once with `click-good`; the rest give `click-bad`.
- **Title menu** (`TitleMenuState`):
  - Swipe up: `click-good`, enter the story (`+[StoryView go]`): unpause a paused story, or else start or continue.
  - Swipe down: `click-good`, back to the title.
  - Swipe left, swipe right or tap: `click-bad`.
  - Two-finger tap: "Swipe up to enter story".
  - The title screen reads "START" ("Start story") or "CONTINUE" ("Continue story from chapter: '<location>'."), where <location> is the story variable `location`, plus a RESTART button.
- **End** (`EndState`), after `end` is set (`+[StoryView raiseEndCredits]`, 0x100025b10):
  - Two-finger tap: "Story has ended. Credits are onscreen. Swipe down to return to menu."
  - Swipe down: `click-good`, then `+[StoryView lowerCredits]` (0x1000264a8) resets the story, returns to the title menu, and offers "Want more?" ("Nah" or "Yes please!", which opens a web page).
  - Other swipes give `click-bad`.

## VoiceOver gestures

### Confirmed from the code
- With VoiceOver running, a two-finger swipe announces what that swipe does in the current state, and a two-finger tap announces the state (`-[GameView gotUp2]` to `gotTap2`, 0x1000189b4 to 0x100018c04).

## On-screen hints (the Tutor)

### Confirmed from the code
- These are mostly visual instructions, timed with one timer (`-[Tutor fireTimerAfter:cmd:]`, 0x100036b78).
- After a spiel ends, a "swipe up for options" hint follows after 3.5 or 10 seconds, the shorter while fewer than 3 choices have been made (`-[Tutor spielEnded]`, 0x100036530).
- After the menu opens, a "swipe up to select" hint follows after 2 seconds (no choices made yet), 3.5 seconds (one made) or 10 seconds (`-[Tutor actionsDialRaised]`, 0x1000365c0).
- The rewind and fast-forward labels show only for the first 4 uses (`tutor-rwnd`, `tutor-ffwd`).

### Not yet confirmed
- The exact choice between 3.5 and 10 seconds in `-[Tutor spielEnded]`: it compares `tutor-actions` with 2.
