"""Where things are: the game's own data, the vendored libraries and the save folder.

From source, everything is found from the repository's root. In a build made by
compiler.py, PyInstaller unpacks the code to ``sys._MEIPASS`` and the game's data
sits beside the executable, or inside it for a single exe (aidocks/plans/build_release_plan.md).

The game never writes to ``game/``. Everything it remembers goes in
``%APPDATA%\\Heathcote`` (aidocks/plans/saves_plan.md), or wherever
``HEATHCOTE_USER_DIR`` points, which the tests set to a throwaway folder so they never
touch a player's save.
"""
from __future__ import annotations

import logging
import os
import sys

log = logging.getLogger('paths')

FROZEN = getattr(sys, 'frozen', False)
if FROZEN:
    ROOT = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EXE_DIR = ROOT

VENDOR = os.path.join(ROOT, 'vendor')
NVDA_DLL = os.path.join(VENDOR, 'nvda', 'nvdaControllerClient64.dll')
#: Gitignored; copied in by hand from the FMOD Engine install (aidocks/general/project_fmod.md).
FMOD_DLL = os.path.join(VENDOR, 'fmod', 'fmod.dll')

#: The save folder's name under %APPDATA% (aidocks/plans/foundation_plan.md).
SAVE_FOLDER = 'Heathcote'
#: Set by the tests to a throwaway folder, never by the game.
USER_DIR_ENV = 'HEATHCOTE_USER_DIR'

#: The folder inside game/ holding everything the game reads, its text and its audio. The
#: dev renamed it from data to documents on 2026-10-20 ("I renamed the folders on perpis.").
DATA_FOLDER = 'documents'
#: The original's master index of the story, inside game/documents/text/system/.
BUNDLE_NAME = 'Heathcote v1.01.bundle.json'


def _has_data(folder: str) -> bool:
    return os.path.isfile(os.path.join(folder, DATA_FOLDER, 'text', 'system', BUNDLE_NAME))


def game() -> str:
    """The folder holding the game's data: beside the executable in a folder build, inside
    it in a single exe, or the repository's own ``game/`` from source."""
    tried = []
    for folder in (os.path.join(EXE_DIR, 'game'), os.path.join(ROOT, 'game')):
        if folder in tried:
            continue
        tried.append(folder)
        if _has_data(folder):
            return folder
    raise SystemExit("Heathcote's game data was not found. Looked for %s in:\n  %s"
                     % (BUNDLE_NAME, '\n  '.join(os.path.join(f, DATA_FOLDER, 'text', 'system')
                                                 for f in tried)))


def text() -> str:
    """``game/documents/text``: the story records in ``story/`` and the index in ``system/``."""
    return os.path.join(game(), DATA_FOLDER, 'text')


def bundle() -> str:
    """The story's master index: labels, and each kind's records by softRef."""
    return os.path.join(text(), 'system', BUNDLE_NAME)


def story_records() -> str:
    """``game/documents/text/story``: one JSON file per record, named by its id."""
    return os.path.join(text(), 'story')


def audio() -> str:
    """``game/documents/Audio``: the story recordings in ``story/`` and the interface
    sounds in ``System/``."""
    return os.path.join(game(), DATA_FOLDER, 'Audio')


#: The story's recordings, packed (platform/pack.py, aidocks/plans/build_release_plan.md).
STORY_PACK = 'story.dat'
#: The pack's size and SHA-256, which compiler.py puts in a build's
#: game/documents/text/system/, beside the story's index (the dev, 2026-10-21: "Can you please
#: put the story_pack.json file in documents/text/system?").
PACK_FINGERPRINT = 'story_pack.json'
PACK_FINGERPRINT_FOLDER = (DATA_FOLDER, 'text', 'system')


def story_pack() -> str:
    """Where story.dat is: beside the executable in a build, or dist\\story.dat from source,
    used there only when game/documents/Audio/story/ is not."""
    return os.path.join(EXE_DIR if FROZEN else os.path.join(ROOT, 'dist'), STORY_PACK)


def version() -> str:
    """The port's version from ``VERSION``, beside the executable or at the repository's
    root; 'unknown' when it is missing."""
    for folder in (EXE_DIR, ROOT):
        try:
            with open(os.path.join(folder, 'VERSION'), 'r', encoding='utf-8-sig') as f:
                value = f.read().strip()
            if value:
                return value
        except OSError:
            pass
    return 'unknown'


def user_dir() -> str:
    """The save folder, made if it is not there yet."""
    folder = os.environ.get(USER_DIR_ENV)
    if not folder:
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        folder = os.path.join(base, SAVE_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def user_path(*parts: str) -> str:
    """A path inside the save folder, such as ``user_path('config', 'settings.json')``."""
    return os.path.join(user_dir(), *parts)


def logs_dir() -> str:
    folder = user_path('logs')
    os.makedirs(folder, exist_ok=True)
    return folder
