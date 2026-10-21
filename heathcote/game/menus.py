"""The menus around the story.

For now this is the stand-in main menu of aidocks/plans/foundation_plan.md: Start story,
added for the story engine (aidocks/plans/story_engine_plan.md), Settings and Quit. The
menus plan
(aidocks/plans/menus_plan.md) puts the real one here, with Start story or Continue story,
Settings, Credits and Quit.
"""
from __future__ import annotations

from ..ui.menu import Menu, Row
from ..ui.settings_screen import SettingsScreen


class MainMenu(Menu):
    name = 'main menu'
    title = 'Heathcote.'

    def opened(self):
        # The title music plays under the main menu (aidocks/plans/menus_plan.md). Until the
        # audio plan plays it, this only lets the title volume's keys work here.
        self.app.title_music = True
        super().opened()

    def rows(self):
        # Quit is its way out, so it has no Back row (aidocks/general/feedback_back_first.md).
        return [Row('Start story', self.start_story),
                Row('Settings', lambda: self.stack.push(SettingsScreen(self.app))),
                Row('Quit', self.app.quit)]

    def start_story(self):
        """The story from its start, each time, until the saves plan gives Continue story."""
        from .story_screen import StoryScreen
        self.stack.push(StoryScreen(self.app))

    def back(self):
        """Nothing is under the main menu: Escape says the row again."""
        self.say(self.row_text())
