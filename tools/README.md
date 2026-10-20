# tools

Scripts for reading the original app. None of them is part of the game, none is shipped in a build, and none writes anything under `game/`. None plays sound or speaks.

- `macho64.py`: reads the arm64 code of `game/Heathcote`, the original's binary. It lists the segments and sections, the Objective-C classes with their methods and instance variables, the selector references and the imported functions. Run on its own, it prints the layout, whether the code is encrypted (it is not: `cryptid` 0), and the game's own classes, leaving out those of the libraries linked in (crash reporting, analytics, the sqlite wrapper). Standard library only.
- `dis64.py`: disassembles methods from that code, naming the selectors, imported functions, classes and strings each instruction refers to, and showing the value of each number loaded into a floating-point register, such as a duration in seconds. It can also find every method that uses an address or calls a selector. It needs `capstone` (`pip install capstone`), which the game itself does not.

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

Notes:
- Addresses are the binary's own virtual addresses, as the plans and notes cite them.
- A class method is named with a + in front, such as `+raiseActionsDial`.
- A class from the system frameworks, such as `NSTimer`, shows as `class@0`, since the binary names it only when it is loaded. The selector sent to it says which it is.
- Most of the binary is FMOD 1.7, the audio library, which these tools do not read.
- `HEATHCOTE_BINARY` sets the path of the binary to read.
