"""The background lanes and the idle loop (heathcote/platform/lanes.py), and the story
group's fades, on FMOD's no-sound output. Spiels here are made up, so each rule is tested
on its own."""
import _quiet  # noqa: F401  (first, before the game)

import os
import time

from heathcote.game.storydata import StoryData
from heathcote.platform.audio import Audio
from heathcote.platform.lanes import Lanes, lane_events
from heathcote.platform.settings import Settings

STORY = StoryData.shared()
A, B = STORY.refs('ambience')[:2]
TITLE = STORY.find('bgm', 'title')[0]
IDLE = STORY.refs('idleLoops')[0]
N = [0]


def fresh():
    N[0] += 1
    a = Audio(Settings(os.path.join(_quiet.FOLDER, 'lanes%d' % N[0], 'settings.json')))
    a.open()
    return a, Lanes(a, STORY)


def fade_to(at, soft, duration):
    return {'at': at, 'fadeTo': {'softRef': soft, 'duration': duration}}


def fade_out(at, duration):
    return {'at': at, 'fadeOut': {'duration': duration}}


def test_events_are_read_in_time_order_and_the_plain_ambience_lane_is_left_out():
    events = lane_events({'ambience1': [fade_to(5, B, 1), fade_out(9, 2), fade_to(1, A, 2)],
                          'ambience': [fade_to(0, A, 1)], 'bgm': []})
    assert events['ambience1'] == [(1.0, A, 2.0), (5.0, B, 1.0), (9.0, None, 2.0)]
    assert events['bgm'] == [] and 'ambience' not in events


def test_an_event_fires_when_playback_passes_it():
    a, lanes = fresh()
    try:
        lanes.begin_spiel({'ambience1': [fade_to(1.0, A, 2)]})
        lanes.update(0.0)
        lanes.update(0.9)
        assert not a.slot('ambience1').playing
        lanes.update(1.0)
        assert a.slot('ambience1').path == STORY.audio_path(A)
        assert lanes.holding['ambience1'] == A
        assert a.slot('ambience1').level() < 0.1            # fading in over 2 seconds
    finally:
        a.close()


def test_a_crossfade_fades_the_old_recording_out_on_its_own_channel():
    a, lanes = fresh()
    try:
        lanes.begin_spiel({'ambience1': [fade_to(0.0, A, 0), fade_to(2.0, B, 3)]})
        lanes.update(0.0)
        old = a.slot('ambience1').channel
        lanes.update(2.0)
        assert a.slot('ambience1').path == STORY.audio_path(B)
        assert any(item[0] is old for item in a.fading_out) and old.is_playing
    finally:
        a.close()


def test_a_lane_already_playing_the_recording_carries_on():
    a, lanes = fresh()
    try:
        lanes.begin_spiel({'bgm': [fade_to(0.0, TITLE, 0)]})
        lanes.update(0.0)
        channel = a.slot('bgm').channel
        lanes.begin_spiel({'bgm': [fade_to(0.5, TITLE, 2)]})
        lanes.update(0.0)
        lanes.update(1.0)
        assert a.slot('bgm').channel is channel and not a.fading_out
    finally:
        a.close()


def test_fade_out_stops_the_lane():
    a, lanes = fresh()
    try:
        lanes.begin_spiel({'ambience2': [fade_to(0.0, A, 0), fade_out(1.0, 0.5)]})
        lanes.update(0.0)
        lanes.update(1.0)
        assert a.slot('ambience2').channel is None and a.fading_out
        assert lanes.holding['ambience2'] is None
    finally:
        a.close()


def test_lanes_carry_on_from_spiel_to_spiel():
    a, lanes = fresh()
    try:
        lanes.begin_spiel({'ambience3': [fade_to(0.0, A, 0)]})
        lanes.update(0.0)
        lanes.begin_spiel({})
        lanes.update(0.0)
        lanes.update(10.0)
        assert a.slot('ambience3').playing and lanes.opening['ambience3'] == A
    finally:
        a.close()


def test_a_jump_back_sets_the_lanes_up_again_from_the_spiels_opening():
    a, lanes = fresh()
    try:
        lanes.begin_spiel({'ambience1': [fade_to(0.0, A, 0)]})
        lanes.update(0.0)
        lanes.begin_spiel({'ambience1': [fade_to(5.0, B, 2)], 'ambience2': [fade_to(3.0, A, 0)]})
        lanes.update(0.0)
        lanes.update(8.0)
        assert a.slot('ambience1').path == STORY.audio_path(B) and a.slot('ambience2').playing
        lanes.update(2.0)                                   # rewound past both events
        assert a.slot('ambience1').path == STORY.audio_path(A)
        assert not a.slot('ambience2').playing and lanes.holding['ambience2'] is None
        lanes.update(3.0)                                   # and forward again: they fire again
        assert a.slot('ambience2').playing
    finally:
        a.close()


def test_a_jump_back_into_a_crossfade_picks_it_up_part_way():
    a, lanes = fresh()
    try:
        lanes.begin_spiel({'ambience1': [fade_to(0.0, A, 0), fade_to(4.0, B, 4)]})
        lanes.update(0.0)
        lanes.update(10.0)
        a.fading_out.clear()
        lanes.update(5.0)                                   # a quarter of the way through
        slot = a.slot('ambience1')
        assert slot.path == STORY.audio_path(B)
        assert abs(slot.level() - 0.25) < 0.05              # B part way up
        assert len(a.fading_out) == 1                       # A part way down, on its own channel
    finally:
        a.close()


def test_the_story_opening_fades_each_lane_in_over_half_a_second():
    a, lanes = fresh()
    try:
        lanes.restore({'bgm': TITLE, 'ambience1': A, 'ambience2': None})
        assert a.slot('bgm').playing and a.slot('ambience1').playing
        assert not a.slot('ambience2').playing
        start = time.perf_counter()
        assert a.slot('bgm').level(start) < 0.1
        assert a.slot('bgm').level(start + 0.6) == 1.0
        assert lanes.opening == lanes.holding
    finally:
        a.close()


def test_the_idle_loop_starts_and_fades_out_over_2_seconds_with_the_next_spiel():
    from heathcote.platform.lanes import IDLE_FADE
    a, lanes = fresh()
    try:
        lanes.start_idle(IDLE)
        idle = a.slot('idleLoop')
        assert idle.playing and lanes.idle == IDLE
        assert idle.channel.mode & a.fmod.flags.MODE.LOOP_NORMAL
        channel = idle.channel
        lanes.begin_spiel({})
        assert IDLE_FADE == 2.0
        assert not idle.playing and lanes.idle is None          # the slot is free at once...
        assert any(c is channel for c, *_rest in a.fading_out)  # ...and the loop fades out
        lanes.start_idle(IDLE)
        lanes.stop_idle()                                       # as a rewind: at once
        assert not idle.playing and len(a.fading_out) == 1
    finally:
        a.close()


def test_the_story_group_fades_out_over_2_and_in_over_1():
    a, _lanes = fresh()
    try:
        a.fade_story(0.0, 2.0)
        start = time.perf_counter()
        assert 0.45 < a.story_level(start + 1.0) < 0.55
        assert a.story_level(start + 2.1) == 0.0
        a._story_fade = (0.0, 0.0, 0.0, 0.0)
        a.fade_story(1.0, 1.0)
        assert a.story_level(time.perf_counter() + 1.1) == 1.0
    finally:
        a.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
