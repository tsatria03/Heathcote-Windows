"""The spiel: playing, pausing, rewind and fast-forward (heathcote/platform/spiel.py), on
FMOD's no-sound output. The clock rewind and fast-forward count by is handed in, so the
tests move it by hand."""
import _quiet  # noqa: F401  (first, before the game)

import os
import time

from heathcote.game.storydata import StoryData
from heathcote.platform.audio import Audio
from heathcote.platform.settings import Settings
from heathcote.platform.spiel import FFWD_FOR, FFWD_SPEED

STORY = StoryData.shared()
N = [0]


def spiel_paths():
    """Recorded spiels, longest first, so seeking has room."""
    found = [STORY.audio_path(s) for s in STORY.refs('actionSpiels')]
    found = [p for p in found if p and os.path.isfile(p)]
    return sorted(found, key=os.path.getsize, reverse=True)


LONG, SECOND = spiel_paths()[:2]
SHORTEST = spiel_paths()[-1]


def fresh():
    N[0] += 1
    a = Audio(Settings(os.path.join(_quiet.FOLDER, 'spiel%d' % N[0], 'settings.json')))
    a.open()
    a.spiel.rewind_sound = STORY.sound_path('systemSounds', 'rewind')
    return a


def close(x, y, within=0.15):
    return abs(x - y) <= within


def wait(a, seconds):
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        a.system.update()
        time.sleep(0.01)


def test_a_spiel_plays_with_its_length_and_position():
    a = fresh()
    try:
        s = a.spiel
        assert s.play(LONG)
        assert s.length > 10 and s.playing and not s.ended
        s.seek(5.0)
        assert close(s.position, 5.0)
    finally:
        a.close()


def test_pause_and_resume_the_story_together():
    a = fresh()
    try:
        a.spiel.play(LONG)
        a.slot('ambience1').play(STORY.audio_path(STORY.refs('ambience')[0]))
        a.pause_story()
        assert a.story_paused and a.spiel.paused and a.groups['story'].paused
        at = a.spiel.position
        wait(a, 0.3)
        assert close(a.spiel.position, at, 0.02)            # held still
        a.resume_story()
        assert not a.groups['story'].paused and not a.spiel.paused
    finally:
        a.close()


def test_rewind_jumps_back_a_second_every_7_ticks_for_45():
    a = fresh()
    try:
        s = a.spiel
        s.play(LONG)
        s.pause()                                           # so playing time does not blur it
        s.seek(20.0)
        s.paused = False                                    # count rewind time, still silent
        s.update(now=100.0)
        assert s.rewind()
        assert close(s.position, 19.0)                      # the first jump comes at once
        assert a.slot('sfx').path.endswith('rewind-try2.mp3')
        s.update(now=100.0 + 6 / 60)
        assert close(s.position, 19.0)                      # not yet 7 ticks
        s.update(now=100.0 + 7 / 60)
        assert close(s.position, 18.0)
        s.update(now=100.0 + 45 / 60)
        assert close(s.position, 13.0)                      # 7 jumps in all
        assert s.rewinding is None
        s.update(now=101.0)
        assert close(s.position, 13.0)
    finally:
        a.close()


def test_rewind_stops_at_the_beginning_and_fades_its_sound():
    a = fresh()
    try:
        s = a.spiel
        s.play(LONG)
        s.pause()
        s.seek(1.5)
        s.paused = False
        s.update(now=10.0)
        s.rewind()
        s.update(now=10.0 + 7 / 60)
        assert s.rewinding is None and close(s.position, 0.0)
        assert a.slot('sfx').channel is None and a.fading_out   # the rewind sound fading
    finally:
        a.close()


def test_rewinding_an_ended_spiel_starts_it_a_second_before_its_end():
    a = fresh()
    try:
        s = a.spiel
        s.play(SHORTEST)
        s.seek(s.length - 0.05)
        wait(a, 0.4)
        assert s.ended and close(s.position, s.length, 0.01)
        s.rewind()
        assert s.playing and close(s.position, s.length - 1.0, 0.2)
    finally:
        a.close()


def test_fast_forward_speeds_up_keeps_pitch_and_ends():
    a = fresh()
    try:
        s = a.spiel
        s.play(LONG)
        base = s.slot.channel.frequency
        dsps = s.slot.channel.num_dsps
        s.update(now=50.0)
        assert s.fast_forward()
        assert close(s.slot.channel.frequency, base * FFWD_SPEED, 1.0)
        assert s.slot.channel.num_dsps == dsps + 1
        assert close(s._pitch.get_parameter_float(0)[0], 1 / FFWD_SPEED, 0.001)
        assert s._pitch.get_parameter_float(3)[0] == 2.0     # 2 channels, as the original
        s.update(now=50.0 + FFWD_FOR - 0.1)
        assert s.fast_forwarding
        s.update(now=50.0 + FFWD_FOR + 0.01)
        assert not s.fast_forwarding
        assert close(s.slot.channel.frequency, base, 1.0) and s.slot.channel.num_dsps == dsps
    finally:
        a.close()


def test_pressing_fast_forward_again_starts_its_time_over():
    a = fresh()
    try:
        s = a.spiel
        s.play(LONG)
        s.update(now=0.0)
        s.fast_forward()
        s.update(now=1.0)
        s.fast_forward()
        s.update(now=2.0)
        assert s.fast_forwarding                            # 1.5 seconds from the second press
        s.update(now=2.6)
        assert not s.fast_forwarding
    finally:
        a.close()


def test_a_pause_keeps_what_fast_forward_had_left():
    a = fresh()
    try:
        s = a.spiel
        s.play(LONG)
        s.update(now=0.0)
        s.fast_forward()
        s.update(now=1.0)
        s.pause()
        s.update(now=30.0)
        s.resume()
        s.update(now=30.4)
        assert s.fast_forwarding
        s.update(now=30.6)
        assert not s.fast_forwarding
    finally:
        a.close()


def test_a_spiel_started_during_fast_forward_fast_forwards_too():
    a = fresh()
    try:
        s = a.spiel
        s.play(LONG)
        s.update(now=0.0)
        s.fast_forward()
        s.play(SECOND)
        assert s.fast_forwarding
        assert close(s.slot.channel.frequency, s.base_frequency * FFWD_SPEED, 1.0)
    finally:
        a.close()


def test_fast_forward_stops_where_the_spiel_ends():
    a = fresh()
    try:
        s = a.spiel
        s.play(SHORTEST)
        s.update(now=0.0)
        s.fast_forward()
        s.seek(s.length - 0.05)
        wait(a, 0.4)
        assert s.ended and not s.fast_forwarding
        s.update(now=0.1)
        s.update(now=0.2)                                   # a frame's grace, then off
        assert s.ffwd_left == 0.0
    finally:
        a.close()


def test_stop_effects_plays_on():
    a = fresh()
    try:
        s = a.spiel
        s.play(LONG)
        s.update(now=0.0)
        s.fast_forward()
        s.stop_effects()
        assert not s.fast_forwarding and s.playing
        s.seek(10.0)
        s.rewind()
        s.stop_effects()
        assert s.rewinding is None and s.playing
    finally:
        a.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
