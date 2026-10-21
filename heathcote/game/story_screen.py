"""The story, as a screen (aidocks/plans/story_engine_plan.md).

It plays the story through ``StoryPlayer`` (game/player.py) and shows, for a sighted helper,
the spiel's label and its transcript. The story's own volume keys work here: master,
backgrounds and interface (platform/keymap.py).

Built a section at a time. For now, sections 2 and 3: it plays from ``start``, chaining on
by itself, and the actions menu key, Up or Enter, opens the actions menu
(game/actions_menu.py), or is refused while the spiel is locked out. Escape leaves for the
main menu; the other keys during play and the pause come in section 4. Until the menus
plan, the end of the story says so and returns to the main menu.

While another screen is on top of it, such as the F1 screen, the spiel waits, and plays on
when it is back on top. The actions menu pauses and resumes the spiel itself.
"""
from __future__ import annotations

import logging

from ..platform.keymap import STORY, STORY_VOLUMES
from ..ui.screens import Screen
from .actions_menu import ActionsMenu
from .player import StoryPlayer
from .state import StoryState
from .storydata import StoryData

log = logging.getLogger('story')

STORY_ENDED = 'The story has ended.'
#: Lines of transcript the window shows.
TRANSCRIPT_LINES = 16


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
        self.covered_by_menu = False

    def volume_group(self):
        return STORY_VOLUMES

    # ---- coming and going ------------------------------------------------------
    def opened(self):
        self.app.title_music = False
        if not self.started:
            self.started = True
            self.player.start()
        elif self.covered_now:
            self.covered_now = False
            if not self.covered_by_menu:
                self.app.audio.spiel.resume()

    def covered(self):
        self.covered_now = True
        self.covered_by_menu = self.player.menu_open    # the menu pauses and resumes it itself
        if not self.covered_by_menu:
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
        elif key == 'escape' and not mods:
            self.leave()                    # until section 4's pause
        return True

    def open_actions_menu(self):
        choices = self.player.open_menu()
        if choices is not None:
            self.stack.push(ActionsMenu(self.app, self.player, choices))

    def update(self):
        self.player.update()

    def lines(self):
        out = [self.story.label(self.player.current) if self.player.current else 'Story', '']
        text = self.player.transcript()
        if text:
            out += [line for line in text.splitlines() if line.strip()][:TRANSCRIPT_LINES]
        return out
