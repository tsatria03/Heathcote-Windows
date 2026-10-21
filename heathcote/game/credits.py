"""The credits, as a spoken menu (aidocks/plans/menus_plan.md).

The original's credits were two pictures, ``credits-1`` and ``credits-2``, which a screen
reader never read; their words are here as text, one row each, read from the pictures on
2026-10-19. After them come the port's row and FMOD's credit line, which FMOD's licence
requires, naming "FMOD" and "Firelight Technologies Pty Ltd." (aidocks/general/project_fmod.md).

Back is the first row, and the menu opens on it. Enter on a credit says it again. The
main menu's Credits row opens it; the end of the story will open it too (section 4).
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
