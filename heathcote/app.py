"""The game's main loop: the window, the keys, the timers and the stack of screens.

``Heathcote.py`` builds an ``App`` and runs it. Every frame, sixty a second, it:

1. reads the window's events: closing the window quits, losing the keyboard tells the top
   screen (the story pauses), and a key goes to the top screen;
2. lets FMOD do its work (platform/audio.py), and runs the timers that are due
   (platform/runloop.py);
3. draws the top screen's text in the window, for a sighted helper.

Two kinds of key are handled here, before the top screen sees them
(aidocks/plans/foundation_plan.md):

* F1 opens the key bindings screen from anywhere, and the timers are held while it is
  open, so the story's timed sets keep their places.
* The volume keys: the master's on every screen, then those the top screen allows
  (``Screen.volume_group``), the background and interface volumes in the story, and the
  title volume wherever the title music plays. Each press says the new level, and holding one down moves it on
  step by step; every other key fires once however long it is held.
"""
from __future__ import annotations

import logging

from . import paths
from .platform import runloop
from .platform.audio import Audio
from .platform.keymap import MASTER_VOLUME, MODIFIER_KEYS, KeyMap, mods_from_pygame
from .platform.runloop import RunLoop
from .platform.settings import VOLUME_LABELS, Settings
from .platform.speech import Speech
from .ui.keybind_screen import KeyBindScreen
from .ui.screens import ScreenStack

log = logging.getLogger('app')

TITLE = 'Heathcote'
WINDOW_SIZE = (800, 500)
FPS = 60
#: The window's text, in lines from the top; the rest is cut.
MAX_LINES = 22
#: Seconds a volume key is held before it starts repeating. The time between repeats is the
#: Volume speed setting (aidocks/plans/settings_plan.md).
REPEAT_DELAY = 0.4
#: The volume keys' actions: (setting, steps per press).
VOLUME_ACTIONS = {
    'master_up': ('master_volume', 1), 'master_down': ('master_volume', -1),
    'backgrounds_up': ('backgrounds_volume', 1), 'backgrounds_down': ('backgrounds_volume', -1),
    'interface_up': ('interface_volume', 1), 'interface_down': ('interface_volume', -1),
    'title_up': ('title_volume', 1), 'title_down': ('title_volume', -1),
}


class App:
    def __init__(self, options, speech=None, settings=None, keymap=None, loop=None, audio=None,
                 progress=None):
        self.options = options
        # The story's progress between runs (game/progress.py), read when first wanted.
        self._progress = progress
        self.speech = speech or Speech.shared()
        self.settings = settings or Settings.shared()
        self.keymap = keymap or KeyMap.shared()
        self.loop = loop or RunLoop.main()
        # FMOD starts in run(), once there is a window (aidocks/plans/audio_plan.md).
        self.audio = audio or Audio(self.settings)
        self.stack = ScreenStack()
        self.running = True
        self.held = None            # [key, mods, action, when it next repeats] for a volume key
        self.pygame = None          # pygame, once run() has opened the window
        self.last_char = ''         # the character the key being handled typed, for text entry
        # The spiel --spiel named, in debug mode: Start story begins there.
        self.start_spiel = None
        self.debug = False
        # Whether the title music is playing, so the title volume's keys work: set by
        # start_title_music() and stop_title_music().
        self.title_music = False
        # Debug mode is for source runs only: --debug turns it on for one run, and the
        # Settings row turns it on or off for good.
        self.set_debug(bool(getattr(options, 'debug', False) or self.settings.get('debug')),
                       remember=False)

    @property
    def progress(self):
        """The story's progress, ``saves/progress.json`` (aidocks/plans/saves_plan.md)."""
        if self._progress is None:
            from .game.progress import Progress
            self._progress = Progress.shared()
        return self._progress

    # ---- debug mode -----------------------------------------------------
    def set_debug(self, on, remember=True):
        """Turn debug mode on or off, at once. Never on in a built game."""
        on = bool(on) and not paths.FROZEN
        self.debug = on
        self.keymap.debug = on
        self.retitle()
        if remember and self.settings.get('debug') != on:
            self.settings.set('debug', on)
        log.info('debug mode %s', 'on' if on else 'off')

    def window_title(self):
        return '%s (debug)' % TITLE if self.debug else TITLE

    def retitle(self):
        """Give the window its title, at once, once there is a window."""
        if self.pygame is not None:
            self.pygame.display.set_caption(self.window_title())

    # ---- volumes --------------------------------------------------------
    def step_volume(self, action):
        """A volume key: move that volume one step and say where it is now."""
        key, steps = VOLUME_ACTIONS[action]
        level = self.settings.step_volume(key, steps)
        self.volumes_changed()
        self.speech.speak('%s, %d percent.' % (VOLUME_LABELS[key], level))

    def volumes_changed(self):
        """Hand the new volumes to FMOD, at once."""
        self.audio.apply_volumes()

    # ---- interface sounds -------------------------------------------------
    def play_sound(self, label):
        """One of the original's interface sounds by its label, such as 'click-good', on a
        channel of its own, so two can sound together."""
        from .game.storydata import StoryData
        path = StoryData.shared().sound_path('systemSounds', label)
        if path is None:
            log.warning('there is no interface sound labelled %s', label)
            return
        self.audio.play_oneshot(path)

    # ---- the title music ----------------------------------------------------
    def start_title_music(self):
        """The title music, under the main menu (aidocks/plans/menus_plan.md): at once,
        looping, at the title volume, while the story group fades out over 2 seconds, as
        the original's did (-[GameView titleMusicShouldBePlaying], 0x100019594). Never
        started twice."""
        if self.title_music:
            return
        self.title_music = True
        if not self.audio.ok:
            return
        from .game.storydata import StoryData
        path = StoryData.shared().sound_path('bgm', 'title')
        if path is None:
            log.warning('there is no title music')
        else:
            self.audio.slot('titleBgm').play(path)
        self.audio.fade_story(0.0, 2.0)

    def stop_title_music(self):
        """Fade the title music out over 3 seconds, and the story group in over 1, as the
        story is entered (-[GameView titleMusicShouldNotBePlaying], 0x1000196dc)."""
        if not self.title_music:
            return
        self.title_music = False
        if not self.audio.ok:
            return
        self.audio.slot('titleBgm').stop(fade_out=3.0)
        self.audio.fade_story(1.0, 1.0)

    # ---- running --------------------------------------------------------
    def quit(self):
        self.running = False

    def open_key_bindings(self):
        if isinstance(self.stack.top, KeyBindScreen):
            return
        self.loop.hold()
        self.stack.push(KeyBindScreen(self))

    def volume_action(self, key, mods):
        """The volume action this key does on the top screen, or None: the master's on every
        screen, then whichever volumes the screen allows."""
        top = self.stack.top
        if top is None or isinstance(top, KeyBindScreen):
            return None
        action = self.keymap.action_for(key, mods, MASTER_VOLUME)
        if action is None:
            group = top.volume_group()
            action = self.keymap.action_for(key, mods, group) if group else None
        return action if action in VOLUME_ACTIONS else None

    def key_down(self, key, mods, now=None, char=''):
        """A key pressed: pygame's name for it, the modifiers held, and the character it
        typed, which a screen taking text, such as debug mode's spiel search, reads from
        ``last_char``."""
        if key in MODIFIER_KEYS:
            return                          # Shift and the rest only go with another key
        self.last_char = char or ''
        self.held = None
        top = self.stack.top
        if isinstance(top, KeyBindScreen):
            top.handle_key(key, mods)       # every key, so any key can be bound
            if top is not self.stack.top:
                self.loop.resume()          # the F1 screen just closed
            return
        if key == 'f1' and not mods:
            self.open_key_bindings()
            return
        action = self.volume_action(key, mods)
        if action is not None:
            self.step_volume(action)
            now = runloop.clock() if now is None else now
            self.held = [key, list(mods), action, now + REPEAT_DELAY]
            return
        if top is not None:
            top.handle_key(key, mods)

    def key_up(self, key):
        """A key let go: it stops repeating, as it does when a modifier held with it is."""
        if self.held is not None and (key == self.held[0] or key in MODIFIER_KEYS):
            self.held = None

    def repeat_keys(self, now=None):
        """Called once a frame: step the held volume again when it is due."""
        if self.held is None:
            return
        now = runloop.clock() if now is None else now
        if now < self.held[3]:
            return
        if self.volume_action(self.held[0], self.held[1]) != self.held[2]:
            self.held = None                # the screen changed under the held key
            return
        self.held[3] = now + self.settings.get('volume_speed') / 1000.0
        self.step_volume(self.held[2])

    def run(self, first_screen, pygame):
        """The main loop. Returns when the game quits or the last screen closes."""
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode(WINDOW_SIZE)
        self.pygame = pygame
        self.retitle()
        font = pygame.font.SysFont('consolas', 18) or pygame.font.Font(None, 22)
        clock = pygame.time.Clock()
        self.audio.open()
        exit_after = getattr(self.options, 'exit_after', None)
        if exit_after:
            self.loop.after(exit_after, self.quit)
            log.info('quitting by itself after %g seconds', exit_after)
        self.stack.push(first_screen)
        try:
            while self.running and not self.stack.empty:
                for event in pygame.event.get():
                    self.handle_event(event, pygame)
                self.repeat_keys()
                if self.stack.top is not None:
                    self.stack.top.update()
                self.audio.update()
                self.loop.pump()
                self.draw(screen, font, pygame)
                clock.tick(FPS)
        finally:
            self.stack.clear()
            self.audio.close()
            pygame.display.quit()

    def handle_event(self, event, pygame):
        if event.type == pygame.QUIT:
            self.quit()
        elif event.type == getattr(pygame, 'WINDOWFOCUSLOST', None):
            self.held = None                # its key-up will go to another window
            if self.stack.top is not None:
                self.stack.top.focus_lost()
        elif event.type == getattr(pygame, 'WINDOWFOCUSGAINED', None):
            if self.stack.top is not None:
                self.stack.top.focus_gained()
        elif event.type == pygame.KEYDOWN:
            self.key_down(pygame.key.name(event.key), mods_from_pygame(event.mod, pygame),
                          char=getattr(event, 'unicode', ''))
        elif event.type == pygame.KEYUP:
            self.key_up(pygame.key.name(event.key))

    def draw(self, screen, font, pygame):
        """The top screen's text, then the last line spoken, for a sighted helper."""
        screen.fill((0, 0, 0))
        lines = self.stack.top.lines() if self.stack.top is not None else []
        lines = list(lines)[:MAX_LINES - 2]
        if self.speech.last:
            lines += ['', self.speech.last]
        y = 10
        for line in lines:
            if line:
                screen.blit(font.render(str(line), True, (230, 230, 230)), (12, y))
            y += font.get_linesize()
        pygame.display.flip()
