"""The key bindings screen, opened with F1 from anywhere and read aloud.

    Back            the first row, which the screen opens on; Enter on it goes back
    Up and Down     move through the actions, each read with its keys, wrapping round
    Left and Right  the same as Up and Down
    Home and End    the first action and the last
    Enter           rebind: press the key you want, with Shift, Control or Alt if you like
    A               add another key instead of replacing
    Delete          unbind
    R               reset every binding, after asking: R again to do it
    F1 or Escape    back

This screen's own keys are fixed, never read from the key map, so a player who has unbound
the menu keys can always come here and put them right. F1 and Escape can never be given to
an action (aidocks/plans/foundation_plan.md). The timers are held while it is open.
"""
from __future__ import annotations

import logging

from ..platform.keymap import FIXED, MODIFIER_KEYS, binding, key_text
from .screens import Screen

log = logging.getLogger('keybind')

#: Said as the screen opens. How to use it is in docks/readme.txt.
HELP = 'Key bindings.'
RESET_PROMPT = ('Reset every binding to the default? Press R again to do it, or any other '
                'key to keep the bindings you have.')


class KeyBindScreen(Screen):
    name = 'key bindings'

    def __init__(self, app):
        super().__init__(app)
        self.keymap = app.keymap
        self.index = 0
        self.capturing = False
        self.capture_add = False
        self.confirm_reset = False

    @property
    def count(self):
        """Back, then every action."""
        return 1 + len(self.keymap.actions)

    @property
    def action(self):
        """The action the screen is on, or None on Back."""
        return self.keymap.actions[self.index - 1] if self.index > 0 else None

    def current_text(self):
        a = self.action
        if a is None:
            return 'Back'
        return '%s: %s' % (self.keymap.label(a), self.keymap.keys_text(a))

    def close(self):
        self.stack.pop()

    def opened(self):
        self.capturing = self.confirm_reset = False
        self.index = min(self.index, self.count - 1)
        self.say(HELP)
        self.say(self.current_text(), interrupt=False)

    def move_to(self, i):
        self.index = i % self.count
        self.say(self.current_text())

    def capture(self, add):
        self.capturing, self.capture_add = True, add
        self.say('Press the key for %s.' % self.keymap.label(self.action))

    def finish_capture(self, key, mods):
        self.capturing = False
        if key in FIXED:
            self.say('%s cannot be rebound. %s' % (key_text(key), self.current_text()))
            return
        b = binding(key, mods)
        stolen = self.keymap.conflicts(b, self.action)
        self.keymap.set_binding(self.action, b, replace=not self.capture_add)
        said = '%s is now %s.' % (self.keymap.label(self.action), self.keymap.keys_text(self.action))
        if stolen:
            said += ' Taken from %s.' % ', '.join(self.keymap.label(a) for a in stolen)
        self.say(said)

    def handle_key(self, key, mods):
        if self.capturing:
            if key in MODIFIER_KEYS:
                return True                 # wait for the key that goes with them
            self.finish_capture(key, mods)
            return True
        if self.confirm_reset:
            self.confirm_reset = False
            if key == 'r' and not mods:
                self.keymap.reset()
                self.say('Every binding is back to the default. %s' % self.current_text())
            else:
                self.say('Your bindings are kept. %s' % self.current_text())
            return True
        if mods:
            self.say(self.current_text())
            return True
        if key in ('escape', 'f1'):
            self.close()
        elif key in ('up', 'left'):
            self.move_to(self.index - 1)
        elif key in ('down', 'right'):
            self.move_to(self.index + 1)
        elif key == 'home':
            self.move_to(0)
        elif key == 'end':
            self.move_to(self.count - 1)
        elif key in ('return', 'enter') and self.action is None:
            self.close()                    # Back
        elif self.action is None and key in ('a', 'delete', 'backspace'):
            self.say(self.current_text())   # nothing to rebind on Back
        elif key in ('return', 'enter'):
            self.capture(add=False)
        elif key == 'a':
            self.capture(add=True)
        elif key in ('delete', 'backspace'):
            self.keymap.clear(self.action)
            self.say('%s is unbound.' % self.keymap.label(self.action))
        elif key == 'r':
            self.confirm_reset = True
            self.say(RESET_PROMPT)
        else:
            self.say(self.current_text())
        return True

    def lines(self):
        out = ['Key bindings', '', '%s Back' % ('>' if self.index == 0 else ' ')]
        for i, a in enumerate(self.keymap.actions, start=1):
            out.append('%s %s: %s' % ('>' if i == self.index else ' ',
                                      self.keymap.label(a), self.keymap.keys_text(a)))
        out.append('')
        for name, what in FIXED.items():
            out.append('  %s: %s (fixed)' % (what, key_text(name)))
        if self.capturing:
            out += ['', 'Press the key you want...']
        if self.confirm_reset:
            out += ['', 'Press R again to reset every binding, or any other key to keep them.']
        return out
