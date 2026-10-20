"""Hear the game's sound by ear, through FMOD (aidocks/plans/audio_plan.md).

    python tests/interact/audio_check.py

It grows with each section of the audio plan. For now, section 1: the title music, an
ambience loop, the interface sounds and the four volumes. The keys:

    1                    the title music: start it, fading in, or stop it, fading out over 3 seconds
    2                    the ambience loop: start it, fading in, or stop it, fading out over 2 seconds
    Up and Down          choose the ambience; a playing loop changes to it at once
    Left and Right       choose an interface sound, saying its name
    Space                play the interface sound chosen
    Shift+Home, Shift+End        the master volume, up and down
    Page Up, Page Down           the background volume: the ambience loop
    Shift+Page Up, Shift+Page Down   the interface volume: the interface sounds
    Control+Page Up, Control+Page Down   the title volume: the title music
    Enter                say what is playing, and every volume
    Escape               quit

Each volume step is 6 decibels, so every press should sound like the same change, and 0
percent is silent. It keeps its own save under %APPDATA%\\Heathcote\\interact\\audio_check,
so its volumes never change the game's.
"""
from __future__ import annotations

import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
os.environ.setdefault('HEATHCOTE_USER_DIR', os.path.join(
    os.environ.get('APPDATA') or os.path.expanduser('~'), 'Heathcote', 'interact', 'audio_check'))

import pygame  # noqa: E402

from heathcote import paths  # noqa: E402
from heathcote.game.storydata import StoryData  # noqa: E402
from heathcote.platform.audio import Audio  # noqa: E402
from heathcote.platform.keymap import mods_from_pygame  # noqa: E402
from heathcote.platform.settings import VOLUME_LABELS, Settings  # noqa: E402
from heathcote.platform.speech import Speech  # noqa: E402

#: (key, modifiers): (volume, steps)
VOLUME_KEYS = {
    ('home', ('shift',)): ('master_volume', 1), ('end', ('shift',)): ('master_volume', -1),
    ('page up', ()): ('backgrounds_volume', 1), ('page down', ()): ('backgrounds_volume', -1),
    ('page up', ('shift',)): ('interface_volume', 1), ('page down', ('shift',)): ('interface_volume', -1),
    ('page up', ('ctrl',)): ('title_volume', 1), ('page down', ('ctrl',)): ('title_volume', -1),
}


class Check:
    def __init__(self):
        self.speech = Speech.shared()
        self.settings = Settings.shared()
        self.audio = Audio(self.settings)
        self.story = StoryData.shared()
        self.ambiences = [(self.story.label(s), self.story.audio_path(s))
                          for s in self.story.refs('ambience') if self.story.audio_path(s)]
        self.sounds = [(self.story.label(s), self.story.audio_path(s))
                       for s in self.story.refs('systemSounds') if self.story.audio_path(s)]
        self.title = self.story.sound_path('bgm', 'title')
        self.ambience_index = 0
        self.sound_index = 0
        self.running = True

    def say(self, text):
        self.speech.speak(text)

    # ---- the title music and the ambience ---------------------------------
    def toggle_title(self):
        slot = self.audio.slot('titleBgm')
        if slot.playing:
            slot.stop(fade_out=3.0)
            self.say('Title music fading out.')
        else:
            slot.play(self.title, fade_in=0.5)
            self.say('Title music.')

    def toggle_ambience(self):
        slot = self.audio.slot('ambience1')
        if slot.playing:
            slot.stop(fade_out=2.0)
            self.say('Ambience fading out.')
        else:
            label, path = self.ambiences[self.ambience_index]
            slot.play(path, fade_in=0.5)
            self.say('Ambience: %s.' % label)

    def choose_ambience(self, step):
        self.ambience_index = (self.ambience_index + step) % len(self.ambiences)
        label, path = self.ambiences[self.ambience_index]
        slot = self.audio.slot('ambience1')
        if slot.playing:
            slot.play(path)
        self.say('%s, %d of %d.' % (label, self.ambience_index + 1, len(self.ambiences)))

    # ---- the interface sounds ---------------------------------------------
    def choose_sound(self, step):
        self.sound_index = (self.sound_index + step) % len(self.sounds)
        self.say('%s, %d of %d.' % (self.sounds[self.sound_index][0], self.sound_index + 1,
                                    len(self.sounds)))

    def play_sound(self):
        self.audio.slot('sfx').play(self.sounds[self.sound_index][1])

    # ---- the volumes -------------------------------------------------------
    def step_volume(self, key, steps):
        level = self.settings.step_volume(key, steps)
        self.audio.apply_volumes()
        self.say('%s, %d percent.' % (VOLUME_LABELS[key], level))

    def status(self):
        playing = []
        if self.audio.slot('titleBgm').playing:
            playing.append('the title music')
        if self.audio.slot('ambience1').playing:
            playing.append('the ambience %s' % self.ambiences[self.ambience_index][0])
        volumes = ', '.join('%s %d' % (VOLUME_LABELS[k], self.settings.get(k)) for k in VOLUME_LABELS)
        self.say('%s. %s.' % ('Playing ' + ' and '.join(playing) if playing else 'Nothing is playing',
                              volumes))

    def key(self, key, mods):
        volume = VOLUME_KEYS.get((key, tuple(mods)))
        if volume:
            self.step_volume(*volume)
        elif mods:
            return
        elif key == 'escape':
            self.running = False
        elif key == '1':
            self.toggle_title()
        elif key == '2':
            self.toggle_ambience()
        elif key in ('up', 'down'):
            self.choose_ambience(-1 if key == 'up' else 1)
        elif key in ('left', 'right'):
            self.choose_sound(-1 if key == 'left' else 1)
        elif key == 'space':
            self.play_sound()
        elif key in ('return', 'enter'):
            self.status()

    def run(self):
        pygame.display.init()
        pygame.display.set_caption('Heathcote audio check')
        pygame.display.set_mode((640, 480))
        self.audio.open()
        self.say('Audio check. Press 1 for the title music, 2 for an ambience loop, Space for '
                 'an interface sound, and Enter for what is playing. Escape quits.')
        clock = pygame.time.Clock()
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        self.key(pygame.key.name(event.key), mods_from_pygame(event.mod, pygame))
                self.audio.update()
                clock.tick(60)
        finally:
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
