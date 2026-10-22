"""A spoken menu: the shape of every menu screen in the game, the story's actions menu
included. Its keys are the menu group's in platform/keymap.py, rebindable on the F1 screen:

    Up and Left     the row before, wrapping round to the last
    Down and Right  the row after, wrapping round to the first
    Home and End    the first row and the last
    Enter           choose the row
    Escape          go back
    any other key   say the row again

Moving, choosing and going back play the original's click-good, while the Click sounds
setting is on (aidocks/plans/menu_sounds_plan.md).

Each row is spoken by its text alone, such as "Settings", never with its place, such as
"1 of 2". Each move cuts off what was being said, so fast arrowing never builds a backlog.
Opening the menu says its title, then its row without cutting the title off
(aidocks/plans/foundation_plan.md). Back is the first row of any menu with a way back, and
the menu opens on it (aidocks/general/feedback_back_first.md).
"""
from __future__ import annotations

from ..platform.keymap import MENU
from .screens import Screen


class Row:
    """One row: its text, which may change, and what Enter on it does."""

    def __init__(self, text, action=None):
        self._text = text
        self.action = action

    @property
    def text(self):
        return self._text() if callable(self._text) else self._text


class Menu(Screen):
    name = 'menu'
    title = ''

    def __init__(self, app):
        super().__init__(app)
        self.index = 0

    def rows(self):
        """The rows, worked out each time, so a row can come and go."""
        return []

    def row_text(self, i=None):
        rows = self.rows()
        if not rows:
            return 'Nothing here.'
        i = self.index if i is None else i
        return rows[i].text

    def opened(self):
        self._clamp()
        if self.title:
            self.say(self.title)
            self.say(self.row_text(), interrupt=False)
        else:
            self.say(self.row_text())

    def _clamp(self):
        count = len(self.rows())
        self.index = min(self.index, max(0, count - 1))

    def move_to(self, i):
        rows = self.rows()
        if not rows:
            return
        self.index = i % len(rows)
        self.moved()

    def moved(self):
        """The row changed: say it. The actions menu plays its recorded clip instead."""
        self.say(self.row_text())

    def back(self):
        """Escape: close this menu."""
        self.stack.pop()

    def choose(self):
        self._clamp()
        rows = self.rows()
        if rows and rows[self.index].action is not None:
            rows[self.index].action()

    def other_key(self, action, key, mods):
        """A key this menu has no use for, or a menu action it leaves to a subclass: say the
        row again."""
        self.say(self.row_text())

    #: The original's click on choosing and on going back (aidocks/plans/menu_sounds_plan.md);
    #: a menu can turn either off.
    click_on_choose = True
    click_on_back = True

    def handle_key(self, key, mods):
        action = self.app.keymap.action_for(key, mods, MENU)
        count = len(self.rows())
        if action in ('menu_previous', 'menu_next', 'menu_first', 'menu_last'):
            self.app.click()
        if action == 'menu_previous':
            self.move_to(self.index - 1)
        elif action == 'menu_next':
            self.move_to(self.index + 1)
        elif action == 'menu_first':
            self.move_to(0)
        elif action == 'menu_last':
            self.move_to(count - 1)
        elif action == 'menu_choose':
            if self.click_on_choose:
                self.app.click()
            self.choose()
        elif action == 'menu_back':
            if self.click_on_back:
                self.app.click()
            self.back()
        else:
            self.other_key(action, key, mods)       # says the row again, with no click
        return True

    def lines(self):
        out = [self.title, ''] if self.title else []
        for i, row in enumerate(self.rows()):
            out.append('%s %s' % ('>' if i == self.index else ' ', row.text))
        return out
