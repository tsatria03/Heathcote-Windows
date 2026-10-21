"""The Settings screen, opened from the main menu and from the pause menu
(aidocks/plans/menus_plan.md, aidocks/plans/settings_plan.md):

    Back                            first, as in every menu
    Debug mode, currently off       source runs only; Enter turns it on or off at once
    Master volume, 100 percent      each volume opens a list of its levels
    Background volume, 100 percent
    Interface volume, 100 percent
    Title volume, 100 percent
    Volume speed, 100 milliseconds  how often a held volume key repeats
    Key bindings                    the F1 screen

A list of levels opens on Back. Enter on a level takes effect at once, is saved, and
returns to Settings saying the row; Escape, or Enter on Back, keeps the value as it was.
Every volume can be set here, wherever its keys work or not, and the keys stay as they are
(platform/keymap.py). The game remembers every setting in ``config/settings.json``.
"""
from __future__ import annotations

from .. import paths
from ..platform.settings import VOLUME_LABELS, VOLUME_SPEEDS, VOLUME_STEP, VOLUMES
from .menu import Menu, Row


def speed_text(ms):
    """'100 milliseconds', with the ends of the list named, as "50 milliseconds, fastest"."""
    text = '%d milliseconds' % ms
    if ms == VOLUME_SPEEDS[0]:
        return text + ', fastest'
    if ms == VOLUME_SPEEDS[-1]:
        return text + ', slowest'
    return text


class LevelsMenu(Menu):
    """A setting's levels: Back first and opened on, then each level. Enter on a level sets
    it, saves it and goes back, where Settings says the row again; Escape keeps it as it
    was."""

    name = 'levels'

    def __init__(self, app, key, label, levels, text, changed=None):
        super().__init__(app)
        self.key = key
        self.title = '%s.' % label
        self.levels = levels
        self.text = text
        self.changed = changed or (lambda: None)

    def rows(self):
        return [Row('Back', self.back)] + [Row(self.text(level), self.picker(level))
                                           for level in self.levels]

    def picker(self, level):
        def pick():
            if self.app.settings.get(self.key) != level:
                self.app.settings.set(self.key, level)
                self.changed()
            self.stack.pop()
        return pick


class SettingsScreen(Menu):
    name = 'settings'
    title = 'Settings.'

    def rows(self):
        rows = [Row('Back', self.back)]
        if not paths.FROZEN:
            rows.append(Row(lambda: 'Debug mode, currently %s' % ('on' if self.app.debug else 'off'),
                            self.toggle_debug))
        for key in VOLUMES:
            rows.append(Row(self.volume_text(key), self.opener(key)))
        rows.append(Row(lambda: 'Volume speed, %s' % speed_text(self.app.settings.get('volume_speed')),
                        self.open_speed))
        rows.append(Row('Key bindings', self.app.open_key_bindings))
        return rows

    def volume_text(self, key):
        return lambda: '%s, %d percent' % (VOLUME_LABELS[key], self.app.settings.get(key))

    def opener(self, key):
        def open_levels():
            self.stack.push(LevelsMenu(self.app, key, VOLUME_LABELS[key],
                                       tuple(range(100, -1, -VOLUME_STEP)), lambda p: '%d percent' % p,
                                       changed=self.app.volumes_changed))
        return open_levels

    def open_speed(self):
        self.stack.push(LevelsMenu(self.app, 'volume_speed', 'Volume speed', VOLUME_SPEEDS, speed_text))

    def opened(self):
        """Back from a list of levels: just the row, with its value now; first opened: the
        title, then the row."""
        if getattr(self, 'shown', False):
            self._clamp()
            self.say(self.row_text())
            return
        self.shown = True
        super().opened()

    def toggle_debug(self):
        self.app.set_debug(not self.app.debug)
        self.say(self.row_text())
