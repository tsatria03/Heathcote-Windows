# tools

Scripts for reading the original app. None of them is part of the game, none is shipped in a build, and none writes anything under `game/`; the only file any of them writes is `analysis/script/Heathcote.txt`. None plays sound or speaks.

- `macho64.py`: reads the arm64 code of `game/Heathcote`, the original's binary. It lists the segments and sections, the Objective-C classes with their methods and instance variables, the selector references and the imported functions. Run on its own, it prints the layout, whether the code is encrypted (it is not: `cryptid` 0), and the game's own classes, leaving out those of the libraries linked in (crash reporting, analytics, the sqlite wrapper). Standard library only.
- `dis64.py`: disassembles methods from that code, naming the selectors, imported functions, classes and strings each instruction refers to, and showing the value of each number loaded into a floating-point register, such as a duration in seconds. It can also find every method that uses an address or calls a selector. It needs `capstone` (`pip install capstone`), which the game itself does not.

- `story.py`: reads the story data in `game/data/text/` as it is, the way the game does, and checks it: every reference leads to a real record, every recording is on disk, every value a condition asks for can happen, every spiel can be reached from `start`, and which `next` entries can both be true. It sorts what it finds into problems, which would break the game, and notes, which play as the original did. `--labels` lists every softRef's label by category. Standard library only.
- `script_text.py`: writes the whole story as plain text into `analysis/script/Heathcote.txt`, in the order it opens up from the start, then every action. Each spiel begins with "Spiel: <label>", so a screen reader's find can jump to it, and that label is what `--spiel` takes. Standard library only.

Examples, from the repo root:

    python tools/macho64.py
    python tools/macho64.py --all
    python tools/macho64.py --ivars Dial
    python tools/dis64.py --list StoryView
    python tools/dis64.py --find lockout
    python tools/dis64.py StoryView +raiseActionsDial
    python tools/dis64.py --at 0x1000245c0
    python tools/dis64.py --refs 0x10023bbb0
    python tools/dis64.py --refs lockoutGraceTimerFired:
    python tools/dis64.py --brief Story +justStart
    python tools/dis64.py --full --brief Sound +tick
    python tools/story.py
    python tools/story.py --labels
    python tools/script_text.py

Notes:
- Addresses are the binary's own virtual addresses, as the plans and notes cite them.
- A class method is named with a + in front, such as `+raiseActionsDial`.
- A listing stops at a method's first `ret` unless `--full` is given, which reads on to where the next method begins; many methods return early and carry on after. `--refs` always reads in full.
- A class from the system frameworks, such as `NSTimer`, shows as `class@0`, since the binary names it only when it is loaded. The selector sent to it says which it is.
- Most of the binary is FMOD 1.7, the audio library, which these tools do not read.
- `HEATHCOTE_BINARY` sets the path of the binary to read.
