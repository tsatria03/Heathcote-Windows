"""The main menu (aidocks/plans/menus_plan.md, section 2), opened after the opening
(game/opening.py) with the title music under it:

    Start story     first, so one Enter gets into the story
    Settings        the Settings screen
    Credits         the credits (game/credits.py)
    Quit            its way out, so it has no Back row

Every menu moves with all four arrows, wrapping, and Home and End. Section 3 makes the
first row Continue story while a story is paused under the menu.
"""
from __future__ import annotations

from ..ui.menu import Menu, Row
from ..ui.settings_screen import SettingsScreen
from .credits import CreditsMenu


class MainMenu(Menu):
    name = 'main menu'
    title = 'Heathcote.'

    def opened(self):
        # The title music plays under the main menu, and starts again whenever the menu
        # comes back from the story (aidocks/plans/menus_plan.md).
        self.app.start_title_music()
        super().opened()

    def rows(self):
        # Quit is its way out, so it has no Back row (aidocks/general/feedback_back_first.md).
        return [Row('Start story', self.start_story),
                Row('Settings', lambda: self.stack.push(SettingsScreen(self.app))),
                Row('Credits', lambda: self.stack.push(CreditsMenu(self.app))),
                Row('Quit', self.app.quit)]

    def start_story(self):
        """The story from its start, each time, until the saves plan gives Continue story;
        the first time, at the spiel --spiel named, in debug mode."""
        from .story_screen import StoryScreen
        start_at, self.app.start_spiel = self.app.start_spiel, None
        self.stack.push(StoryScreen(self.app, start_at=start_at))

    def back(self):
        """Nothing is under the main menu: Escape says the row again."""
        self.say(self.row_text())
