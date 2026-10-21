"""Playing the story (heathcote/game/player.py) and its screen
(heathcote/game/story_screen.py), on the real story data and FMOD's no-sound output."""
import _quiet  # noqa: F401  (first, before the game)

import os
import time
import types

from heathcote.game.player import PLAYING, SCENE_END, STORY_END, StoryPlayer, timed_sets
from heathcote.game.state import StoryState
from heathcote.game.storydata import StoryData
from heathcote.platform.audio import Audio
from heathcote.platform.settings import Settings

STORY = StoryData.shared()
N = [0]


def spiel(label):
    return STORY.find('actionSpiels', label)[0]


def var(label):
    return STORY.find('variables', label)[0]


def fresh():
    N[0] += 1
    audio = Audio(Settings(os.path.join(_quiet.FOLDER, 'player%d' % N[0], 'settings.json')))
    audio.open()
    state = StoryState(STORY)
    sounds = []
    player = StoryPlayer(audio, STORY, state, sounds.append)
    return audio, state, player, sounds


def run_to_end(audio, player):
    """Seek the spiel to just before its end, then let it run out in real time."""
    audio.spiel.seek(audio.spiel.length - 0.05)
    player.update()
    end = time.perf_counter() + 1.0
    while time.perf_counter() < end and audio.spiel.playing:
        audio.update()
        time.sleep(0.01)
    audio.update()
    player.update()


def test_timed_sets_are_read_in_time_order():
    rec = {'set': [{'at': 5, 'set': {'b': '1'}}, {'at': 0.1, 'set': {'a': '1'}}]}
    assert timed_sets(rec) == [(0.1, {'a': '1'}), (5.0, {'b': '1'})]
    assert timed_sets({'set': {'a': '1'}}) == [(0.0, {'a': '1'})]
    assert timed_sets({}) == []


def test_the_story_starts_at_start_and_its_timed_set_applies_as_it_passes():
    audio, state, player, _sounds = fresh()
    try:
        player.start()
        assert player.current == STORY.start() and player.phase == PLAYING
        at, sets = timed_sets(STORY.record(STORY.start()))[0]
        player.update()
        audio.spiel.seek(at + 0.5)
        player.update()
        for v, value in sets.items():
            assert state.get(v) == value
    finally:
        audio.close()


def test_the_lanes_follow_the_spiel():
    audio, _state, player, _sounds = fresh()
    try:
        player.start()
        player.update()
        audio.spiel.seek(0.5)
        player.update()
        assert player.lanes.holding['ambience1'] is not None    # start brings an ambience in at 0.1
    finally:
        audio.close()


def test_a_scene_ends_with_its_idle_loop_lockout_off_menu_available_and_heard():
    audio, state, player, sounds = fresh()
    try:
        ended = []
        player.on_scene_end = ended.append
        player.start()
        state.set_by_label('lockout', '1')
        run_to_end(audio, player)
        start = STORY.start()
        assert player.phase == SCENE_END and ended == [start]
        assert not state.locked_out and state.is_heard(start)
        assert 'menu-available' in sounds
        assert player.lanes.idle == STORY.record(start)['idleLoop']
    finally:
        audio.close()


def test_a_spiel_with_a_next_that_holds_goes_straight_on_and_is_not_marked_heard():
    audio, state, player, _sounds = fresh()
    try:
        chained = next(s for s in STORY.refs('actionSpiels')
                       if STORY.record(s) and STORY.record(s).get('next') and STORY.record(s).get('file')
                       and state.next_spiel(s) is not None)
        following = state.next_spiel(chained)
        began = []
        player.on_spiel = began.append
        player.play(chained)
        run_to_end(audio, player)
        assert player.current == following and began == [chained, following]
        assert not state.is_heard(chained)
    finally:
        audio.close()


def test_a_spiel_with_no_recording_passes_straight_on():
    audio, state, player, _sounds = fresh()
    try:
        dispatch = spiel('east wing dispatch')
        player.play(dispatch)
        assert player.silent and not audio.spiel.playing
        player.update()
        following = state.next_spiel(dispatch)
        assert player.current == (following or dispatch)
        assert player.phase == (PLAYING if following else SCENE_END)
    finally:
        audio.close()


def test_timed_sets_fire_again_after_a_jump_back():
    audio, state, player, _sounds = fresh()
    try:
        fear = var('fear')
        player.start()
        player.sets = [(2.0, {fear: 'clowns'})]
        player.update()
        audio.spiel.seek(3.0)
        player.update()
        assert state.get(fear) == 'clowns'
        state.apply({fear: '0'})
        audio.spiel.seek(1.0)
        player.update()                                 # back: nothing undone, nothing fired
        assert state.get(fear) == '0'
        audio.spiel.seek(3.0)
        player.update()
        assert state.get(fear) == 'clowns'              # forward again: it fires again
    finally:
        audio.close()


def test_setting_end_ends_the_story():
    audio, state, player, _sounds = fresh()
    try:
        over = []
        player.on_story_end = lambda: over.append(True)
        player.start()
        player.sets = [(0.0, {var('end'): 'clowns'})]
        player.update()
        assert player.phase == STORY_END and over == [True] and state.ended
        player.update()
        assert over == [True]                           # once
    finally:
        audio.close()


def test_the_main_menu_starts_the_story_screen_and_escape_leaves_it():
    from heathcote.app import App
    from heathcote.game.menus import MainMenu
    from heathcote.game.story_screen import StoryScreen
    from heathcote.platform.keymap import KeyMap
    from heathcote.platform.runloop import RunLoop
    from heathcote.platform.speech import Speech
    folder = os.path.join(_quiet.FOLDER, 'screen')
    settings = Settings(os.path.join(folder, 'settings.json'))
    app = App(types.SimpleNamespace(debug=False, exit_after=None), speech=Speech(), settings=settings,
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop())
    app.audio.open()
    try:
        app.stack.push(MainMenu(app))
        assert app.title_music
        app.key_down('return', [])                      # Start story
        screen = app.stack.top
        assert isinstance(screen, StoryScreen) and not app.title_music
        assert screen.player.current == STORY.start() and app.audio.spiel.playing
        assert screen.lines()[0] == 'start' and len(screen.lines()) > 2
        app.key_down('page down', [])                   # the story's background volume
        assert settings.get('backgrounds_volume') == 90
        app.key_down('escape', [])
        assert isinstance(app.stack.top, MainMenu) and app.title_music
        assert not app.audio.spiel.playing
    finally:
        app.stack.clear()
        app.audio.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
