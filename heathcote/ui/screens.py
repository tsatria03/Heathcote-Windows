"""The stack of screens the main loop drives.

The top screen gets every key and is drawn in the window. A screen can open another on top
(``stack.push``), close itself (``stack.pop``), or put another in its place
(``stack.replace``); closing the last one ends the game. The F1 key bindings screen goes
on top of whatever is open, and the timers are held while it is up
(aidocks/plans/foundation_plan.md).
"""
from __future__ import annotations

import logging

log = logging.getLogger('screens')


class Screen:
    """What every screen has. Subclasses fill in what they need."""

    #: A short name for the log.
    name = 'screen'

    def __init__(self, app):
        self.app = app

    @property
    def stack(self):
        return self.app.stack

    def say(self, text, interrupt=True):
        self.app.speech.speak(text, interrupt)

    def opened(self):
        """Put on top of the stack, or back on top after the one above it closed."""

    def closed(self):
        """Taken off the stack for good."""

    def covered(self):
        """Another screen was opened on top of this one."""

    def handle_key(self, key, mods):
        """A key was pressed: pygame's name for it, and the modifiers held. True when used."""
        return False

    def update(self):
        """Called once a frame while on top."""

    def focus_lost(self):
        """The game's window lost the keyboard; the story pauses."""

    def focus_gained(self):
        """The game's window has the keyboard again."""

    def lines(self):
        """What the window shows, for a sighted helper."""
        return []


class ScreenStack:
    def __init__(self):
        self.screens = []

    @property
    def top(self):
        return self.screens[-1] if self.screens else None

    @property
    def empty(self):
        return not self.screens

    def push(self, screen):
        if self.top is not None:
            self.top.covered()
        self.screens.append(screen)
        log.info('opened %s', screen.name)
        screen.opened()

    def pop(self):
        """Close the top screen and reopen the one below it."""
        if not self.screens:
            return
        screen = self.screens.pop()
        log.info('closed %s', screen.name)
        screen.closed()
        if self.top is not None:
            self.top.opened()

    def replace(self, screen):
        """Put ``screen`` in place of the top one."""
        if self.screens:
            old = self.screens.pop()
            log.info('closed %s', old.name)
            old.closed()
        self.screens.append(screen)
        log.info('opened %s', screen.name)
        screen.opened()

    def reset(self, screen):
        """Close every screen and open ``screen`` alone."""
        self.clear()
        self.push(screen)

    def clear(self):
        while self.screens:
            screen = self.screens.pop()
            log.info('closed %s', screen.name)
            screen.closed()
