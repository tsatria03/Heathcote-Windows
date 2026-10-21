"""Play the story by ear, by the original's rules (aidocks/plans/story_engine_plan.md).

    python tests/interact/story_check.py

It grows with each section of the story engine plan. For now, section 2: the story plays
from its start and moves on by itself wherever a spiel leads straight into the next, with
its music and ambience in context, to the end of the first scene, where its idle loop and
menu-available play. Choosing what happens next comes with section 3. The keys:

    Enter                start the story from its beginning, or start it again
    Comma and Full stop  choose a spiel, saying its label, and "leads on" when it has next spiels;
                         with Shift, 10 at a time. The story's start ends its scene by itself,
                         so to hear spiels leading on, choose one that leads on
    3                    play the spiel chosen, with the story's state as it is
    Tab                  say where the story is: the spiel, how far in, and whether it has ended
    V                    turn saying each spiel's label as it begins on or off; on at first
    Shift+Home, Shift+End        the master volume
    Page Up, Page Down           the background volume
    Shift+Page Up, Shift+Page Down   the interface volume
    Escape               quit

It keeps its own save under %APPDATA%\\Heathcote\\interact\\story_check, so nothing here
ever changes the game's own volumes, keys or progress.
"""
from __future__ import annotations

import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
os.environ.setdefault('HEATHCOTE_USER_DIR', os.path.join(
    os.environ.get('APPDATA') or os.path.expanduser('~'), 'Heathcote', 'interact', 'story_check'))

import pygame  # noqa: E402

from heathcote import paths  # noqa: E402
from heathcote.game.player import PLAYING, SCENE_END, STORY_END, StoryPlayer  # noqa: E402
from heathcote.game.state import StoryState  # noqa: E402
from heathcote.game.storydata import StoryData  # noqa: E402
from heathcote.platform.audio import Audio  # noqa: E402
from heathcote.platform.keymap import mods_from_pygame  # noqa: E402
from heathcote.platform.settings import VOLUME_LABELS, Settings  # noqa: E402
from heathcote.platform.speech import Speech  # noqa: E402

#: (key, modifiers): (volume, steps): the story's own volumes.
VOLUME_KEYS = {
    ('home', ('shift',)): ('master_volume', 1), ('end', ('shift',)): ('master_volume', -1),
    ('page up', ()): ('backgrounds_volume', 1), ('page down', ()): ('backgrounds_volume', -1),
    ('page up', ('shift',)): ('interface_volume', 1), ('page down', ('shift',)): ('interface_volume', -1),
}


class Check:
    def __init__(self):
        self.speech = Speech.shared()
        self.settings = Settings.shared()
        self.audio = Audio(self.settings)
        self.story = StoryData.shared()
        self.state = StoryState(self.story)
        self.player = None
        self.announce = True
        self.running = True
        self.spiels = [s for s in self.story.refs('actionSpiels') if self.story.record(s)]
        self.spiel_index = 0

    def say(self, text, interrupt=True):
        self.speech.speak(text, interrupt)

    def play_sound(self, label):
        path = self.story.sound_path('systemSounds', label)
        if path:
            self.audio.slot('sfx').play(path)

    # ---- the story -------------------------------------------------------------
    def new_player(self):
        if self.player is not None:
            self.player.stop()
        self.player = StoryPlayer(self.audio, self.story, self.state, self.play_sound)
        self.player.audio.spiel.rewind_sound = self.story.sound_path('systemSounds', 'rewind')
        self.player.on_spiel = self.spiel_began
        self.player.on_scene_end = self.scene_ended
        self.player.on_story_end = lambda: self.say('The story has ended.')

    def start(self):
        """The story from its beginning, with the state reset."""
        self.state.reset()
        self.new_player()
        self.player.start()

    def choose(self, step):
        self.spiel_index = (self.spiel_index + step) % len(self.spiels)
        soft = self.spiels[self.spiel_index]
        leads = ', leads on' if (self.story.record(soft) or {}).get('next') else ''
        silent = ', no recording' if not (self.story.record(soft) or {}).get('file') else ''
        self.say('%s%s%s, %d of %d.' % (self.story.label(soft), leads, silent,
                                        self.spiel_index + 1, len(self.spiels)))

    def play_chosen(self):
        """The spiel chosen, with the state as it is, so its next spiels follow from it."""
        self.new_player()
        self.player.play(self.spiels[self.spiel_index])

    def spiel_began(self, soft):
        if self.announce:
            self.say(self.story.label(soft), interrupt=False)

    def scene_ended(self, soft):
        if self.announce:
            self.say('End of scene: %s.' % self.story.label(soft), interrupt=False)

    def where(self):
        p = self.player
        if p is None or p.current is None:
            self.say('The story has not started. Press Enter to start it.')
            return
        label = self.story.label(p.current)
        if p.phase == SCENE_END:
            self.say('End of scene: %s.' % label)
        elif p.phase == STORY_END:
            self.say('The story has ended, at %s.' % label)
        elif p.phase == PLAYING:
            self.say('%s, %.0f of %.0f seconds.' % (label, p.position, self.audio.spiel.length))

    # ---- the keys ------------------------------------------------------------
    def key(self, key, mods):
        volume = VOLUME_KEYS.get((key, tuple(mods)))
        if volume:
            level = self.settings.step_volume(*volume)
            self.audio.apply_volumes()
            self.say('%s, %d percent.' % (VOLUME_LABELS[volume[0]], level))
        elif key in (',', '.') and mods in ([], ['shift']):
            self.choose((-1 if key == ',' else 1) * (10 if mods else 1))
        elif mods:
            return
        elif key == '3':
            self.play_chosen()
        elif key == 'escape':
            self.running = False
        elif key in ('return', 'enter'):
            self.start()
        elif key == 'tab':
            self.where()
        elif key == 'v':
            self.announce = not self.announce
            self.say('Spiel labels %s.' % ('on' if self.announce else 'off'))

    def run(self):
        pygame.display.init()
        pygame.display.set_caption('Heathcote story check')
        pygame.display.set_mode((640, 480))
        self.audio.open()
        self.say('Story check. Press Enter to start the story, or choose a spiel with Comma and '
                 'Full stop and play it with 3. Tab says where the story is, and V turns the '
                 'spiel labels on or off. Escape quits.')
        clock = pygame.time.Clock()
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        self.key(pygame.key.name(event.key), mods_from_pygame(event.mod, pygame))
                if self.player is not None:
                    self.player.update()
                self.audio.update()
                clock.tick(60)
        finally:
            if self.player is not None:
                self.player.stop()
            self.audio.close()
            pygame.display.quit()


def main():
    logging.basicConfig(filename=os.path.join(paths.logs_dir(), 'log.txt'), filemode='w',
                        level=logging.DEBUG, encoding='utf-8',
                        format='%(asctime)s %(levelname)-7s %(name)-9s %(message)s')
    try:
        Check().run()
    except SystemExit as stop:
        if isinstance(stop.code, str):
            Speech.shared().speak(stop.code)
            print(stop.code)
            pygame.time.wait(4000)
        raise


if __name__ == '__main__':
    main()
