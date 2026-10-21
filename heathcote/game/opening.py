"""The opening, before the main menu (aidocks/plans/menus_plan.md, section 1).

1. The original's splash: its ``ident`` sound, a police radio, on the ``sfx`` channel, with
   "Heathcote." spoken. It moves on when the sound ends (-[IdentState tick], 0x10003e6bc).
   Enter skips it with ``click-good``, as the original's swipe up did; any other key gives
   ``click-bad`` (-[IdentState up], 0x10003e974).
2. The first time only, a notice from the original's first-run tutorial (``PreflightState``):
   Enter continues, and the game remembers it has been shown, in the
   ``first_run_notice_shown`` setting, as the original's ``tutor-preflight``. Any other key
   says it again. The tutorial's "Control the story by swiping, not tapping." is left out,
   since it does not fit a keyboard.
3. Then the main menu, with the title music, and no 4-second title before it.
"""
from __future__ import annotations

from ..platform.keymap import MENU, binding_text
from ..ui.screens import Screen
from .storydata import StoryData

TITLE = 'Heathcote.'
NOTICE = ('Heathcote is a responsive story told through sound. Headphones are strongly '
          'recommended. For the most immersive experience, try playing with your eyes closed.')


def main_menu(app):
    from .menus import MainMenu
    return MainMenu(app)


class OpeningScreen(Screen):
    """The splash: the police radio, then the notice or the main menu."""

    name = 'opening'

    def __init__(self, app):
        super().__init__(app)
        self.started = False
        self.playing = False        # whether the ident sound started
        self.done = False

    def opened(self):
        if self.started:            # back from the F1 screen: the sound played on
            return
        self.started = True
        # Not cutting anything off, so a tool's opening words are heard first.
        self.say(TITLE, interrupt=False)
        path = StoryData.shared().sound_path('systemSounds', 'ident')
        audio = self.app.audio
        self.playing = bool(path and audio.ok and audio.slot('sfx').play(path, loop=False))

    def update(self):
        if not self.done and not (self.playing and self.app.audio.slot('sfx').playing):
            self.move_on()

    def handle_key(self, key, mods):
        if self.app.keymap.action_for(key, mods, MENU) == 'menu_choose':
            self.app.play_sound('click-good')
            if self.playing:
                self.app.audio.slot('sfx').stop()
            self.move_on()
        else:
            self.app.play_sound('click-bad')
        return True

    def move_on(self):
        if self.done:
            return
        self.done = True
        if self.app.settings.get('first_run_notice_shown'):
            self.stack.replace(main_menu(self.app))
        else:
            self.stack.replace(NoticeScreen(self.app))

    def lines(self):
        return [TITLE]


class NoticeScreen(Screen):
    """The first-run notice: Enter continues, and it is never shown again."""

    name = 'first-run notice'

    def continue_text(self):
        keys = self.app.keymap.bindings.get('menu_choose') or []
        return 'Press %s to continue.' % binding_text(keys[0]) if keys else ''

    def opened(self):
        self.say(NOTICE)
        self.say(self.continue_text(), interrupt=False)

    def handle_key(self, key, mods):
        if self.app.keymap.action_for(key, mods, MENU) == 'menu_choose':
            self.app.play_sound('click-good')
            self.app.settings.set('first_run_notice_shown', True)
            self.stack.replace(main_menu(self.app))
        else:
            self.opened()
        return True

    def lines(self):
        # A sentence a line, so the window does not cut them off.
        return [s.strip() + '.' for s in NOTICE.split('.') if s.strip()] + ['', self.continue_text()]
