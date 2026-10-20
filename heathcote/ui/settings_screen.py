"""The Settings screen. The menus plan (aidocks/plans/menus_plan.md, section 2) finishes
it; for now it has what the foundation needs:

    Back                        first, as in every menu
    Debug mode, currently off   source runs only; Enter turns it on or off at once
    Key bindings                the F1 screen

The volumes are set with their keys: the master anywhere, the title volume here and in
the main menu while the title music plays, and the others in the story
(platform/keymap.py). The game
remembers every setting in ``config/settings.json``.
"""
from __future__ import annotations

from .. import paths
from .menu import Menu, Row


class SettingsScreen(Menu):
    name = 'settings'
    title = 'Settings.'

    def rows(self):
        rows = [Row('Back', self.back)]
        if not paths.FROZEN:
            rows.append(Row(lambda: 'Debug mode, currently %s' % ('on' if self.app.debug else 'off'),
                            self.toggle_debug))
        rows.append(Row('Key bindings', self.app.open_key_bindings))
        return rows

    def toggle_debug(self):
        self.app.set_debug(not self.app.debug)
        self.say(self.row_text())
