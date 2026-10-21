"""The story's actions menu (aidocks/plans/story_engine_plan.md, section 3).

It is plan 2's spoken menu (ui/menu.py), with the same keys, rebindable on F1: all four
arrows move, wrapping round, Home and End jump, Enter accepts, and Escape closes. It opens
on the first choice, the lowest ``order`` (-[Dial configure:], 0x10000dac0).

Each move plays the choice's recorded clip from ``speech/``, as the original announced it
(-[Dial announcePos], 0x10000eb30). A choice with no clip, "next room" or "just stop", is
said by the screen reader instead, since the original's synthesizer was a stub and said
nothing. After 7 seconds with no move, the choice plays again (-[ActionsDialState tick],
0x100037de0); the original's swipe hint is left out, as it does not fit a keyboard.

Space, the ``choice_text`` action, speaks the choice's text through the screen reader,
without moving or accepting (the dev, 2026-10-19: "Space is fine.").

The story's volume keys work here too, as the story is still playing underneath.
"""
from __future__ import annotations

import time

from ..platform.keymap import STORY, STORY_VOLUMES
from ..ui.menu import Menu, Row

#: Seconds with no move before the choice plays again: 420 ticks.
REPEAT_AFTER = 7.0


class ActionsMenu(Menu):
    name = 'actions menu'

    def __init__(self, app, player, choices, clock=time.perf_counter):
        super().__init__(app)
        self.player = player
        self.choices = list(choices)
        self.clock = clock
        self.moved_at = clock()
        self.done = False

    def volume_group(self):
        return STORY_VOLUMES

    def rows(self):
        return [Row(self.player.choice_text(a), lambda a=a: self.accept(a)) for a in self.choices]

    @property
    def action(self):
        return self.choices[self.index] if self.choices else None

    # ---- saying the choice -------------------------------------------------------
    def announce(self):
        """The choice's recorded clip, or the screen reader when it has none."""
        self.moved_at = self.clock()
        if self.action is None:
            self.say('Nothing to choose.')
            return
        clip = self.player.choice_clip(self.action)
        if clip:
            self.app.speech.stop()
            self.app.audio.slot('systemVoice').play(clip)
        else:
            self.app.audio.slot('systemVoice').stop()
            self.say(self.player.choice_text(self.action))

    def opened(self):
        if self.done:
            return
        self._clamp()
        self.announce()

    def moved(self):
        self.announce()

    def other_key(self, action, key, mods):
        if action == 'choice_text' and self.action is not None:
            self.moved_at = self.clock()
            self.say(self.player.choice_text(self.action))
        elif self.app.keymap.action_for(key, mods, STORY) == 'where':
            self.say(self.player.where())   # "Actions menu is open.", and the chapter
        else:
            self.announce()

    def focus_lost(self):
        """Losing the window closes the menu, then the story pauses (-[ActionsDialState
        blur])."""
        if self.done:
            return
        self.done = True
        self.app.audio.slot('systemVoice').stop()
        self.stack.pop()
        self.player.close_menu(quietly=True)
        if self.stack.top is not None:
            self.stack.top.focus_lost()

    # ---- choosing and closing ------------------------------------------------------
    def accept(self, action):
        self.done = True
        self.stack.pop()
        self.player.accept(action)

    def back(self):
        """Escape: close without choosing; the spiel plays on."""
        self.done = True
        self.app.audio.slot('systemVoice').stop()
        self.stack.pop()
        self.player.close_menu()

    def update(self):
        if not self.done and self.clock() - self.moved_at >= REPEAT_AFTER:
            self.announce()

    def lines(self):
        return ['Actions', ''] + super().lines()
