"""The credits, as a spoken menu (aidocks/plans/menus_plan.md).

The original's credits were two pictures, ``credits-1`` and ``credits-2``, which a screen
reader never read; their words are here as text, one row each, read from the pictures on
2026-10-19. After them come the port's row and FMOD's credit line, which FMOD's licence
requires, naming "FMOD" and "Firelight Technologies Pty Ltd." (aidocks/general/project_fmod.md).

Back is the first row, and the menu opens on it. Enter on a credit says it again. The
main menu's Credits row opens it, and the end of the story opens it as ``EndCredits``.
"""
from __future__ import annotations

from ..ui.menu import Menu, Row

#: The original's two cards, in their order.
ORIGINAL = (
    'Heathcote, version 1.01, by Fabulae Obscurae',
    'Story: Christian Francis, Ben Meares',
    'David Scott, Fausto Kaufer, Joe Banks: Hunter Davis',
    'Martin Fellows: Robert Dunne',
    'Announcer: Mark Hamilton',
    'Music: Jason Martin Castillo',
    'Design and Engineering: Mike Dean',
    'Producing and Directing: Lisa Wong',
    'Audio Consultant: Alex Ruger',
    'Special thanks to Nowell Valeri',
    'This app uses many sounds from freesound. For the full list see fabulaeobscurae.com/heathcote',
    'FMOD Studio by Firelight Technologies',
)
PORT = 'Windows port: tsatria03'
FMOD_LINE = 'Made with FMOD Engine, by Firelight Technologies Pty Ltd.'
CREDITS = ORIGINAL + (PORT, FMOD_LINE)


class CreditsMenu(Menu):
    name = 'credits'
    title = 'Credits.'

    def rows(self):
        return [Row('Back', self.back)] + [Row(text, self.say_again) for text in CREDITS]

    def say_again(self):
        self.say(self.row_text())


class EndCredits(CreditsMenu):
    """The credits at the end of the story (section 4; +[StoryView raiseEndCredits],
    0x100025b10). They open over the story, which plays on beneath them, its last spiel
    and its ending music, so the story's volume keys work here. Leaving them, by Back or
    Escape, plays ``pause-pause``, resets the story, as Restart story does, and returns to
    the main menu, which offers Start story again (+[StoryView lowerCredits], 0x1000264a8).
    The original's "Want more?" prompt, which opened its developer's website, is left out."""

    name = 'end credits'
    title = 'The story has ended. Credits.'

    def __init__(self, app, story_screen):
        super().__init__(app)
        self.story_screen = story_screen

    def volume_group(self):
        return self.story_screen.volume_group()

    def update(self):
        self.story_screen.update()          # the story plays on beneath

    def back(self):
        self.stack.pop()
        self.story_screen.end_story()
