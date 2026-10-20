"""The player's settings, in ``config/settings.json`` in the save folder.

Every setting is written on the first start, at its default, so the file always lists all
of them (aidocks/plans/saves_plan.md). A value the game cannot use is put back to its
default, and a setting it no longer knows is left alone.
"""
from __future__ import annotations

import logging

from .. import paths
from .files import JsonFile

log = logging.getLogger('settings')

#: Each setting's default, in the order the file lists them.
DEFAULTS = {
    # aidocks/plans/audio_plan.md: 0 to 100 percent. The spiel follows only the master;
    # the backgrounds are the music, the ambiences and the idle loop; the interface is the
    # system sounds and the recorded choices.
    'master_volume': 100,
    'backgrounds_volume': 100,
    'interface_volume': 100,
    'debug': False,                     # aidocks/plans/foundation_plan.md: source runs only
    'first_run_notice_shown': False,    # aidocks/plans/menus_plan.md: the first start only
}
VOLUMES = ('master_volume', 'backgrounds_volume', 'interface_volume')
#: What each volume is called when it is spoken.
VOLUME_LABELS = {'master_volume': 'Master volume',
                 'backgrounds_volume': 'Background volume',
                 'interface_volume': 'Interface volume'}
#: How far one press of a volume key moves a volume, in percent. Every volume is a
#: multiple of it, so 0 and 100 are always reached.
VOLUME_STEP = 10


def _valid(key, value):
    default = DEFAULTS[key]
    if isinstance(default, bool):
        return isinstance(value, bool)
    if isinstance(value, bool) or not isinstance(value, type(default)):
        return False
    if key in VOLUMES:
        return 0 <= value <= 100 and value % VOLUME_STEP == 0
    return True


class Settings:
    _shared = None

    @classmethod
    def shared(cls):
        if cls._shared is None:
            cls._shared = Settings()
        return cls._shared

    def __init__(self, path=None):
        self.file = JsonFile(path or paths.user_path('config', 'settings.json'),
                             order=list(DEFAULTS))
        changed = self.file.recovered
        for key, default in DEFAULTS.items():
            if key not in self.file.data:
                self.file.data[key] = default
                changed = True
            elif not _valid(key, self.file.data[key]):
                log.warning('settings: %s was %r, put back to %r', key, self.file.data[key], default)
                self.file.data[key] = default
                changed = True
        if changed:
            self.file.write()

    def get(self, key):
        return self.file.data.get(key, DEFAULTS[key])

    def set(self, key, value):
        """Change a setting and write the file at once."""
        if key not in DEFAULTS:
            raise KeyError(key)
        if not _valid(key, value):
            raise ValueError('%s cannot be %r' % (key, value))
        self.file.data[key] = value
        self.file.write()

    def toggle(self, key):
        """Turn an on-or-off setting over; the new value."""
        value = not self.get(key)
        self.set(key, value)
        return value

    def step_volume(self, key, steps):
        """Move a volume by ``steps`` presses, kept within 0 and 100; the new level."""
        level = min(100, max(0, self.get(key) + steps * VOLUME_STEP))
        if level != self.get(key):
            self.set(key, level)
        return level
