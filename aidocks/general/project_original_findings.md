---
name: project_original_findings
description: "What the original iOS Heathcote bundle in game/ contains: data format, script grammar, runtime classes, audio, and what to drop."
metadata:
  node_type: memory
  type: project
---

Findings from the first read-only survey of `game/` (2026-10-19). Claude changes `game/` only when the dev asks, as with the extensions and English names of the recordings.

## The dev's layout of game/ (reorganized 2026-10-19)
- `game/data/Audio/story/`: 206 of the story recordings (were `game/Documents/`), all MP3, in five folders by kind: `scene/`, `speech/`, `ambience/`, `idle/` and `music/`. The dev named `scene/` and `speech/` on 2026-10-19. Each has its English name from its record; the old id of each is in [[project_audio_names]].
- `game/data/Audio/System/menu/`: the seven `menu-*` interface sounds.
- `game/data/Audio/System/misc/`: the other seven interface sounds, plus `bugfound.mp3` and `thonk.mp3` (were `game/Audio/`).
- **Every recording is MP3** (the dev converted them all on 2026-10-19: "I was able to convert every sound to mp3, even in the system folder"). The original formats were 148 MP3, 61 WAV and 12 AAC `.m4a`. The data's `original.name` still gives the old extension.
- `game/data/text/story/`: the 606 record JSON files.
- `game/data/text/system/`: `Heathcote v1.01.bundle.json` and `ReadMe.txt`.
- `game/images/story/`: the 48 story graphics (24 ids, each `.png` and `@2x.png`). The dev moved the images out of `game/data/` on 2026-10-19, so `game/data/` holds only what the game reads.
- `game/images/system/`: the 22 interface images (were `game/Images/`).
- `game/certificate/`: the four `.der` certificates.
- `game/scripts/`: the three stray source files.
- The app binary, `Info.plist`, icons, `Base.lproj/` and `_CodeSignature/` stay at the top of `game/`.
- Every file the story data references resolves in this layout; checked 2026-10-19.

Paths below that say `game/Documents/` now mean the folders above.

## The bundle
- `game/` is the iOS .app bundle of Heathcote 1.01, by Fabulae Obscurae (Mike Dean), built 2015-2016 with Xcode 7.2 for iOS 9.2.
- Bundle id `com.fabulaeobscurae.heathcote`.
- `game/Heathcote` is a thin arm64 Mach-O (not fat). `LC_ENCRYPTION_INFO_64` cryptid is 0, so it is not FairPlay-encrypted and can be disassembled.
- No downloads are needed: every recording is in the bundle (about 97 MB in `game/Documents/`).

## The story data is all JSON
- `game/Documents/` holds an export from a web authoring tool (Meteor-style 17-character ids).
- `Heathcote v1.01.bundle.json` is the master index:
  - `labels`: softRef id to a readable name (362 entries).
  - `assets`: category to {softRef id: record id}.
- Each record is `<id>.json`. A record's `file` field names the media file, which is the bare id with no extension. Graphics are the exception: `<id>.png` and `<id>@2x.png`.
- Asset categories and counts:
  - `actions` (91): the menu choices.
  - `actionSpiels` (104): the story recordings.
  - `systemVoice` (67): spoken menu labels and prompts, each with `transcript` and `whisper`.
  - `variables` (23): records hold only notes; values are strings.
  - `ambience` (21), `bgm` (2), `idleLoops` (15), `systemSounds` (14), `graphics` (24).
  - `recaps` (1): broken. Its record `iRRuxKjogQweYZQWS.json` holds the text "No such collection" and is not JSON.
  - `describes`, `describeSpiels`, `recapSpiels` and `orphanSpiels` are empty.
- Every audio file referenced exists. Formats: 148 MP3, 61 WAV, 11 M4A, plus `game/Audio/thonk.m4a` and `game/Audio/bugfound.wav`.
- The 11 M4A files are `go in`, `darkness`, `offices and cells`, `rats`, `what was the question?`, `email`, `spiders`, `enough already`, `basement and kitchens`, `clowns` and `we're losing you`.

## Script grammar
- An action has:
  - `if`: {variable: value}, all must match.
  - `order`: int, its place in the menu.
  - `systemVoice`: the spoken label.
  - `actionSpiels`: exactly one spiel in every action.
  - `burnAfterReading`: bool, the choice goes away once used.
  - `set`: always empty on actions.
- A spiel has:
  - `file` and `transcript`.
  - `set`: a list of {at: seconds, set: {variable: value}}, applied as playback passes each time.
  - `next`: a list of {if, softRef}, the conditional follow-on spiel.
  - `idleLoop`: the loop that plays after the spiel ends.
  - `bgm`, and `ambience` or `ambience1` to `ambience3`: lists of {at, fadeTo: {duration, softRef}} or {at, fadeOut: {duration}}.
- Key variables:
  - `lockout`: 1 blocks the actions menu during a spiel.
  - `waypoint`, `location` and `where you at?`: they drive which "where you at?" choice is offered.
  - `end`: nonzero means the story is over.
  - `fear`: clowns, spiders or darkness. It picks the ending.
  - `cellphone`, `landline` and `flashlight`.
- Transcripts are full radio-script text (MARTIN:, DAVID:, [SFX: ...]).

## Runtime, read from binary strings only so far
- States: `StateManager` with `IdentState`, `PreflightState`, `TitleState`, `TitleMenuState`, `PlayState`, `ActionsDialState`, `PausedState`, `WaitState` and `EndState`.
- Controls were swipes:
  - Swipe up opens the actions dial; rotate to choose; swipe up to accept.
  - Swipe down pauses, and again exits.
  - Rewind and fast-forward are swipes (`spotRewind`, `startRewind`).
  - A two-finger tap describes the current state.
- Audio is FMOD 1.7 (fade points, channel groups, story channel group fade, a "muffle" effect).
- It speaks through the system synthesizer, with a "Bypasses VoiceOver" option.
- Saves use NSUserDefaults (`appState`, `vals`, `resetGameState`, `spielStartSoftRef`, the opening ambience and bgm softRefs).
- Lockout has a grace period (`isInLockoutGracePeriod`, `menu-lockout-ended`).
- `menu-reminder` and `remindedThatSpielHasEnded`: nudges when the player idles.
- The book view (`book-open`, `book-pageturn-1` to `-7`) shows the credits and journal.
- Drop in the port: Crittercism crash reporting, Amplitude analytics, the rate-me alert, the bug report (`bugfound.wav`, `Bug.png`), and the location services.
- `game/Images/` also has three stray source files (`MockPhoneView.h`, `MockPhoneView.m` and `PreflightCard2View.h`). The last one lists the tutorial card steps.
