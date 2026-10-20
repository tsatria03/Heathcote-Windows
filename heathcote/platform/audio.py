"""Every sound the game plays, through FMOD (aidocks/plans/audio_plan.md).

FMOD is the engine the original used. It is reached through pyfmodex, which loads the
DLL named by ``PYFMODEX_DLL_PATH``, so that is set to ``vendor/fmod/fmod.dll``, or the
build's copy, before pyfmodex is first imported. pygame plays nothing.

The channels are the original's (+[Sound initEngine], 0x1000203f0), each a ``Slot``:

    story group     spiel, bgm, ambience1, ambience2, ambience3, idleLoop
    system group    titleBgm, sfx, systemVoice

A slot plays one recording at a time; playing another stops the one before.

The four volumes (platform/settings.py) move in even-sounding steps: each 10 percent is
6 decibels, and 0 percent is silence (the dev, 2026-10-19: "I want even steps if
possible."). The master sets FMOD's master group, so it scales everything. Each slot also
follows one other volume: the backgrounds for the music lane, the ambiences and the idle
loop; the interface for the system sounds and the recorded choices; the title for the
title music. The spiel follows the master alone, so the voices are never quieter than
the backgrounds.

Fades are FMOD fade points, timed on the mixer's own clock, so they are exact to the
sample and run between frames. They multiply with the volumes, so a volume change never
disturbs a fade.

With ``HEATHCOTE_NOSOUND`` set, as the tests set it, or when no sound device opens, FMOD
starts with its no-sound output: everything works and nothing is heard.
"""
from __future__ import annotations

import logging
import os
import time
import types

from .. import paths

log = logging.getLogger('audio')

#: Set to 1 by the tests: FMOD runs, silently, opening no sound device.
NOSOUND_ENV = 'HEATHCOTE_NOSOUND'
#: Decibels per 10 percent of a volume.
STEP_DB = 6.0

#: Each slot: (its channel group, the volume it follows besides the master, or None).
SLOTS = {
    'spiel': ('story', None),
    'bgm': ('story', 'backgrounds_volume'),
    'ambience1': ('story', 'backgrounds_volume'),
    'ambience2': ('story', 'backgrounds_volume'),
    'ambience3': ('story', 'backgrounds_volume'),
    'idleLoop': ('story', 'backgrounds_volume'),
    'titleBgm': ('system', 'title_volume'),
    'sfx': ('system', 'interface_volume'),
    'systemVoice': ('system', 'interface_volume'),
}
#: The slots that loop what they play, and so open it as a stream, read from disk as it
#: plays rather than all at once.
LOOPING = ('bgm', 'ambience1', 'ambience2', 'ambience3', 'idleLoop', 'titleBgm')

MISSING_DLL = ("Heathcote's sound engine, fmod.dll, was not found in %s. Install the FMOD "
               "Engine 2.02.35 for Windows from fmod.com, and copy api\\core\\lib\\x64\\fmod.dll "
               "from its install into that folder.")


def gain(percent):
    """A volume's percentage as FMOD's linear volume: 100 is 1.0, each 10 percent less
    is 6 decibels quieter, and 0 is silence."""
    if percent <= 0:
        return 0.0
    return 10 ** ((percent - 100) / 10.0 * STEP_DB / 20.0)


def load_pyfmodex():
    """pyfmodex, loaded against the game's own fmod.dll; SystemExit with a message for the
    player when the DLL is not there."""
    if not os.path.isfile(paths.FMOD_DLL):
        raise SystemExit(MISSING_DLL % os.path.dirname(paths.FMOD_DLL))
    os.environ['PYFMODEX_DLL_PATH'] = paths.FMOD_DLL
    import pyfmodex
    return pyfmodex


class Slot:
    """One of the original's channels: one recording at a time, with its fade level."""

    def __init__(self, audio, name, group, volume_key):
        self.audio = audio
        self.name = name
        self.group = group
        self.volume_key = volume_key
        self.channel = None
        self.sound = None
        self.path = None
        # The fade level last aimed for, and the fade towards it: (from, to, start, seconds).
        self._fade = (1.0, 1.0, 0.0, 0.0)

    # ---- the level a fade has reached ---------------------------------------
    def level(self, now=None):
        """How far the slot's fade has got, from 0.0 to 1.0, worked out from when it began."""
        start_level, end_level, began, seconds = self._fade
        now = time.perf_counter() if now is None else now
        if seconds <= 0 or now >= began + seconds:
            return end_level
        return start_level + (end_level - start_level) * (now - began) / seconds

    # ---- playing --------------------------------------------------------------
    def play(self, path, loop=None, fade_in=0.0):
        """Play a recording, stopping what this slot was playing. Looping slots loop
        unless ``loop`` says otherwise. True when it started."""
        self.stop()
        loop = self.name in LOOPING if loop is None else loop
        fmod = self.audio.fmod
        mode = fmod.flags.MODE.TWOD | fmod.flags.MODE.ACCURATETIME
        mode |= fmod.flags.MODE.LOOP_NORMAL if loop else fmod.flags.MODE.LOOP_OFF
        try:
            if self.name in LOOPING:
                sound = self.audio.system.create_stream(path, mode=mode)
            else:
                sound = self.audio.system.create_sound(path, mode=mode | fmod.flags.MODE.CREATESAMPLE)
            channel = self.audio.system.play_sound(sound, channel_group=self.audio.groups[self.group],
                                                   paused=True)
        except Exception:
            log.exception('%s could not play %s', self.name, path)
            return False
        self.sound, self.channel, self.path = sound, channel, path
        self._fade = (1.0, 1.0, 0.0, 0.0)
        self.apply_volume()
        if fade_in > 0:
            self._fade_points(0.0, 1.0, fade_in)
        channel.paused = False
        log.debug('%s plays %s', self.name, os.path.basename(path))
        return True

    @property
    def playing(self):
        if self.channel is None:
            return False
        try:
            return bool(self.channel.is_playing)
        except Exception:
            return False                    # FMOD has freed a channel that finished

    def fade_to(self, level, seconds):
        """Fade from wherever the slot's fade is now to ``level``, over ``seconds``."""
        if self.channel is None:
            return
        self._fade_points(self.level(), level, seconds)

    def stop(self, fade_out=0.0):
        """Stop, at once or after fading out over ``fade_out`` seconds."""
        if self.channel is None:
            return
        if fade_out > 0 and self.playing:
            end = self._fade_points(self.level(), 0.0, fade_out)
            if end is not None:
                try:
                    # Stopped by FMOD itself, to the sample, once the fade has ended.
                    self.channel.delay = types.SimpleNamespace(dsp_start=0, dsp_end=end, stop_channels=True)
                    self.audio.fading_out.append((self.channel, self.sound))
                    self.channel = self.sound = self.path = None
                    return
                except Exception:
                    log.exception('%s could not fade out', self.name)
        self._release()

    def _release(self):
        try:
            if self.channel is not None:
                self.channel.stop()
        except Exception:
            pass
        try:
            if self.sound is not None:
                self.sound.release()
        except Exception:
            pass
        self.channel = self.sound = self.path = None

    def _fade_points(self, start_level, end_level, seconds):
        """Put the channel's fade points from ``start_level`` now to ``end_level`` in
        ``seconds``; the parent clock it ends at, or None."""
        try:
            clock = self.channel.dsp_clock.parent_clock
            end = clock + int(seconds * self.audio.rate)
            self.channel.remove_fade_points(0, 2 ** 63 - 1)
            self.channel.add_fade_point(clock, start_level)
            self.channel.add_fade_point(end, end_level)
        except Exception:
            log.exception('%s could not fade', self.name)
            return None
        self._fade = (start_level, end_level, time.perf_counter(), seconds)
        return end

    # ---- volume ------------------------------------------------------------
    def apply_volume(self):
        """The slot's own volume setting, on its channel; the master is on the master group."""
        if self.channel is None:
            return
        value = 1.0 if self.volume_key is None else gain(self.audio.settings.get(self.volume_key))
        try:
            self.channel.volume = value
        except Exception:
            pass


class Audio:
    """FMOD, its two channel groups and the original's channels."""

    _shared = None

    @classmethod
    def shared(cls, settings=None):
        if cls._shared is None:
            from .settings import Settings
            cls._shared = Audio(settings or Settings.shared())
        return cls._shared

    def __init__(self, settings):
        self.settings = settings
        self.fmod = None
        self.system = None
        self.groups = {}
        self.slots = {}
        self.rate = 48000
        self.silent = False             # running FMOD's no-sound output
        self.fading_out = []            # (channel, sound) fading out, freed once stopped

    @property
    def ok(self):
        return self.system is not None

    def open(self):
        """Start FMOD and make the channels. SystemExit if fmod.dll is missing; with no
        sound device, FMOD runs silent and the game carries on."""
        if self.ok:
            return
        fmod = load_pyfmodex()
        self.fmod = fmod
        want_silence = os.environ.get(NOSOUND_ENV) == '1'
        self.system = self._start(fmod, silent=want_silence)
        if self.system is None and not want_silence:
            log.warning('no sound device could be opened, so the game runs without sound')
            self.system = self._start(fmod, silent=True)
        if self.system is None:
            raise SystemExit("Heathcote's sound engine, FMOD, could not start. The details are in "
                             "log.txt, in the logs folder of the game's save folder.")
        self.rate = self.system.software_format.sample_rate
        v = self.system.version
        log.info('FMOD %x.%02x.%02x started, %s, at %d Hz', v >> 16, (v >> 8) & 0xff, v & 0xff,
                 'silent' if self.silent else 'with sound', self.rate)
        master = self.system.master_channel_group
        self.groups = {'master': master,
                       'story': self.system.create_channel_group('story'),
                       'system': self.system.create_channel_group('system')}
        self.slots = {name: Slot(self, name, group, key) for name, (group, key) in SLOTS.items()}
        self.apply_volumes()

    def _start(self, fmod, silent):
        try:
            system = fmod.System()
            if silent:
                system.output = fmod.enums.OUTPUTTYPE.NOSOUND
            system.init()
        except Exception:
            log.exception('FMOD could not start%s', ' silently' if silent else '')
            return None
        self.silent = silent
        return system

    def slot(self, name):
        return self.slots[name]

    def apply_volumes(self):
        """Every volume, as the settings now have them, at once."""
        if not self.ok:
            return
        try:
            self.groups['master'].volume = gain(self.settings.get('master_volume'))
        except Exception:
            log.exception('the master volume could not be set')
        for slot in self.slots.values():
            slot.apply_volume()

    def update(self):
        """Once a frame: let FMOD do its work, and free what has finished fading out."""
        if not self.ok:
            return
        try:
            self.system.update()
        except Exception:
            log.exception('FMOD update failed')
        still = []
        for channel, sound in self.fading_out:
            try:
                playing = channel.is_playing
            except Exception:
                playing = False
            if playing:
                still.append((channel, sound))
            else:
                try:
                    sound.release()
                except Exception:
                    pass
        self.fading_out = still

    def close(self):
        if not self.ok:
            return
        for slot in self.slots.values():
            slot._release()
        for channel, sound in self.fading_out:
            try:
                channel.stop()
                sound.release()
            except Exception:
                pass
        self.fading_out = []
        try:
            self.system.release()
        except Exception:
            log.exception('FMOD did not close cleanly')
        self.system = None
        self.slots = {}
        self.groups = {}
        log.info('FMOD closed')
