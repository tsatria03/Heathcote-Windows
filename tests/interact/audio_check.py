"""Hear the game's sound by ear, through FMOD (aidocks/plans/audio_plan.md).

    python tests/interact/audio_check.py

It grew with each section of the audio plan, and now has all of it: the title music, an
ambience loop, the interface sounds, the four volumes, and any spiel, found by its label,
with pause, rewind and fast-forward, playing with its own music and ambience lanes, which
change on cue and are set up again after a rewind, and its idle loop when it ends. The
keys:

    1                    the title music: start it, fading in, or stop it, fading out over 3 seconds
    2                    the ambience loop: start it, fading in, or stop it, fading out over 2 seconds
    Up and Down          choose the ambience; a playing loop changes to it at once
    [ and ]              choose an interface sound, saying its name
    Space                play the interface sound chosen
    Comma and Full stop  choose a spiel, saying its label; with Shift, 10 at a time; a spiel
                         that is playing changes to the one chosen at once
    3                    play the spiel chosen from its start, with its lanes, or stop it and its lanes
    S                    find a spiel by its label: type part of it, such as "cells", then Enter
                         plays the first match; the same text again moves to the next match.
                         Each letter is spoken as typed, Backspace takes one off, and Escape gives
                         up. The labels are the "Spiel:" headings of analysis/script/Heathcote.txt.
                         A spiel found this way starts with every lane silent, so only its own
                         cues are heard
    Left                 rewind, as the original: back 1 second every 7 ticks for 0.75 seconds
    Right                fast-forward, as the original: 1.75 times for 1.5 seconds, voices kept at pitch
    P                    pause as the original: the spiel stops, and the ambience and music play on,
                         muffled by the hush; P again resumes and unmuffles them
    Tab                  say where the spiel is, in seconds
    L                    say what each lane holds, and the idle loop
    F                    fade the whole story out over 2 seconds, or back in over 1, as the original
    Shift+Home, Shift+End        the master volume, up and down
    Page Up, Page Down           the background volume: the ambience loop
    Shift+Page Up, Shift+Page Down   the interface volume: the interface sounds
    Control+Page Up, Control+Page Down   the title volume: the title music
    Enter                say what is playing, and every volume
    Escape               quit

Each volume step is 6 decibels, so every press should sound like the same change, and 0
percent is silent. Key 2's ambience plays on the first ambience lane, so a spiel's own
events can take it over; stop it with 2 before trying a spiel's lanes. It keeps its own save under %APPDATA%\\Heathcote\\interact\\audio_check,
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
from heathcote.platform.lanes import LANES, Lanes  # noqa: E402
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
        self.spiels = [(self.story.label(s), self.story.audio_path(s), s)
                       for s in self.story.refs('actionSpiels')
                       if self.story.audio_path(s) and os.path.isfile(self.story.audio_path(s))]
        self.lanes = Lanes(self.audio, self.story)
        self.idle_started = False       # the ended spiel's idle loop has been started
        self.searching = None           # the text typed so far while finding a spiel, or None
        self.last_search = None
        self.ambience_index = 0
        self.sound_index = 0
        self.spiel_index = 0
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

    # ---- the spiel ---------------------------------------------------------
    def choose_spiel(self, step):
        """Choose another spiel; one that is playing changes to it at once (the dev,
        2026-10-20: "make it so pressing comma/period plays the next spiel while it's
        playing.")."""
        self.spiel_index = (self.spiel_index + step) % len(self.spiels)
        self.say('%s, %d of %d.' % (self.spiels[self.spiel_index][0], self.spiel_index + 1,
                                    len(self.spiels)))
        if self.audio.spiel.playing:
            self.start_spiel()

    def start_spiel(self, fresh=False):
        """Play the spiel chosen from its start, with its own lane events. The lanes carry
        on from the spiel before, as in the game. With ``fresh``, as for a spiel found by its
        label, every lane starts silent, so only the spiel's own cues are heard: what the
        lanes held before it depends on the choices made on the way, which only the story
        engine knows (aidocks/plans/story_engine_plan.md)."""
        if self.audio.story_paused:
            self.audio.resume_story()
        label, path, soft = self.spiels[self.spiel_index]
        if fresh:
            self.lanes.stop_all()
        self.lanes.begin_spiel(self.story.record(soft))
        self.audio.spiel.play(path)
        self.idle_started = False
        return label

    def toggle_spiel(self):
        spiel = self.audio.spiel
        if spiel.started:
            spiel.stop()
            self.lanes.stop_all(fade_out=1.0)
            self.say('Spiel stopped.')
        else:
            self.say('Spiel: %s.' % self.start_spiel())    # as 1 and 2 say theirs

    def follow_lanes(self):
        """Once a frame: the lanes follow the spiel, and an ended spiel starts its idle loop."""
        spiel = self.audio.spiel
        if not spiel.started:
            return
        self.lanes.update(spiel.position)
        if spiel.ended and not self.idle_started:
            self.idle_started = True
            soft = (self.story.record(self.spiels[self.spiel_index][2]) or {}).get('idleLoop')
            if soft:
                self.lanes.start_idle(soft)

    def rewind(self):
        if self.audio.spiel.ended:
            self.lanes.stop_idle()          # rewinding an ended spiel stops its idle loop
            self.idle_started = False
        if not self.audio.spiel.rewind():
            self.say('No spiel is playing.')

    def say_lanes(self):
        held = ['%s %s' % (lane, self.story.label(self.lanes.holding[lane]))
                for lane in LANES if self.lanes.holding[lane]]
        if self.lanes.idle:
            held.append('idle loop %s' % self.story.label(self.lanes.idle))
        self.say('. '.join(held) + '.' if held else 'Every lane is silent.')

    def toggle_story_fade(self):
        if self.audio.story_target > 0.5:   # by where it is heading, so a quick second press turns it back
            self.audio.fade_story(0.0, 2.0)
            self.say('Story fading out.')
        else:
            self.audio.fade_story(1.0, 1.0)
            self.say('Story fading in.')

    def fast_forward(self):
        if not self.audio.spiel.fast_forward():
            self.say('No spiel is playing.')

    def toggle_pause(self):
        sfx = self.audio.slot('sfx')
        if self.audio.story_paused:
            self.audio.resume_story()
            sfx.play(self.story.sound_path('systemSounds', 'pause-unpause'))
        else:
            self.audio.pause_story()
            sfx.play(self.story.sound_path('systemSounds', 'pause-pause'))

    def where(self):
        spiel = self.audio.spiel
        if not spiel.started:
            self.say('No spiel is playing.')
            return
        state = 'ended' if spiel.ended else 'paused' if self.audio.story_paused else \
            'fast-forwarding' if spiel.fast_forwarding else 'rewinding' if spiel.rewinding else 'playing'
        self.say('%.1f of %.1f seconds, %s.' % (spiel.position, spiel.length, state))

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
        if self.audio.spiel.playing:
            playing.append('the spiel %s' % self.spiels[self.spiel_index][0])
        if self.lanes.idle:
            playing.append('the idle loop %s' % self.story.label(self.lanes.idle))
        volumes = ', '.join('%s %d' % (VOLUME_LABELS[k], self.settings.get(k)) for k in VOLUME_LABELS)
        self.say('%s. %s.' % ('Playing ' + ' and '.join(playing) if playing else 'Nothing is playing',
                              volumes))

    # ---- finding a spiel by its label ------------------------------------------
    def start_search(self):
        self.searching = ''
        self.say('Find a spiel: type part of its label, then Enter. Escape cancels.')

    def search_key(self, key, char):
        """A key while searching: letters build the text, Backspace takes one off, Enter
        finds, and Escape gives up."""
        if key == 'escape':
            self.searching = None
            self.say('Search cancelled.')
        elif key in ('return', 'enter'):
            self.find(self.searching)
        elif key == 'backspace':
            if self.searching:
                gone, self.searching = self.searching[-1], self.searching[:-1]
                self.say(gone if gone.strip() else 'space')
        elif char and char.isprintable():
            self.searching += char
            self.say(char if char.strip() else 'space')

    def find(self, text):
        """Play the first spiel whose label holds ``text``, any case; the same text again
        moves on to the next match."""
        self.searching = None
        text = text.strip().lower()
        if not text:
            self.say('Nothing typed.')
            return
        matches = [i for i, s in enumerate(self.spiels) if text in s[0].lower()]
        if not matches:
            self.say('No spiel has "%s" in its label.' % text)
            return
        if text == self.last_search:
            later = [i for i in matches if i > self.spiel_index]
            index = later[0] if later else matches[0]
        else:
            index = matches[0]
        self.last_search = text
        self.spiel_index = index
        if self.audio.spiel.started:
            self.audio.spiel.stop()
        label = self.start_spiel(fresh=True)
        self.say('%s, %d of %d matches.' % (label, matches.index(index) + 1, len(matches)))

    def key(self, key, mods, char=''):
        if self.searching is not None:
            self.search_key(key, char)
            return
        volume = VOLUME_KEYS.get((key, tuple(mods)))
        if volume:
            self.step_volume(*volume)
        elif key in (',', '.') and mods in ([], ['shift']):
            self.choose_spiel((-1 if key == ',' else 1) * (10 if mods else 1))
        elif mods:
            return
        elif key == 'escape':
            self.running = False
        elif key == '1':
            self.toggle_title()
        elif key == '2':
            self.toggle_ambience()
        elif key == '3':
            self.toggle_spiel()
        elif key in ('up', 'down'):
            self.choose_ambience(-1 if key == 'up' else 1)
        elif key in ('[', ']'):
            self.choose_sound(-1 if key == '[' else 1)
        elif key == 'space':
            self.play_sound()
        elif key == 'left':
            self.rewind()
        elif key == 'right':
            self.fast_forward()
        elif key == 'p':
            self.toggle_pause()
        elif key == 'tab':
            self.where()
        elif key == 'l':
            self.say_lanes()
        elif key == 'f':
            self.toggle_story_fade()
        elif key == 's':
            self.start_search()
        elif key in ('return', 'enter'):
            self.status()

    def run(self):
        pygame.display.init()
        pygame.display.set_caption('Heathcote audio check')
        pygame.display.set_mode((640, 480))
        self.audio.open()
        self.audio.spiel.rewind_sound = self.story.sound_path('systemSounds', 'rewind')
        self.say('Audio check. Press 1 for the title music, 2 for an ambience loop, 3 for a spiel, '
                 'Space for an interface sound, and Enter for what is playing. Escape quits.')
        clock = pygame.time.Clock()
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        self.key(pygame.key.name(event.key), mods_from_pygame(event.mod, pygame),
                                 event.unicode)
                self.audio.update()
                self.follow_lanes()
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
