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

In debug mode only (section 5): F2 skips to the end of the spiel, its waiting timed sets
and lane events firing on the way; F3 finds a spiel by part of its label and jumps to it,
the variables kept as they are; and F4 speaks every variable that is not "0".

Losing the window plays ``lost focus`` and pauses, closing the actions menu if it is open
(-[PlayState blur], 0x100033d98; -[ActionsDialState blur]). Getting the window back resumes
by itself, unlike the original, which stayed paused; a pause made with Escape stays.

The pause menu has Resume, Restart story, Settings and Return to menu
(aidocks/plans/menus_plan.md, section 3). Return to menu takes the story off the stack
still paused, kept as ``app.paused_story``, and the main menu's Continue story puts it back.
When the story ends, the end credits open over it (game/credits.py, section 4), and it
plays on beneath them until they are left.

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
from .state import LOCATION, StoryState
from .storydata import StoryData

log = logging.getLogger('story')

#: Lines of transcript the window shows.
TRANSCRIPT_LINES = 16


RESTART_QUESTION = 'Restart the story? Your progress will be lost.'


class RestartMenu(Menu):
    """Restart story asks first, as the original's restart did, with No first and opened
    on; Escape is No too."""

    name = 'restart question'
    title = RESTART_QUESTION

    def __init__(self, app, story_screen):
        super().__init__(app)
        self.story_screen = story_screen

    def rows(self):
        return [Row('No', self.back), Row('Yes', self.restart)]

    def restart(self):
        self.stack.pop()                    # this question
        self.stack.pop()                    # the pause menu, back to the story
        self.story_screen.restart()


class PauseMenu(Menu):
    """The pause menu (aidocks/plans/menus_plan.md, section 3). Escape during the story
    pauses as the original did, and opens it:

        Resume          first and opened on; Escape does the same
        Restart story   asks first, then plays the story again from its start
        Settings        the same screen as the main menu's
        Return to menu  leaves the story paused, so Continue story picks it up exactly
                        there, as the original did; it does not ask, since nothing is lost
    """

    name = 'pause menu'
    title = 'Paused.'

    def __init__(self, app, story_screen, by_focus=False):
        """``by_focus``: opened because the window lost the keyboard, so getting it back
        resumes by itself."""
        super().__init__(app)
        self.story_screen = story_screen
        self.by_focus = by_focus

    def focus_gained(self):
        """Back in the game's window: a pause that losing the window made ends by itself
        (the dev, 2026-10-20: "Coming back out of the game's window should auto resume the
        game."), unlike the original, which stayed paused. A pause made with Escape stays."""
        if self.by_focus and self.stack.top is self:
            self.resume()

    def rows(self):
        from ..ui.settings_screen import SettingsScreen
        return [Row('Resume', self.resume),
                Row('Restart story', lambda: self.stack.push(RestartMenu(self.app, self.story_screen))),
                Row('Settings', lambda: self.stack.push(SettingsScreen(self.app))),
                Row('Return to menu', self.return_to_menu)]

    def resume(self):
        self.stack.pop()
        self.story_screen.player.resume()

    def back(self):
        self.resume()

    def return_to_menu(self):
        self.stack.pop()
        self.story_screen.return_to_menu()


class StoryScreen(Screen):
    name = 'story'

    def __init__(self, app, state=None, story=None, start_at=None, lanes=None, saving=True):
        """``start_at``, a spiel's softRef, starts the story there instead of at ``start``:
        Continue story's saved spiel, with ``lanes``, what the four lanes held as it began,
        or --spiel's in debug mode. ``saving`` False writes no progress, as after a debug
        mode jump (aidocks/plans/saves_plan.md)."""
        super().__init__(app)
        self.story = story or StoryData.shared()
        self.state = state or StoryState(self.story)
        self.start_at = start_at
        self.start_lanes = lanes
        self.saving = saving
        self.search = None
        self.last_search = None
        self.player = StoryPlayer(app.audio, self.story, self.state, app.play_sound,
                                  after=app.loop.after)
        self.player.on_story_end = self.story_ended
        # The progress, written as the original wrote every change (aidocks/plans/saves_plan.md).
        self.player.on_spiel = self.save_spiel
        self.player.on_scene_end = self.save_heard
        self.player.on_changed = self.save_chapter
        self.started = False
        self.covered_now = False
        self.covered_by_story = False
        self.kept = False               # taken off the stack, paused, for Continue story
        self.ending = False             # the end credits are up, the story playing on beneath

    def volume_group(self):
        return STORY_VOLUMES

    # ---- coming and going ------------------------------------------------------
    def opened(self):
        self.app.stop_title_music()         # fading out over 3 seconds as the story starts
        if not self.started:
            self.started = True
            # Only now: a screen can be made before the main loop starts FMOD, as
            # story_check.py makes its own.
            self.app.audio.spiel.rewind_sound = self.story.sound_path('systemSounds', 'rewind')
            if self.start_lanes is not None:
                # Continue story: the lanes held as the saved spiel began, fading in over
                # 0.5 seconds, as the original's story opened (+[StoryView go], 0x100025ce8).
                self.player.lanes.restore(self.start_lanes)
            if self.start_at:
                self.player.play(self.start_at)
            else:
                self.player.start()
        elif self.covered_now:
            self.covered_now = False
            if not self.covered_by_story:
                self.app.audio.spiel.resume()

    def covered(self):
        self.covered_now = True
        # The actions menu and the pause pause and resume the spiel themselves, and the end
        # credits leave it playing.
        self.covered_by_story = self.player.menu_open or self.player.paused or self.ending
        if not self.covered_by_story:
            self.app.audio.spiel.pause()

    def closed(self):
        if not self.kept:
            self.player.stop()

    # ---- the pause menu's rows ------------------------------------------------------
    def return_to_menu(self):
        """Back to the main menu, the story left paused under it, its backgrounds muffled and
        fading out under the title music, so Continue story picks it up exactly here
        (+[StoryView returnToTitle], 0x100025614)."""
        self.kept = True
        self.app.paused_story = self
        self.leave()

    def continue_story(self):
        """Continue story, from the main menu: back on the stack, the title music fading out
        and the story fading in, and unpaused (+[StoryView go], 0x100025ce8)."""
        self.kept = False
        if self.app.paused_story is self:
            self.app.paused_story = None
        self.stack.push(self)
        self.player.resume()

    def restart(self):
        """Restart story, said yes to: the variables, the heard spiels and the actions'
        counts back to a story never played, and the story again from ``start``, as the
        original's restart (-[ViewController resetGameState], 0x100011068). The settings
        and the first-run notice stay as they are."""
        self.say('The story starts again.')     # cutting off the pause menu, reopened on the way
        self.player.stop()
        self.state.reset()
        self.saving = True                  # a fresh story, even after a debug mode jump
        self.app.progress.clear()
        self.player.start()                 # which writes its start as the new progress

    # ---- the progress --------------------------------------------------------------
    def save_spiel(self, soft):
        """A spiel begins: where Continue story will pick up, with the state and the lanes
        as they are now."""
        if self.saving:
            self.app.progress.begin(soft, self.state, self.player.lanes.opening)

    def save_heard(self, soft):
        if self.saving:
            self.app.progress.mark_heard(soft)

    def save_chapter(self, changes):
        """The chapter Continue story names, kept apart from the spiel's snapshot."""
        if not self.saving:
            return
        location = self.state.variable(LOCATION)
        for var, _old, new in changes:
            if var == location:
                self.app.progress.set_chapter(new)

    def stop_saving(self):
        """Debug mode jumped: this story writes no more progress, so testing never
        overwrites the real one."""
        if self.saving:
            self.saving = False
            log.info('a debug mode jump: this story writes no progress from here')

    def story_ended(self):
        """The story set ``end``: the end credits open over it, and it plays on beneath."""
        from .credits import EndCredits
        self.ending = True
        # The story is over, so quitting now offers Start story next time; nothing more is
        # written while its last moments play on.
        if self.saving:
            self.app.progress.clear()
            self.saving = False
        self.stack.push(EndCredits(self.app, self))

    def end_story(self):
        """Leaving the end credits: ``pause-pause``, the story reset, and the main menu."""
        self.app.play_sound('pause-pause')
        self.state.reset()
        self.leave()

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
        elif action == 'debug_skip':
            if not self.player.skip():
                self.say('Nothing to skip.')
        elif action == 'debug_jump':
            self.find_spiel()
        elif action == 'debug_variables':
            self.say(self.player.variables_text())
        return True

    # ---- debug mode's jump --------------------------------------------------------
    def find_spiel(self):
        """F3: find a spiel by part of its label, and jump there."""
        from ..ui.search import SearchScreen
        names = [(self.story.label(s), s) for s in self.story.refs('actionSpiels') if self.story.record(s)]
        self.search = SearchScreen(self.app, 'Jump to a spiel: type part of its label, then Enter. '
                                   'Escape cancels.', names, self.jump_to, last=self.last_search)
        self.stack.push(self.search)

    def jump_to(self, soft, label, number, count):
        self.last_search = self.search.result
        self.say('%s, %d of %d matches.' % (label, number, count))
        self.stop_saving()
        self.player.jump(soft)

    def open_actions_menu(self):
        choices = self.player.open_menu()
        if choices is not None:
            self.stack.push(ActionsMenu(self.app, self.player, choices))

    def pause(self):
        if self.player.pause():
            self.stack.push(PauseMenu(self.app, self))

    def focus_lost(self):
        """The window lost the keyboard: lost focus, and the story pauses until the window
        has the keyboard again."""
        if self.player.phase is None or self.player.paused:
            return
        self.app.play_sound('lost focus')
        if self.player.pause():
            self.stack.push(PauseMenu(self.app, self, by_focus=True))

    def update(self):
        self.player.update()

    def lines(self):
        out = [self.story.label(self.player.current) if self.player.current else 'Story', '']
        text = self.player.transcript()
        if text:
            out += [line for line in text.splitlines() if line.strip()][:TRANSCRIPT_LINES]
        return out
