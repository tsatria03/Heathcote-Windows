"""The original's story data, read as it is, and where its recordings are on disk.

The data is the export of the original's authoring tool, in game/documents/text/:

- system/Heathcote v1.01.bundle.json, the index: ``labels`` maps each softRef to a
  readable name, and ``assets`` maps each category to {softRef: record id}.
- story/<record id>.json, one record each.

Every reference inside a record is a softRef, except ``file``, which is the id of the
record describing the audio file. A recording is found through that file record's
``original.name``, with ``.mp3`` in place of its extension and any character Windows does
not allow dropped, in the folders for the referring record's category (``FOLDERS``, and
aidocks/general/project_audio_names.md).

This is the one place those rules live. The game reads the story through it, and
``tools/story.py`` checks the data through it, so what the tool reports is what the game
meets (aidocks/plans/audio_plan.md).
"""
from __future__ import annotations

import json
import logging
import os
import re

from .. import paths
from ..platform import pack

log = logging.getLogger('story')

#: The folders under game/documents/Audio/ that hold each category's recordings, as the dev
#: laid them out. A recording is looked for in each, in order.
FOLDERS = {
    'actionSpiels': ('story/scene',),
    'systemVoice': ('story/speech',),
    'ambience': ('story/ambience',),
    'idleLoops': ('story/idle',),
    'bgm': ('story/music',),
    'systemSounds': ('System/menu', 'System/misc'),
}

#: Every story variable starts as this string (+[Vars createStoryDefaults], 0x1000321e4).
VARIABLE_DEFAULT = '0'

#: The spiel the story starts with (+[Story justStart], 0x10001a6e0).
START_LABEL = 'start'

#: The audio lanes a spiel can carry, besides its own recording.
LANES = ('bgm', 'ambience', 'ambience1', 'ambience2', 'ambience3')

#: The plain "ambience" lane is in the data but the original never reads it
#: (+[Sound tick], 0x100020dd4 to 0x100020e30), so its fades never played.
UNPLAYED_LANES = ('ambience',)


#: The folder under Audio/ that story.dat packs whole (aidocks/plans/build_release_plan.md).
PACKED_FOLDER = 'story'

MISSING_PACK = ("Heathcote's story recordings were not found. They are in story.dat, which "
                "belongs beside Heathcote.exe; extract the whole Heathcote-Windows folder "
                "from the download again. Looked for %s.")
WRONG_PACK = ("Heathcote's story.dat does not belong to this copy of the game: %s. Extract "
              "the whole Heathcote-Windows folder from the download again.")


def open_pack(game_folder):
    """story.dat, opened and checked against the fingerprint a build carries in its
    game/documents/text/system/; SystemExit with a message for the player when it is
    missing, damaged or from another build."""
    where = paths.story_pack()
    if not os.path.isfile(where):
        raise SystemExit(MISSING_PACK % where)
    expected = os.path.join(game_folder, *paths.PACK_FINGERPRINT_FOLDER, paths.PACK_FINGERPRINT)
    if os.path.isfile(expected):
        try:
            with open(expected, encoding='utf-8') as f:
                size = json.load(f)['size']
        except (OSError, ValueError, KeyError):
            size = None
        if size is not None and os.path.getsize(where) != size:
            raise SystemExit(WRONG_PACK % ('it is %d bytes, not %d' % (os.path.getsize(where), size)))
    try:
        opened = pack.Pack(where)
    except pack.PackError as error:
        raise SystemExit(WRONG_PACK % error)
    pack.use(opened)
    log.info('story recordings: %s', where)
    return opened


def disk_name(original):
    """The MP3 name a recording has on disk, from its file record's original name.

    The extension becomes .mp3, characters Windows does not allow are dropped, and spaces
    at either end of the name are trimmed, as in "idle loop (inside entrance) .mp3".
    """
    base = os.path.splitext(original)[0]
    return re.sub(r'[<>:"/\\|?*]', '', base).strip() + '.mp3'


class StoryData:
    """The index and every record, with the lookups the game and the tool share."""

    _shared = None

    @classmethod
    def shared(cls):
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    def __init__(self, text=None):
        text = text or paths.text()
        self.audio_root = os.path.join(os.path.dirname(text), 'Audio')
        with open(os.path.join(text, 'system', paths.BUNDLE_NAME), encoding='utf-8-sig') as f:
            index = json.load(f)
        self.labels = index['labels']
        self.assets = index['assets']
        self.records = {}
        self.unreadable = []   # (file name, reason)
        folder = os.path.join(text, 'story')
        for name in sorted(os.listdir(folder)):
            try:
                with open(os.path.join(folder, name), encoding='utf-8-sig') as f:
                    rec = json.load(f)
                self.records[rec['_id']] = rec
            except (ValueError, KeyError) as e:
                self.unreadable.append((name, str(e).split(':')[0]))
        self.category = {soft: cat for cat, refs in self.assets.items() for soft in refs}
        # The story's recordings: the loose folder when it is there, as from source, or else
        # story.dat (platform/pack.py), as in a build.
        self.pack = None
        if not os.path.isdir(os.path.join(self.audio_root, PACKED_FOLDER)):
            self.pack = open_pack(os.path.dirname(os.path.dirname(text)))

    def record(self, soft):
        """The record a softRef stands for, or None."""
        cat = self.category.get(soft)
        return self.records.get(self.assets[cat][soft]) if cat else None

    def label(self, soft):
        return self.labels.get(soft, soft)

    def refs(self, category):
        """The softRefs of a category, in the index's order."""
        return list(self.assets.get(category, {}))

    def find(self, category, label):
        """The softRefs in a category with this label; labels are not always unique."""
        return [s for s in self.refs(category) if self.labels.get(s) == label]

    def start(self):
        found = self.find('actionSpiels', START_LABEL)
        return found[0] if found else None

    def audio_path(self, soft):
        """The path of a softRef's recording, or None if it has no file.

        It is the first of the category's folders that holds the file; when none does, it
        is where the file would be in the first folder.
        """
        rec = self.record(soft)
        cat = self.category.get(soft)
        if not rec or not rec.get('file') or cat not in FOLDERS:
            return None
        frec = self.records.get(rec['file'])
        if not frec or 'original' not in frec:
            return None
        name = disk_name(frec['original']['name'])
        if self.pack is not None and FOLDERS[cat][0].startswith(PACKED_FOLDER + '/'):
            names = ['%s/%s' % (folder[len(PACKED_FOLDER) + 1:], name) for folder in FOLDERS[cat]]
            return pack.PREFIX + next((n for n in names if n in self.pack), names[0])
        found = [os.path.join(self.audio_root, *folder.split('/'), name) for folder in FOLDERS[cat]]
        return next((p for p in found if os.path.exists(p)), found[0])

    def sound_path(self, category, label):
        """The recording of the first softRef in a category with this label, such as
        ('systemSounds', 'click-good') or ('bgm', 'title'); None if there is none."""
        for soft in self.find(category, label):
            path = self.audio_path(soft)
            if path:
                return path
        return None
