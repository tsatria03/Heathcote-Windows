"""The main menu (aidocks/plans/menus_plan.md, section 2), opened after the opening
(game/opening.py) with the title music under it:

    Start story     first, so one Enter gets into the story
    Settings        the Settings screen
    Credits         the credits (game/credits.py)
    Quit            its way out, so it has no Back row; Escape quits too

Every menu moves with all four arrows, wrapping, and Home and End. While a story is paused
under the menu (section 3), the first row is Continue story instead, said with its chapter.
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
        # One row whose name changes, so Start story and Continue story are never offered
        # together.
        if self.app.paused_story is not None:
            first = Row(self.continue_text, self.continue_story)
        else:
            first = Row('Start story', self.start_story)
        return [first,
                Row('Settings', lambda: self.stack.push(SettingsScreen(self.app))),
                Row('Credits', lambda: self.stack.push(CreditsMenu(self.app))),
                Row('Quit', self.app.quit)]

    def start_story(self):
        """A new story from its start; the first time, at the spiel --spiel named, in debug
        mode. Offered whenever no story is paused under the menu; the saves plan will
        offer Continue story across runs too."""
        from .story_screen import StoryScreen
        start_at, self.app.start_spiel = self.app.start_spiel, None
        self.stack.push(StoryScreen(self.app, start_at=start_at))

    def continue_text(self):
        """Said with its chapter, the story variable ``location``, as the original's
        CONTINUE was, in the dev's words (2026-10-20: "Continue story: approaching
        Heathcote.")."""
        from .state import LOCATION, VARIABLE_DEFAULT
        location = self.app.paused_story.state.get_by_label(LOCATION)
        if location == VARIABLE_DEFAULT:
            return 'Continue story'
        return 'Continue story: %s.' % location

    def continue_story(self):
        """The paused story, picked up exactly where Return to menu left it."""
        self.app.paused_story.continue_story()

    def back(self):
        """Escape quits, as the Quit row does (the dev, 2026-10-20: "Pressing escape in the
        main menu should also quit the game, like the quit option already does.")."""
        self.app.quit()
