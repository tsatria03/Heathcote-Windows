"""The spiel: the story's own recording, with pausing, rewind and fast-forward, as the
original played them (aidocks/plans/audio_plan.md, section 2; the numbers are from
aidocks/general/project_original_behaviour.md).

The spiel is opened as an FMOD stream on the ``spiel`` slot, so it can seek, and FMOD
gives its length and position exactly.

Rewind (-[PlayState tick_rewind], 0x100033248):

* the ``rewind`` interface sound plays;
* every 7 ticks the spiel jumps back 1 second, for 45 ticks (0.75 seconds), then plays on;
* at the beginning it stops early, and the interface sound fades out over 0.75 seconds;
* a spiel that has ended starts again 1 second before its end
  (-[SoundChannel setPositionBeforeEnd:], 0x10002eda0, subtracts 1000 milliseconds),
  and the jumps go on from there.

Fast-forward (-[SoundChannel startFastForward], 0x10002f348):

* the spiel plays at 1.75 times its speed for 90 ticks (1.5 seconds), then plays on;
* FMOD's pitch shift effect is attached while it runs, at 1/1.75, so voices keep their
  pitch ("chipmunk suppression", in the original's own log), with 2 channels;
* pressing it again while it runs starts its 1.5 seconds over;
* if the spiel ends during it, it stops there; a spiel started during it fast-forwards too.

Rewind and fast-forward count time only while the spiel is not paused, so a pause in the
middle keeps what they had left.
"""
from __future__ import annotations

import logging
import time

log = logging.getLogger('spiel')

TICK = 1 / 60.0
REWIND_EVERY = 7 * TICK         # seconds between jumps back
REWIND_FOR = 45 * TICK          # how long a rewind lasts
REWIND_JUMP = 1.0               # seconds each jump goes back
REWIND_SOUND_FADE = 0.75        # the rewind sound's fade-out, when the beginning is reached
BEFORE_END = 1.0                # where a rewound ended spiel starts, before its end
FFWD_SPEED = 1.75
FFWD_FOR = 90 * TICK


class SpielPlayer:
    """The spiel slot, with the original's rewind and fast-forward."""

    def __init__(self, audio, rewind_sound=None):
        self.audio = audio
        self.slot = audio.slot('spiel')
        self.rewind_sound = rewind_sound    # the path of the 'rewind' interface sound
        self.length = 0.0
        self.started = False                # a spiel was played and has not been stopped
        self.paused = False
        self.rewinding = None               # [seconds into the rewind, next jump at]
        self.ffwd_left = 0.0                # seconds of fast-forward left; 0 when off
        self.base_frequency = None
        self._pitch = None                  # FMOD's pitch shift effect, made on first use
        self._last = None                   # time.perf_counter() at the last update
        self._ended_seen = False            # an update has already seen the spiel ended

    # ---- playing -------------------------------------------------------------
    def play(self, path):
        """Play a spiel from its start. A fast-forward under way carries on into it."""
        carry = self.ffwd_left > 0
        self._ended_seen = False
        self.rewinding = None
        self._detach_pitch()
        fmod = self.audio.fmod
        if not self.slot.play(path, loop=False):
            self.started = False
            return False
        self.started = True
        self.paused = False
        try:
            self.length = self.slot.sound.get_length(fmod.enums.TIMEUNIT.MS) / 1000.0
            self.base_frequency = self.slot.channel.frequency
        except Exception:
            log.exception('the spiel\'s length could not be read')
            self.length, self.base_frequency = 0.0, None
        if carry:
            self._start_ffwd_effect()
        return True

    def stop(self):
        self.rewinding = None
        self.ffwd_left = 0.0
        self._detach_pitch()
        self.slot.stop()
        self.started = False
        self.paused = False

    @property
    def playing(self):
        """Sounding or paused, but not ended."""
        return self.started and self.slot.playing

    @property
    def ended(self):
        """A spiel was played and has run to its end."""
        return self.started and not self.slot.playing

    @property
    def position(self):
        """Seconds into the spiel; its length once it has ended."""
        if self.ended:
            return self.length
        try:
            return self.slot.channel.get_position(self.audio.fmod.enums.TIMEUNIT.MS) / 1000.0
        except Exception:
            return 0.0

    def seek(self, seconds):
        seconds = max(0.0, min(seconds, max(0.0, self.length - 0.001)))
        try:
            self.slot.channel.set_position(int(seconds * 1000), self.audio.fmod.enums.TIMEUNIT.MS)
        except Exception:
            log.exception('the spiel could not seek to %.2f', seconds)

    # ---- pausing ---------------------------------------------------------------
    def pause(self):
        if self.slot.channel is not None and not self.paused:
            try:
                self.slot.channel.paused = True
            except Exception:
                pass
        self.paused = True

    def resume(self):
        if self.slot.channel is not None and self.paused:
            try:
                self.slot.channel.paused = False
            except Exception:
                pass
        self.paused = False

    # ---- rewind ----------------------------------------------------------------
    def rewind(self):
        """Start the original's rewind; True when it started."""
        if not self.started:
            return False
        self.ffwd_left = 0.0
        self._detach_pitch()
        if self.rewind_sound:
            self.audio.slot('sfx').play(self.rewind_sound)
        self.rewinding = [0.0, 0.0]         # the first jump comes at once
        self._rewind_step(0.0)
        return True

    def _jump_back(self):
        """One jump back; True when the beginning was reached."""
        if self.ended:
            # Started again, 1 second before its end (+[Sound spotRewind:], 0x1000222cc).
            path = self.slot.path
            carry_paused = self.paused
            if path is None:
                return True
            self.slot.play(path, loop=False)
            self.seek(self.length - BEFORE_END)
            if carry_paused:
                self.pause()
            return False
        target = self.position - REWIND_JUMP
        self.seek(target)
        return target <= 0

    def _rewind_step(self, dt):
        state = self.rewinding
        state[0] += dt
        # A hair of slack, so adding 7/60 up over and over never lands a frame late.
        due = state[0] + 1e-9
        while self.rewinding is not None and due >= state[1] and state[1] < REWIND_FOR:
            state[1] += REWIND_EVERY
            if self._jump_back():
                self.rewinding = None
                self.audio.slot('sfx').stop(fade_out=REWIND_SOUND_FADE)
                return
        if self.rewinding is not None and due >= REWIND_FOR:
            self.rewinding = None

    # ---- fast-forward ------------------------------------------------------------
    def fast_forward(self):
        """Start the original's fast-forward, or start its 1.5 seconds over; True when it
        runs."""
        if not self.playing:
            return False
        self.rewinding = None
        if self.ffwd_left <= 0:
            self._start_ffwd_effect()
        self.ffwd_left = FFWD_FOR
        return True

    def _pitch_dsp(self):
        if self._pitch is None:
            fmod = self.audio.fmod
            dsp = self.audio.system.create_dsp_by_type(fmod.enums.DSP_TYPE.PITCHSHIFT)
            # By name: pyfmodex's numbering of these is not FMOD 2.02's. Every one is a
            # float in 2.02, the channel count included.
            names = {dsp.get_parameter_info(i).name.decode().lower(): i for i in range(dsp.num_parameters)}
            dsp.set_parameter_float(names['pitch'], 1.0 / FFWD_SPEED)
            dsp.set_parameter_float(names['max channels'], 2.0)
            self._pitch = dsp
        return self._pitch

    def _start_ffwd_effect(self):
        channel = self.slot.channel
        if channel is None or self.base_frequency is None:
            return
        try:
            channel.frequency = self.base_frequency * FFWD_SPEED
            channel.add_dsp(0, self._pitch_dsp())
        except Exception:
            log.exception('fast-forward could not start')
        if self.ffwd_left <= 0:
            self.ffwd_left = FFWD_FOR

    def _detach_pitch(self):
        channel = self.slot.channel
        if channel is not None and self._pitch is not None:
            try:
                channel.remove_dsp(self._pitch)
            except Exception:
                pass
            try:
                if self.base_frequency is not None:
                    channel.frequency = self.base_frequency
            except Exception:
                pass

    def stop_effects(self):
        """End a rewind or fast-forward at once and play on, as a tap did in the original."""
        self.rewinding = None
        if self.ffwd_left > 0:
            self.ffwd_left = 0.0
            self._detach_pitch()

    @property
    def fast_forwarding(self):
        return self.ffwd_left > 0 and not self.ended

    # ---- once a frame ------------------------------------------------------------
    def update(self, now=None):
        """Called once a frame: move rewind and fast-forward on by the time passed."""
        now = time.perf_counter() if now is None else now
        dt = 0.0 if self._last is None else max(0.0, now - self._last)
        self._last = now
        if self.paused or not self.started:
            return
        if self.rewinding is not None:
            self._rewind_step(dt)
        if self.ffwd_left > 0:
            if self.ended:
                # It stops where the spiel ended, unless the story starts the next spiel
                # in this same frame, which then fast-forwards too: one frame's grace,
                # whichever of the two is updated first.
                if self._ended_seen:
                    self.ffwd_left = 0.0
                self._ended_seen = True
                return
            self.ffwd_left -= dt
            if self.ffwd_left <= 0:
                self.ffwd_left = 0.0
                self._detach_pitch()

    def close(self):
        self.stop()
        if self._pitch is not None:
            try:
                self._pitch.release()
            except Exception:
                pass
            self._pitch = None
