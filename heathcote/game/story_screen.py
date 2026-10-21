"""The story, as a screen (aidocks/plans/story_engine_plan.md).

It plays the story through ``StoryPlayer`` (game/player.py) and shows, for a sighted helper,
the spiel's label and its transcript. The story's own volume keys work here: master,
backgrounds and interface (platform/keymap.py).

The keys during play, each an action in the key map's story group, rebindable on F1
(section 4; the dev, 2026-10-19: "I want the arrow keys to be rebindable, so yes."):

    Up or Enter    open the actions menu (game/actions_menu.py), or hear it refused
    Left           rewind, as the original's swipe right
    Right          fast-forward, as the original's swipe left
    Escape         pause, as the original's swipe down: the spiel stops, the backgrounds play
                   on muffled, and the pause menu opens
    Tab            say where you are, as the original's two-finger tap

Losing the window plays ``lost focus`` and pauses, closing the actions menu if it is open
(-[PlayState blur], 0x100033d98; -[ActionsDialState blur]).

Until the menus plan (aidocks/plans/menus_plan.md), the pause menu is a stand-in with
Resume and Return to menu, and the end of the story says so and returns to the main menu.

While another screen is on top of it, such as the F1 screen, the spiel waits, and plays on
when it is back on top. The actions menu and the pause pause and resume it themselves.
"""
from __future__ import annotations

import logging

from ..platform.keymap import STORY, STORY_VOLUMES
from ..ui.menu import Menu, Row
from ..ui.screens import Screen
from .actions_menu import ActionsMenu
from .player import StoryPlayer
from .state import StoryState
from .storydata import StoryData

log = logging.getLogger('story')

STORY_ENDED = 'The story has ended.'
#: Lines of transcript the window shows.
TRANSCRIPT_LINES = 16


class PauseMenu(Menu):
    """The stand-in pause menu, until the menus plan's: Resume, first and opened on, as
    Escape is too, and Return to menu, which leaves the story."""

    name = 'pause menu'
    title = 'Paused.'

    def __init__(self, app, story_screen):
        super().__init__(app)
        self.story_screen = story_screen

    def rows(self):
        return [Row('Resume', self.resume), Row('Return to menu', self.return_to_menu)]

    def resume(self):
        self.stack.pop()
        self.story_screen.player.resume()

    def back(self):
        self.resume()

    def return_to_menu(self):
        self.stack.pop()
        self.story_screen.leave()


class StoryScreen(Screen):
    name = 'story'

    def __init__(self, app, state=None, story=None):
        super().__init__(app)
        self.story = story or StoryData.shared()
        self.state = state or StoryState(self.story)
        self.player = StoryPlayer(app.audio, self.story, self.state, app.play_sound,
                                  after=app.loop.after)
        self.player.on_story_end = self.story_ended
        self.started = False
        self.covered_now = False
        self.covered_by_story = False

    def volume_group(self):
        return STORY_VOLUMES

    # ---- coming and going ------------------------------------------------------
    def opened(self):
        self.app.title_music = False
        if not self.started:
            self.started = True
            # Only now: a screen can be made before the main loop starts FMOD, as
            # story_check.py makes its own.
            self.app.audio.spiel.rewind_sound = self.story.sound_path('systemSounds', 'rewind')
            self.player.start()
        elif self.covered_now:
            self.covered_now = False
            if not self.covered_by_story:
                self.app.audio.spiel.resume()

    def covered(self):
        self.covered_now = True
        # The actions menu and the pause pause and resume the spiel themselves.
        self.covered_by_story = self.player.menu_open or self.player.paused
        if not self.covered_by_story:
            self.app.audio.spiel.pause()

    def closed(self):
        self.player.stop()

    def story_ended(self):
        self.say(STORY_ENDED)
        # Back to the main menu once the line is said: until the menus plan's credits.
        self.app.loop.after(2.0, self.leave)

    def leave(self):
        if self.stack.top is self:
            self.stack.pop()

    # ---- keys and frames --------------------------------------------------------
    def handle_key(self, key, mods):
        self.player.poke()
        action = self.app.keymap.action_for(key, mods, STORY)
        if action == 'actions_menu':
            self.open_actions_menu()
        elif action == 'rewind':
            self.player.rewind()
        elif action == 'fast_forward':
            self.player.fast_forward()
        elif action == 'pause':
            self.pause()
        elif action == 'where':
            self.say(self.player.where())
        return True

    def open_actions_menu(self):
        choices = self.player.open_menu()
        if choices is not None:
            self.stack.push(ActionsMenu(self.app, self.player, choices))

    def pause(self):
        if self.player.pause():
            self.stack.push(PauseMenu(self.app, self))

    def focus_lost(self):
        """The window lost the keyboard: lost focus, and the story pauses."""
        if self.player.phase is None or self.player.paused:
            return
        self.app.play_sound('lost focus')
        if self.player.pause():
            self.stack.push(PauseMenu(self.app, self))

    def update(self):
        self.player.update()

    def lines(self):
        out = [self.story.label(self.player.current) if self.player.current else 'Story', '']
        text = self.player.transcript()
        if text:
            out += [line for line in text.splitlines() if line.strip()][:TRANSCRIPT_LINES]
        return out
