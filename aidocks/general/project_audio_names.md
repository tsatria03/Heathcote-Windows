---
name: project_audio_names
description: "Where each story recording now lives: its English file name under game/data/Audio/story/<kind>/, and the original id the story data names it by."
metadata:
  node_type: memory
  type: project
---

On 2026-10-19, once the dev had converted every recording to MP3, each story recording was renamed from its bare id to its English name, taken from its record's `original.name`, and moved into a folder for its kind. The dev asked for it: "Is it possible to rename the jibrish audio files to there english counterparts, according to the json files?", then "Yes. Let's do it that way."

**Why:** the dev does not like names with no meaning or extension. The folders keep apart names that clash across kinds, such as `rats.mp3` in `scene/` and in `speech/`.

**How to apply:**
- The story data still names every file by its id. The game finds a file by following the id to its record, taking `original.name`, swapping its extension for `.mp3`, dropping any character Windows does not allow, and looking in the folder for the record's bundle category.
- The folder for each bundle category, as the dev named them on 2026-10-19:
  - `actionSpiels`: `scene/`
  - `systemVoice`: `speech/`
  - `ambience`: `ambience/`
  - `idleLoops`: `idle/`
  - `bgm`: `music/`
  - `systemSounds`: `game/data/Audio/System/menu/` for the seven `menu-*` sounds, and `game/data/Audio/System/misc/` for the other seven, so the game looks in both
- The folders above are under `game/data/Audio/story/`, except the interface sounds'.
- The two app sounds, `bugfound.mp3` and `thonk.mp3`, are also in `game/data/Audio/System/misc/`; neither is in the story data.
- One name lost a character: `what was the question?` is now `what was the question.mp3`.
- Each line below reads: new name, then the original id.

## scene/: the story recordings (actionSpiels), 103 files

- `basement and kitchens.mp3`: 6XKCiH4XQuiDrXwZQ
- `call opening.mp3`: KJKwxSfbzEHPK3rBT
- `cant revisit 1.mp3`: cNfE7HuRanLf44usg
- `cant revisit 2.mp3`: d7YFrfno9PtJii3BB
- `cellphone (2 bars).mp3`: 54tiwJoPDRMxDsmw5
- `cellphone (25% battery).mp3`: fu98SrDxwSTyWogTz
- `cellphone (3 bars).mp3`: 8SWCmRF5r3M3vzJhC
- `cellphone (50% battery).mp3`: Wv2ABJ863rXBPiv93
- `cellphone (dropped call).mp3`: 352LmZhzG9q4J6eRW
- `cellphone (records room).mp3`: Cuh6F6p2Y8CdTNok2
- `cellphone (rotation 1).mp3`: kDukmhMZob4LALNPF
- `cellphone (rotation 2).mp3`: z7rpfvwb5FzkhZWp8
- `cells.mp3`: fzbCMmxQ3sBnHzsaD
- `check email.mp3`: jvQaTg7cdpvvLAqt3
- `clearing.mp3`: FaZBWYsw6AGG7GSdu
- `closed cells.mp3`: Rm9fnZBPPsqSyPX62
- `commercial reflection.mp3`: nkCP3Rs5tkE7sLXKJ
- `commercial.mp3`: m93sZNEqfMrgthkn2
- `Crazy Ralph (cold).mp3`: qibREYf2wFSArTyxw
- `Crazy Ralph (warm).mp3`: YxcCttMTcRdXuWGbh
- `Crazy Ralph.mp3`: vz8yvEsYCCugTcvHT
- `David's fear.mp3`: 4cu8uFpLgJmvJNSqP
- `doctor's office.mp3`: B3LpQqgWynFcCmoox
- `doctors notebook.mp3`: 9FMdcqMbySEGiDMTd
- `dual calls (answer landline).mp3`: nFCdzGvtAgysfFd9M
- `dual calls (landline).mp3`: jhqDuWkS48C2quZjZ
- `dual calls (switch to cell).mp3`: qKGzF6JrSRXmM4F8E
- `east wing (blocked 1).mp3`: QGa3E4LisMzJD9Cb9
- `east wing (blocked 2).mp3`: Ex8bZrdtcsoEok5xr
- `east wing (blocked 3).mp3`: ZCZvDkaSSTFYwoMQB
- `ending (clowns).mp3`: RpkudMxPpvodpdwzw
- `ending (commercial).mp3`: SFhLNZddx3CraLPZw
- `ending (darkness).mp3`: qcRqwLKporMeoe7qF
- `ending (spiders).mp3`: SqGshvk9nm2W8xQ8Q
- `enter from outside.mp3`: XHqbHzAiSzGkptQzc
- `escape 1.mp3`: HrM9Xr9QEnPqfaYjg
- `escape 2.mp3`: CenZh6FQ9KtFLFErz
- `examination room.mp3`: NvTpvnhzRuryMDZDN
- `fallen.mp3`: nZi2uxjSYMsGbCqae
- `fear of the dark.mp3`: K5Lqv5rvacj3SYTGT
- `filing cabinet.mp3`: pPXeedoannBRq7YqP
- `flashlight (hint).mp3`: ndhW2wmCwR753PbWH
- `flashlight (just broke).mp3`: Shimks46Jzr8Sr8NQ
- `flashlight (records room).mp3`: pTSmB5toSvBJzfPfx
- `foyer revisited.mp3`: KjKdakJTo6nHnAQ2F
- `go back (clearing).mp3`: wGhTADeZCz9Etv6Z5
- `graffiti.mp3`: vsaAtFwQFRNKmL63z
- `hallway graffiti (clowns).mp3`: tS536dPko6yYomCTz
- `hallway graffiti (darkness).mp3`: 7dza6jC3TWpnPjtsJ
- `hallway graffiti (spiders).mp3`: rcZFrGMsS8YAGLo5g
- `hallway.mp3`: 9NmXirSvfJiwPyGH2
- `handwritten note.mp3`: GThCLBGSxs74kLF6S
- `I fear clowns.mp3`: akCd7MBzp5HwgDict
- `I fear darkness.mp3`: Z4FzLLKC72NomdMR8
- `I fear spiders.mp3`: N3oskSoWCndTfXJX9
- `journal.mp3`: GM8muZXAX9mnJ6ZCp
- `Judith 1.mp3`: kY8nERNC7QPTwzHuB
- `Judith 2.mp3`: jcGN33D5jvWbHntJr
- `Judith 3.mp3`: zfGfAbuswWbrn6F7W
- `keep going (clearing).mp3`: d4Sa5bRoDsLP7qED6
- `landline (dropped call).mp3`: TiXsh2uLrz8yK7HDm
- `offices (end).mp3`: Wn4jCLew9AEgnDkxh
- `offices revisit.mp3`: MpfoFZmxwZ8jyqGQR
- `offices.mp3`: XcpdFvwy6NsEXsx2h
- `open cell.mp3`: xwokajfjqpzweNNYW
- `Operation Paperclip.mp3`: cYMtjQuuwNKPGjt3q
- `painting.mp3`: ZaEHmEoeerEHM4N3c
- `rats.mp3`: h8mPiQJJH8y3xEKtX
- `records room (move on).mp3`: PjW3rDJrmsqh5cMJ9
- `records room.mp3`: RZBN8sBd9DJ88Z6jJ
- `repeat question (fear).mp3`: cTusHjh4Qoq3XnZix
- `research Kaufer.mp3`: jsySozaabYqbMmSQW
- `self-opened door.mp3`: 3FTdjvZcKH5mFJAhH
- `shrine.mp3`: QKu65dhQtMnXPpFsY
- `shut door (clowns).mp3`: eJq9ytZtrqsLibwi9
- `shut door (darkness).mp3`: KFtaj2qTFEQiNLtoe
- `shut door (end).mp3`: D2LJZQJRRSE6Y8NsZ
- `shut door (spiders).mp3`: wmiRRdm3KsZFi4yaf
- `smoke.mp3`: WAH2ZeP3yGpbw9c9X
- `spiel 1.mp3`: iBDTHu7EimAgjiTwf
- `spiel 2.mp3`: 74Jq48X2cTrw5pdGd
- `spiel 3 (clowns).mp3`: igBuXyYH4mZpKmQcZ
- `spiel 3 (darkness).mp3`: QbvH5A2LQp8CMaCXj
- `spiel 3 (end).mp3`: 7CXfoQgeHppfuCMgk
- `spiel 3 (spiders).mp3`: vaNfK3d7NAJjBD5wZ
- `spiel 3 (start).mp3`: NtiXp8xMx6XPeXiCi
- `start recording (passage to east wing).mp3`: Bj9uQwFqe8GATf4QH
- `start.mp3`: 5YN9k5GuMDhuHfTFv
- `typewriters.mp3`: gTt77eHzRyuMQW9Fk
- `where you at (cell block c - not windy).mp3`: ubunxwKTTXv6vMRHT
- `where you at (cell block c - windy).mp3`: gg2fFXzXgeNDopnKa
- `where you at (doctors office).mp3`: u9ggt3C78NaumahBd
- `where you at (during spiel).mp3`: i2rPYcqNzsxGMi6FS
- `where you at (examination room).mp3`: bGBfsBzkEETTFnH45
- `where you at (foyer).mp3`: fcbjNZsHAdxcxJ7Ld
- `where you at (inside entrance).mp3`: Z73obP7jRZpXoZsrt
- `where you at (offices 1).mp3`: xTxSzZTj8Taa2KDk8
- `where you at (outside entrance).mp3`: vaELAwyhPhSB2Z3c4
- `where you at (passage to east wing).mp3`: xyXJXAARs5QRFBSNH
- `where you at (path).mp3`: Px2GcsPYSZy3GdMei
- `where you at (records room, no light).mp3`: NvZSTsoPLHZHvLedN
- `where you at (typewriter room).mp3`: 9dPCQrEuFHE6sAoGL
- `where you at_ (records room - light).mp3`: Z7P9pF2LQbvwEcPgw

## speech/: the spoken menu labels and prompts (systemVoice), 65 files

- `afraid of the dark.mp3`: HYJx6yWH2SGWN8Xb9
- `basement and kitchens.mp3`: dMix5jpAN2cmXewAo
- `building plans.mp3`: p9FDiw9rKvawmptxQ
- `burning hair (P).mp3`: o4sEH2vgTQs2a8gg3
- `call for help.mp3`: iiQhTbbKAdQxWdXMm
- `cellphone (P).mp3`: 2CPxgbK4bk5YtR9RX
- `cellphone.mp3`: 6ZiPGNgCovYaqCcuf
- `cells (P).mp3`: kwiMzJZXtmZrxxi4x
- `closed cells (P).mp3`: pNYrdfC4rBYnGdmFa
- `clowns.mp3`: DPmudYvPvT2QYhwE6
- `Crazy Ralph.mp3`: rmCyEoizXywLsXJvf
- `darkness.mp3`: dQRy7JyxrJynPq89q
- `David 1 (P).mp3`: PK5ZcW2gSCwhvsf6M
- `David 2 (P).mp3`: y75ndiDtN7822Z3Jp
- `David 3 (P).mp3`: ycWnu85x2CYywycPH
- `David!!.mp3`: 6i2hKWsi2wCLnb8nG
- `David.mp3`: HctC4gWSGwPk8gQFz
- `David_.mp3`: wgQtXCMRL2MMWrXmX
- `Doctor Kaufer (P).mp3`: L7nGGsHozeYAmzaCt
- `doctor's office (P).mp3`: NNQiHKXSBzt5fnehx
- `east wing (P).mp3`: McfSsKyj4Ne5azesf
- `email.mp3`: EgRycwZcNYwBkzXFc
- `enough already.mp3`: Xmf9bhnmtz3G6XSSE
- `examination room (P).mp3`: hWtd2YeexP6dg9zYy
- `flashlight (P).mp3`: eSmS6pwfSKv7fvkvR
- `go back (P).mp3`: wWqAT8JYQHNrRxsan
- `go in.mp3`: 84sHH7b5zZHnxycEd
- `graffiti (P).mp3`: XGMZkudo6v3ELFxjG
- `handwritten note (P).mp3`: tJNXZyLkFG7fbcsQ6
- `head back (P).mp3`: rpsHEL3vnwxF9nLtD
- `hear what.mp3`: ss28TmWRrx74LtTeH
- `hurt you (P).mp3`: o3wBS4gMSfrEP9nJA
- `journal (P).mp3`: WXBc632xPAocC3JRt
- `keep going (P).mp3`: 8noiJtrYt2HiXZiEz
- `keep recording (P).mp3`: jvbcn7gcnqFYpq7bv
- `keep walking (P).mp3`: YEkqfx354fHhjhAuW
- `landline (P).mp3`: aiTeuunDzzqazKcJ8
- `landline.mp3`: myBe47kE2vfLFqbtr
- `listen to me (P).mp3`: qAcuK6Er2EBSydk9E
- `listen to me.mp3`: Qja9AqNDuE8pTNXdn
- `notebook (P).mp3`: HebgpChpyGkYSAxth
- `offices (P).mp3`: dSgFWYBK8Jn3iu7eh
- `offices and cells.mp3`: g7TEQg42yJPfJhosf
- `open cell (P).mp3`: 2adMcY4idFk4S7DTh
- `Operation Paperclip (P).mp3`: 3cKZ7XutivSA5Kytf
- `painting (P).mp3`: 49FjC9KjY8yMaWHHA
- `pick up (P).mp3`: 7N68XCpBkEYRK75zm
- `pick up.mp3`: oXyhCrNT9iXiHePgu
- `rats.mp3`: s3wQu7zTAHepoMLu2
- `run (P).mp3`: gAecLTX6rhxsHHXBY
- `run.mp3`: LssnX9fA5Aw6JWCFu
- `shrine (P).mp3`: gHwFGezCyXaJ843SX
- `smoke (P).mp3`: X4YSjduqJZkAnsp4e
- `spiders.mp3`: FopxQswoR7NQyQXTC
- `start recording (P).mp3`: uNXWs4JGesc3QSLzJ
- `typewriters (P).mp3`: RtEdGSkGnCFz3HYv4
- `what was the question.mp3`: iF7Ks4ghwh2GiZMKu
- `what's going on (P).mp3`: Sty9LHYgbwFmbGmqx
- `whats going on.mp3`: JLZPwHFGGJtkxuYwm
- `whats happening.mp3`: 8Emd9wyQCmLemBbsK
- `where are you (P).mp3`: xmqJgRu7tKf5ESTTe
- `where are you.mp3`: rDysXF2Q2DKE76zdA
- `who's there.mp3`: azbvAhCc5nsHqQ2qA
- `you kidding (P).mp3`: i3DCSyadaYA94N8xR
- `you kidding.mp3`: be5AAryhnhxoSniyZ

## ambience/: the ambience tracks (ambience), 21 files

- `cells, windy.mp3`: wAXyJJEEKudZpLTRH
- `east wing less rain.mp3`: o5JHHLPg8caDqb8B6
- `east wing more rain (M-L).mp3`: YtubCp2BMLYszPinh
- `east wing more rain.mp3`: HiRWXtrA52J4vsaPg
- `fire (M-L).mp3`: P34pvnuLtPEY988Pb
- `heartbeat (120bpm, f).mp3`: hhtzkJYTRXLS4Nb2C
- `heartbeat (43 bpm, pp).mp3`: hegbmsEYjwj6Ho2J8
- `heartbeat (43bpm, mf).mp3`: 7D6G5uPXXMBerv5Zm
- `heartbeat (90bpm, mf).mp3`: 7vWQnnkw3F8ex7byh
- `indoors (M-C).mp3`: g5veWkrhu8L5dWifn
- `indoors, calm.mp3`: pDwBYjirk6kLZiFaP
- `indoors.mp3`: TbtmYPXaBLpuhjexQ
- `Judith (M-C).mp3`: 4nCjTJboeGJ62Epn4
- `Judith.mp3`: Y7k9RASauxdFGkBXJ
- `Martin office.mp3`: ACk55ANkaptLbiRNL
- `offices.mp3`: kfZqvvJ42cdm5cNgy
- `outside, calm (M-C).mp3`: RRgaLFNzikYQ5YM77
- `outside, calm (M-L).mp3`: usyujpmwavAxwQxtc
- `outside, stormy (M-C).mp3`: 8SEaTX9LrhB9NyL5f
- `Untitled Session 1_mixdown.mp3`: rP99dF9wofCi8Ts96
- `wind howling thru Martin's landline.mp3`: qftEq8ARGtX2JRnxQ

## idle/: the idle loops (idleLoops), 15 files

- `idle (fire loop).mp3`: dyvaHpvRshuzNnZrK
- `idle loop (dual calls (answer landline)).mp3`: Wb5MhNjRGNCZKZnxe
- `idle loop (dual calls (switch to cell)).mp3`: Bsy5SKrsmq6FsYEst
- `idle loop (escape 2).mp3`: WXk7bPmoeSrM8Qbcx
- `idle loop (flashlight).mp3`: D9nyZFCj5Y2vSCMLf
- `idle loop (footsteps).mp3`: B65HpZkgyFawtFDy9
- `idle loop (inside entrance).mp3`: Q5fh6KNikaj3bu4KZ
- `idle loop (Judith 1).mp3`: yxuNoMC4fjuPPAEcA
- `idle loop (Judith 2).mp3`: pXujDfy3JXbHdME9j
- `idle loop (Judith 3).mp3`: 3uz3W5vo2y4NquWrq
- `idle loop (paper flipping).mp3`: TGi6pTFEoCEsSXHL2
- `idle loop (path).mp3`: QbgRgKcwr6Kf6qJGv
- `idle loop (records room).mp3`: uTa5ksZGZYsGrugiQ
- `idle loop (start).mp3`: bsosfdaiRL9xypsTG
- `idle loop (terror).mp3`: Fu4e3G5HJqJocdASd

## music/: the music (bgm), 2 files

- `Ending.mp3`: fD6RJw2kJjcPG27Gb
- `Title.mp3`: fdwgwPZMKzYCpPEXD

## The interface sounds (systemSounds), 14 files, under game/data/Audio/System/

These were in `story/interface/` until the dev moved them on 2026-10-19.

### System/menu/, 7 files

- `menu-accepted-try1.mp3`: GcZvWaGvTf6nzqnWd
- `menu-available.mp3`: 7EbuiHN2BGqKXSn3b
- `menu-close-try1.mp3`: WuGAzWQniekEytAXW
- `menu-lockout-ended.mp3`: jHEzaZdeciqffkAh5
- `menu-open-try3.mp3`: FbJYneK5wA9oyyWMF
- `menu-reminder.mp3`: SKLKBkamqkeev4N5q
- `menu-unavailable-try2.mp3`: 55dQB2vhhSZfDaLj2

### System/misc/, 7 files, beside bugfound.mp3 and thonk.mp3

- `click-bad.mp3`: Zv6QRNuE3MzLwPH9k
- `click.mp3`: jLiBQDqEp4skc4Ebg
- `ident - police radio.mp3`: AnbkA2qQc9EZndrLY
- `pause-pause healed.mp3`: sSHTADrgddeR94ots
- `pause-unpause.mp3`: T6uLifdW9uGFsXbzw
- `rewind-try2.mp3`: PEEhT2Q9u8im4Stze
- `we're losing you.mp3`: 9gAKj7wkhqMiAFWP4
