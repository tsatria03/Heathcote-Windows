"""The audio (heathcote/platform/audio.py) and finding recordings
(heathcote/game/storydata.py), on FMOD's no-sound output: nothing here is ever heard."""
import _quiet  # noqa: F401  (first, before the game)

import os
import sys
import time
import types

from heathcote import paths
from heathcote.game.storydata import FOLDERS, StoryData, disk_name
from heathcote.platform import audio as audio_module
from heathcote.platform.audio import SLOTS, Audio, gain
from heathcote.platform.settings import Settings

N = [0]
STORY = StoryData.shared()


def fresh():
    N[0] += 1
    a = Audio(Settings(os.path.join(_quiet.FOLDER, 'audio%d' % N[0], 'settings.json')))
    a.open()
    return a


def wait(a, seconds):
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        a.update()
        time.sleep(0.01)


def test_volume_steps_are_six_decibels_and_zero_is_silence():
    assert gain(100) == 1.0
    assert abs(gain(90) - 10 ** (-6 / 20)) < 1e-9          # about half the signal
    assert abs(gain(50) - 10 ** (-30 / 20)) < 1e-9
    assert abs(gain(10) - 10 ** (-54 / 20)) < 1e-9
    assert gain(0) == 0.0
    for p in range(20, 101, 10):                           # every step the same ratio
        assert abs(gain(p) / gain(p - 10) - 10 ** (6 / 20)) < 1e-9, p


def test_fmod_starts_silently_with_the_original_channels():
    a = fresh()
    try:
        assert a.ok and a.silent
        assert set(a.slots) == set(SLOTS)
        assert set(a.groups) == {'master', 'story', 'system'}
        assert a.rate > 0
    finally:
        a.close()
    assert not a.ok


def test_a_missing_dll_stops_with_a_message():
    saved = paths.FMOD_DLL
    paths.FMOD_DLL = os.path.join(_quiet.FOLDER, 'nowhere', 'fmod.dll')
    try:
        audio_module.load_pyfmodex()
    except SystemExit as stop:
        assert 'fmod.dll, was not found' in stop.code and 'api\\core\\lib\\x64' in stop.code
    else:
        raise AssertionError('no SystemExit')
    finally:
        paths.FMOD_DLL = saved


def test_every_interface_sound_and_both_musics_and_every_ambience_are_found():
    for label in ('click-good', 'click-bad', 'ident', 'menu-open', 'menu-available',
                  'menu-unavailable', 'menu-accepted', 'menu-close', 'menu-reminder',
                  'menu-lockout-ended', 'rewind', 'pause-pause', 'pause-unpause', 'lost focus'):
        path = STORY.sound_path('systemSounds', label)
        assert path and os.path.isfile(path), label
    for label in ('title', 'ending'):
        assert os.path.isfile(STORY.sound_path('bgm', label)), label
    for soft in STORY.refs('ambience'):
        assert os.path.isfile(STORY.audio_path(soft)), STORY.label(soft)


def test_the_tool_and_the_game_share_one_rule():
    sys.path.insert(0, os.path.join(_quiet.ROOT, 'tools'))
    import story
    assert story.FOLDERS is FOLDERS and story.disk_name is disk_name
    assert issubclass(story.Story, StoryData)
    assert disk_name('idle loop (inside entrance) .m4a') == 'idle loop (inside entrance).mp3'


def test_a_loop_plays_and_keeps_playing():
    a = fresh()
    try:
        slot = a.slot('titleBgm')
        assert slot.play(STORY.sound_path('bgm', 'title'))
        wait(a, 0.2)
        assert slot.playing
        assert slot.channel.mode & a.fmod.flags.MODE.LOOP_NORMAL
    finally:
        a.close()


def test_a_slot_plays_one_recording_at_a_time():
    a = fresh()
    try:
        slot = a.slot('sfx')
        first = STORY.sound_path('systemSounds', 'click-good')
        second = STORY.sound_path('systemSounds', 'click-bad')
        slot.play(first)
        slot.play(second)
        assert slot.path == second and slot.playing
    finally:
        a.close()


def test_each_slot_follows_its_own_volume_and_the_master_is_on_the_master_group():
    a = fresh()
    try:
        s = a.settings
        s.set('master_volume', 80)
        s.set('backgrounds_volume', 50)
        s.set('interface_volume', 70)
        s.set('title_volume', 90)
        a.slot('ambience1').play(STORY.audio_path(STORY.refs('ambience')[0]))
        a.slot('titleBgm').play(STORY.sound_path('bgm', 'title'))
        a.slot('sfx').play(STORY.sound_path('systemSounds', 'click-good'))
        a.apply_volumes()
        close = lambda x, y: abs(x - y) < 1e-4
        assert close(a.groups['master'].volume, gain(80))
        assert close(a.slot('ambience1').channel.volume, gain(50))
        assert close(a.slot('titleBgm').channel.volume, gain(90))
        assert close(a.slot('sfx').channel.volume, gain(70))
        s.set('master_volume', 0)
        a.apply_volumes()
        assert a.groups['master'].volume == 0.0
    finally:
        a.close()


def test_a_fade_out_stops_the_channel_once_it_ends():
    a = fresh()
    try:
        slot = a.slot('ambience1')
        slot.play(STORY.audio_path(STORY.refs('ambience')[0]))
        channel = slot.channel
        slot.stop(fade_out=0.3)
        assert slot.channel is None and not slot.playing
        assert a.fading_out and channel.is_playing          # still fading
        wait(a, 0.8)
        assert not a.fading_out                             # stopped and freed
    finally:
        a.close()


def test_a_fade_goes_between_its_levels():
    a = fresh()
    try:
        slot = a.slot('bgm')
        slot.play(STORY.sound_path('bgm', 'title'), fade_in=1.0)
        start = time.perf_counter()
        assert slot.level(start) < 0.1
        assert 0.4 < slot.level(start + 0.5) < 0.6
        assert slot.level(start + 1.5) == 1.0
        slot.fade_to(0.25, 0.0)                             # straight to a level
        assert slot.level() == 0.25
    finally:
        a.close()


def test_the_hush_is_the_originals_eq_and_ramps_at_its_speeds():
    a = fresh()
    try:
        bgm = a.slot('bgm')
        bgm.play(STORY.sound_path('bgm', 'title'))
        idle = a.slot('idleLoop')
        idle.play(STORY.audio_path(STORY.refs('ambience')[0]))
        a.update(now=0.0)
        a.hush_backgrounds()
        assert bgm.eq is not None and idle.eq is None       # never the idle loop
        assert bgm.eq.get_parameter_float(0)[0] == 1250.0
        assert bgm.eq.get_parameter_float(1)[0] == 5.0
        a.update(now=15 / 60 + 1e-6)                        # 15 ticks: not quite there
        assert -12.0 < bgm.eq_gain < -11.0
        a.update(now=16 / 60 + 1e-6)
        assert bgm.eq_gain == -12.0 and bgm.eq_step == 0.0
        assert abs(bgm.eq.get_parameter_float(2)[0] + 12.0) < 1e-4
        a.unhush_backgrounds()
        a.update(now=(16 + 23) / 60 + 1e-6)                 # 23 of the 24 ticks back up
        assert bgm.eq is not None and bgm.eq_gain < 0
        a.update(now=(16 + 24) / 60 + 1e-6)
        assert bgm.eq is None                               # fully unhushed: the effect is off
    finally:
        a.close()


def test_hushes_nest_and_a_lane_started_while_hushed_is_muffled_at_once():
    a = fresh()
    try:
        a.hush_backgrounds()
        a.hush_backgrounds()
        lane = a.slot('ambience2')
        lane.play(STORY.audio_path(STORY.refs('ambience')[1]))
        assert lane.eq is not None and lane.eq_gain == -12.0
        a.unhush_backgrounds()
        assert lane.eq_step == 0.0                          # still hushed once
        a.unhush_backgrounds()
        assert lane.eq_step > 0
        a.unhush_backgrounds()                              # one too many does nothing
        assert a.hush_count == 0
    finally:
        a.close()


def test_a_silent_channel_is_not_hushed():
    a = fresh()
    try:
        a.hush_backgrounds()
        assert all(a.slot(n).eq is None for n in ('bgm', 'ambience1', 'ambience2', 'ambience3'))
    finally:
        a.close()


def test_the_app_plays_interface_sounds_and_passes_volumes_on():
    from heathcote.app import App
    from heathcote.platform.keymap import KeyMap
    from heathcote.platform.runloop import RunLoop
    from heathcote.platform.speech import Speech
    folder = os.path.join(_quiet.FOLDER, 'app')
    settings = Settings(os.path.join(folder, 'settings.json'))
    app = App(types.SimpleNamespace(debug=False, exit_after=None), speech=Speech(), settings=settings,
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop())
    app.audio.open()
    try:
        app.play_sound('click-good')
        assert app.audio.slot('sfx').playing
        app.play_sound('no such sound')                     # logged, nothing breaks
        settings.set('master_volume', 60)
        app.volumes_changed()
        assert abs(app.audio.groups['master'].volume - gain(60)) < 1e-4
    finally:
        app.audio.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
