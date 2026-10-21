"""The story's actions menu (aidocks/plans/story_engine_plan.md, section 3).

It is plan 2's spoken menu (ui/menu.py), with the same keys, rebindable on F1: all four
arrows move, wrapping round, Home and End jump, Enter accepts, and Escape closes. It opens
on the first choice, the lowest ``order`` (-[Dial configure:], 0x10000dac0).

Each move plays the choice's recorded clip from ``speech/``, as the original announced it
(-[Dial announcePos], 0x10000eb30). A choice with no clip, "next room" or "just stop", is
said by the screen reader instead, since the original's synthesizer was a stub and said
nothing. After 7 seconds with no move, the choice plays again (-[ActionsDialState tick],
0x100037de0); the original's swipe hint is left out, as it does not fit a keyboard.

Once a choice's clip has finished, the screen reader speaks the choice's text, without
cutting anything off, the first time only: the 7-second repeat replays the clip alone
(aidocks/plans/choice_text_plan.md; the dev, 2026-10-21: "if you hover over a choice in the
menu, the text appears for that choice, but after the recording plays", and "I do not want
it to respeak the text every 7 seconds after the audio recording."). Moving on before the
clip ends cancels the text. This replaced Space's choice_text action.

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
        self.text_due = False           # the choice's text waits for its clip to finish

    def volume_group(self):
        return STORY_VOLUMES

    def rows(self):
        return [Row(self.player.choice_text(a), lambda a=a: self.accept(a)) for a in self.choices]

    @property
    def action(self):
        return self.choices[self.index] if self.choices else None

    # ---- saying the choice -------------------------------------------------------
    def announce(self, with_text=True):
        """The choice's recorded clip, its text to follow once the clip ends when
        ``with_text``; or the screen reader at once when it has no clip. The 7-second repeat
        leaves the text out."""
        self.moved_at = self.clock()
        self.text_due = False               # a choice left before its clip ended says nothing
        if self.action is None:
            self.say('Nothing to choose.')
            return
        clip = self.player.choice_clip(self.action)
        if clip:
            self.app.speech.stop()
            self.app.audio.slot('systemVoice').play(clip)
            self.text_due = with_text
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
        if self.app.keymap.action_for(key, mods, STORY) == 'where':
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
        if self.done:
            return
        if self.text_due and not self.app.audio.slot('systemVoice').playing:
            self.text_due = False           # the clip has finished: its text, once
            self.say(self.player.choice_text(self.action), interrupt=False)
        if self.clock() - self.moved_at >= REPEAT_AFTER:
            self.announce(with_text=False)

    def lines(self):
        return ['Actions', ''] + super().lines()
