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
loop; the interface for the system sounds; the title for the title music. The spiel and
the recorded choices from ``speech/``, on ``systemVoice``, follow the master alone, so the
voices are never quieter than the backgrounds, and the interface volume never turns the
choices down (the dev, 2026-10-20: "the sounds found in the speech folder should not be
effected by the interface volume setting.").

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
    'systemVoice': ('system', None),
}
#: The slots that loop what they play, and so open it as a stream, read from disk as it
#: plays rather than all at once.
LOOPING = ('bgm', 'ambience1', 'ambience2', 'ambience3', 'idleLoop', 'titleBgm')

#: The hush (-[SoundChannel hush], 0x10002f4e0; +[Sound hushBackgrounds], 0x1000223b8): a
#: parametric EQ, FMOD effect type 12, on the music and the three ambiences, never the
#: spiel or the idle loop. Each tick its gain moves by a step towards its target
#: (-[SoundChannel tick], 0x10002f6e0): down by 0.796875 dB a tick to -12 dB, about a
#: quarter of a second, and back up by 0.5 dB a tick to 0, 0.4 seconds, when the effect
#: comes off.
HUSHED = ('bgm', 'ambience1', 'ambience2', 'ambience3')
HUSH_CENTER = 1250.0
HUSH_OCTAVES = 5.0
HUSH_DB = -12.0
HUSH_STEP = -0.796875
UNHUSH_STEP = 0.5
TICK = 1 / 60.0

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
        # The hush's EQ on this channel, its gain in dB, and where that gain is heading.
        self.eq = None
        self.eq_gain = 0.0
        self.eq_step = 0.0
        self.eq_target = 0.0

    # ---- the level a fade has reached ---------------------------------------
    def level(self, now=None):
        """How far the slot's fade has got, from 0.0 to 1.0, worked out from when it began."""
        start_level, end_level, began, seconds = self._fade
        now = time.perf_counter() if now is None else now
        if seconds <= 0 or now >= began + seconds:
            return end_level
        return start_level + (end_level - start_level) * (now - began) / seconds

    # ---- playing --------------------------------------------------------------
    def play(self, path, loop=None, fade_in=0.0, start_level=0.0, end_level=1.0):
        """Play a recording, stopping what this slot was playing. Looping slots loop
        unless ``loop`` says otherwise. With ``fade_in``, it fades from ``start_level`` to
        ``end_level``: up from 0 as a rule, or from part way when a crossfade is picked up
        after a jump back. True when it started."""
        self.stop()
        loop = self.name in LOOPING if loop is None else loop
        fmod = self.audio.fmod
        mode = fmod.flags.MODE.TWOD | fmod.flags.MODE.ACCURATETIME
        mode |= fmod.flags.MODE.LOOP_NORMAL if loop else fmod.flags.MODE.LOOP_OFF
        try:
            source, exinfo = self.audio.source(path)
            if exinfo is not None:
                mode |= fmod.flags.MODE.OPENMEMORY
            if self.name in LOOPING:
                sound = self.audio.system.create_sound(source, mode=mode | fmod.flags.MODE.CREATESTREAM,
                                                       exinfo=exinfo)
            else:
                sound = self.audio.system.create_sound(source, mode=mode | fmod.flags.MODE.CREATESAMPLE,
                                                       exinfo=exinfo)
            channel = self.audio.system.play_sound(sound, channel_group=self.audio.groups[self.group],
                                                   paused=True)
        except Exception:
            log.exception('%s could not play %s', self.name, path)
            return False
        self.sound, self.channel, self.path = sound, channel, path
        self._fade = (1.0, 1.0, 0.0, 0.0)
        self.apply_volume()
        if self.name in HUSHED and self.audio.hush_count > 0:
            self._attach_eq(HUSH_DB)        # started while hushed: muffled from the first sample
        if fade_in > 0:
            self._fade_points(start_level, end_level, fade_in)
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

    def play_fading_out(self, path, from_level, seconds):
        """Play a recording already part way through fading out, from ``from_level`` down
        to silence over ``seconds``, then let it go: the old side of a crossfade picked up
        part way, after a jump back."""
        # The fade down is in place before the channel is heard, so it never starts loud.
        if not self.play(path, fade_in=seconds, start_level=from_level, end_level=0.0):
            return
        self._fade = (from_level, from_level, 0.0, 0.0)
        self.stop(fade_out=seconds)

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
                    # The hush, if any, stays on the fading channel and is freed with it.
                    self.audio.fading_out.append((self.channel, self.sound, self.eq))
                    self.channel = self.sound = self.path = self.eq = None
                    self.eq_gain = self.eq_target = self.eq_step = 0.0
                    return
                except Exception:
                    log.exception('%s could not fade out', self.name)
        self._release()

    # ---- the hush ------------------------------------------------------------
    def _attach_eq(self, gain_db):
        fmod = self.audio.fmod
        try:
            if self.eq is None:
                dsp = self.audio.system.create_dsp_by_type(fmod.enums.DSP_TYPE.PARAMEQ)
                dsp.set_parameter_float(0, HUSH_CENTER)
                dsp.set_parameter_float(1, HUSH_OCTAVES)
                dsp.set_parameter_float(2, gain_db)
                self.channel.add_dsp(0, dsp)
                self.eq = dsp
            self.eq_gain = self.eq_target = gain_db
            self.eq_step = 0.0
        except Exception:
            log.exception('%s could not be hushed', self.name)

    def hush(self):
        """Start muffling, as the original: only a channel that is playing."""
        if not self.playing:
            return
        if self.eq is None:
            self._attach_eq(0.0)
        self.eq_step, self.eq_target = HUSH_STEP, HUSH_DB

    def unhush(self):
        if self.eq is not None:
            self.eq_step, self.eq_target = UNHUSH_STEP, 0.0

    def tick(self):
        """One tick of the hush's ramp."""
        if self.eq is None or self.eq_step == 0.0:
            return
        self.eq_gain += self.eq_step
        if (self.eq_step < 0 and self.eq_gain <= self.eq_target) or \
                (self.eq_step > 0 and self.eq_gain >= self.eq_target):
            self.eq_gain, self.eq_step = self.eq_target, 0.0
            if self.eq_target == 0.0:
                self._detach_eq()           # fully unhushed: the effect comes off
                return
        try:
            self.eq.set_parameter_float(2, self.eq_gain)
        except Exception:
            pass

    def _detach_eq(self):
        if self.eq is None:
            return
        try:
            if self.channel is not None:
                self.channel.remove_dsp(self.eq)
        except Exception:
            pass
        try:
            self.eq.release()
        except Exception:
            pass
        self.eq = None
        self.eq_gain = self.eq_target = self.eq_step = 0.0

    def _release(self):
        self._detach_eq()
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
        self.fading_out = []            # (channel, sound, eq or None) fading out, freed once stopped
        self.hush_count = 0             # nested hushes; the backgrounds are muffled while above 0
        self._story_fade = (1.0, 1.0, 0.0, 0.0)   # the story group's fade: from, to, start, seconds
        self._tick_time = 0.0           # time towards the next hush tick
        self._last_update = None
        self.spiel = None               # the SpielPlayer, once FMOD has started
        self.story_paused = False

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
        from .spiel import SpielPlayer
        self.spiel = SpielPlayer(self)
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

    def source(self, path):
        """What FMOD opens for ``path``: (the path, None) for a file on disk, or, for a
        recording in story.dat (platform/pack.py), (its bytes, decrypted in memory, and the
        extra information FMOD's OPENMEMORY needs). FMOD copies the bytes, so nothing
        decrypted is kept here or written to disk."""
        from . import pack
        if not path.startswith(pack.PREFIX):
            return path, None
        from pyfmodex.structures import CREATESOUNDEXINFO     # loaded with FMOD already
        data = pack.read(path)
        exinfo = CREATESOUNDEXINFO()
        exinfo.length = len(data)
        return data, exinfo

    def play_oneshot(self, path):
        """An interface sound on a channel of its own, at the interface volume, so two can
        sound together, as click-good and menu-open do; freed once it ends. True when it
        started."""
        if not self.ok or not path:
            return False
        fmod = self.fmod
        try:
            sound = self.system.create_sound(path, mode=fmod.flags.MODE.TWOD | fmod.flags.MODE.CREATESAMPLE
                                             | fmod.flags.MODE.LOOP_OFF)
            channel = self.system.play_sound(sound, channel_group=self.groups['system'], paused=True)
            channel.volume = gain(self.settings.get('interface_volume'))
            channel.paused = False
        except Exception:
            log.exception('could not play %s', path)
            return False
        self.fading_out.append((channel, sound, None))     # freed by update() once it ends
        return True

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

    # ---- the hush ------------------------------------------------------------
    def hush_backgrounds(self):
        """Muffle the music and the three ambiences. A counter, as the original's: nested
        hushes need as many unhushes (+[Sound hushBackgrounds], 0x1000223b8)."""
        if not self.ok:
            return
        self.hush_count += 1
        if self.hush_count == 1:
            for name in HUSHED:
                self.slots[name].hush()

    def unhush_backgrounds(self):
        if not self.ok or self.hush_count == 0:
            return
        self.hush_count -= 1
        if self.hush_count == 0:
            for name in HUSHED:
                self.slots[name].unhush()

    # ---- the story group's fades -------------------------------------------------
    def fade_story(self, level, seconds):
        """Fade the whole story group, spiel and backgrounds, to ``level`` over ``seconds``:
        out over 2 and in over 1, as the original (+[Sound fadeOutStoryChannelGroup],
        0x1000225d4; fadeInStoryChannelGroup, 0x100022690)."""
        if not self.ok:
            return
        group = self.groups['story']
        try:
            clock = group.dsp_clock.parent_clock
            group.remove_fade_points(0, 2 ** 63 - 1)
            group.add_fade_point(clock, self.story_level())
            group.add_fade_point(clock + int(seconds * self.rate), level)
        except Exception:
            log.exception('the story could not fade')
            return
        self._story_fade = (self.story_level(), level, time.perf_counter(), seconds)

    @property
    def story_target(self):
        """The level the story group's fade is heading for, 0.0 or 1.0."""
        return self._story_fade[1]

    def story_level(self, now=None):
        """How far the story group's fade has got, 0.0 to 1.0."""
        start_level, end_level, began, seconds = self._story_fade
        now = time.perf_counter() if now is None else now
        if seconds <= 0 or now >= began + seconds:
            return end_level
        return start_level + (end_level - start_level) * (now - began) / seconds

    # ---- pausing ---------------------------------------------------------------
    def pause_story(self):
        """Pause as the original paused (+[StoryView pause], 0x1000252cc): the backgrounds
        are hushed and play on, muffled, and only the spiel stops (the dev, 2026-10-20: "It
        should match the original, including in the audio checker."). The pause sound is
        the caller's to play.

        The idle loop is muffled too, unlike the original, which never hushed it (the dev,
        2026-10-20: "Please make the idle ambiences also muffle if you pause the game.").
        Only the pause does this; the actions menu's hush leaves the idle loop clear, as
        the original's did."""
        if not self.ok or self.story_paused:
            return
        self.hush_backgrounds()
        self.slots['idleLoop'].hush()
        self.spiel.pause()
        self.story_paused = True

    def resume_story(self):
        """Unpause (+[StoryView unpause], 0x100025484): unhush, and the spiel plays on."""
        if not self.ok or not self.story_paused:
            return
        self.unhush_backgrounds()
        self.slots['idleLoop'].unhush()
        self.spiel.resume()
        self.story_paused = False

    def update(self, now=None):
        """Once a frame: let FMOD do its work, move rewind, fast-forward and the hush on,
        and free what has finished fading out."""
        if not self.ok:
            return
        now = time.perf_counter() if now is None else now
        try:
            self.system.update()
        except Exception:
            log.exception('FMOD update failed')
        self.spiel.update(now)
        self.tick_hush(now)
        still = []
        for item in self.fading_out:
            try:
                playing = item[0].is_playing
            except Exception:
                playing = False
            if playing:
                still.append(item)
            else:
                self._free(*item)
        self.fading_out = still

    def tick_hush(self, now):
        """Step the hush's ramps once for every 1/60 second passed, as the original ticked."""
        if self._last_update is not None:
            self._tick_time += max(0.0, now - self._last_update)
        self._last_update = now
        while self._tick_time >= TICK:
            self._tick_time -= TICK
            for name in HUSHED + ('idleLoop',):     # the idle loop, muffled by a pause
                self.slots[name].tick()

    @staticmethod
    def _free(channel, sound, eq):
        for release in (lambda: channel.stop(), lambda: sound.release(),
                        lambda: eq.release() if eq is not None else None):
            try:
                release()
            except Exception:
                pass

    def close(self):
        if not self.ok:
            return
        self.spiel.close()
        for slot in self.slots.values():
            slot._release()
        for item in self.fading_out:
            self._free(*item)
        self.fading_out = []
        self.hush_count = 0
        try:
            self.system.release()
        except Exception:
            log.exception('FMOD did not close cleanly')
        self.system = None
        self.slots = {}
        self.groups = {}
        self.spiel = None
        self.story_paused = False
        log.info('FMOD closed')
