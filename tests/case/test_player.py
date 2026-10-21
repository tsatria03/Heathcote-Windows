"""Playing the story (heathcote/game/player.py) and its screen
(heathcote/game/story_screen.py), on the real story data and FMOD's no-sound output."""
import _quiet  # noqa: F401  (first, before the game)

from heathcote.game.progress import Progress  # noqa: E402

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


def test_the_main_menu_starts_the_story_screen_and_return_to_menu_leaves_it():
    from heathcote.app import App
    from heathcote.game.menus import MainMenu
    from heathcote.game.story_screen import StoryScreen
    from heathcote.platform.keymap import KeyMap
    from heathcote.platform.runloop import RunLoop
    from heathcote.platform.speech import Speech
    folder = os.path.join(_quiet.FOLDER, 'screen')
    settings = Settings(os.path.join(folder, 'settings.json'))
    app = App(types.SimpleNamespace(debug=False, exit_after=None), speech=Speech(), settings=settings,
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop(),
              progress=Progress(os.path.join(folder, 'progress.json')))
    app.audio.open()
    title = app.audio.slot('titleBgm')
    try:
        app.stack.push(MainMenu(app))
        assert app.title_music and title.playing and title.path.endswith('Title.mp3')
        assert app.audio.story_target == 0.0           # the story group fades out under it
        app.key_down('return', [])                      # Start story
        screen = app.stack.top
        assert isinstance(screen, StoryScreen) and not app.title_music
        # Fading out over 3 seconds, handed to FMOD, while the story group fades in.
        assert title.channel is None and len(app.audio.fading_out) >= 1
        assert app.audio.story_target == 1.0
        assert screen.player.current == STORY.start() and app.audio.spiel.playing
        assert screen.lines()[0] == 'start' and len(screen.lines()) > 2
        app.key_down('page down', [])                   # the story's background volume
        assert settings.get('backgrounds_volume') == 90
        app.key_down('escape', [])                      # pause, then the pause menu
        app.key_down('end', [])
        app.key_down('return', [])                      # Return to menu
        assert isinstance(app.stack.top, MainMenu) and app.title_music
        assert title.playing                            # again, as the menu comes back
        # The story is kept, paused, its backgrounds fading out under the title music.
        assert app.paused_story is screen and app.audio.story_paused
        assert app.audio.spiel.paused and app.audio.story_target == 0.0
        assert screen.player.current == STORY.start()
        assert app.stack.top.row_text().startswith('Continue story')
        app.key_down('return', [])                      # Continue story
        assert app.stack.top is screen and app.paused_story is None
        assert not app.audio.story_paused and not app.audio.spiel.paused
        assert title.channel is None and app.audio.story_target == 1.0
        assert screen.player.current == STORY.start()   # picked up exactly there
    finally:
        app.stack.clear()
        app.audio.close()


def story_app(name, start=True, start_spiel=None):
    """An app on FMOD's no-sound output, with its own save in a folder named ``name``, at
    the main menu; with ``start``, Enter is pressed on its first row. Made again with the
    same name, it is the next run, reading the progress the last one wrote."""
    from heathcote.app import App
    from heathcote.game.menus import MainMenu
    from heathcote.platform.keymap import KeyMap
    from heathcote.platform.runloop import RunLoop
    from heathcote.platform.speech import Speech

    class Listening(Speech):
        def __init__(self):
            super().__init__()
            self.lines = []

        def speak(self, text, interrupt=True):
            self.lines.append(text)
            return super().speak(text, interrupt)

    folder = os.path.join(_quiet.FOLDER, name)
    app = App(types.SimpleNamespace(debug=False, exit_after=None), speech=Listening(),
              settings=Settings(os.path.join(folder, 'settings.json')),
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop(),
              progress=Progress(os.path.join(folder, 'progress.json')))
    app.audio.open()
    app.start_spiel = start_spiel
    app.stack.push(MainMenu(app))
    if start:
        app.key_down('return', [])                      # Start story, or Continue story
    return app, app.stack.top


def quit_app(app):
    app.stack.clear()
    app.audio.close()


def test_progress_is_written_as_spiels_begin_and_continue_story_picks_it_up_next_run():
    from heathcote.game.story_screen import StoryScreen
    app, screen = story_app('next run')
    try:
        assert app.progress.under_way and app.progress.spiel == STORY.start()
        app.audio.spiel.seek(0.3)                       # past start's sets and its first fade
        screen.update()
        assert app.progress.chapter == 'working late'
        held = screen.player.lanes.holding['ambience1']
        assert held is not None
        screen.state.set_by_label('fear', 'clowns')
        screen.player.play(spiel('cells'))              # as a choice or a next would
        assert app.progress.spiel == spiel('cells') and app.progress.lanes['ambience1'] == held
    finally:
        quit_app(app)
    app, menu = story_app('next run', start=False)      # the game started again
    try:
        assert menu.row_text() == 'Continue story: working late.'
        app.key_down('return', [])
        story = app.stack.top
        assert isinstance(story, StoryScreen) and story.player.current == spiel('cells')
        assert story.state.get_by_label('fear') == 'clowns'
        assert story.player.lanes.holding['ambience1'] == held
        assert app.audio.slot('ambience1').playing and app.audio.spiel.playing
        assert story.saving
    finally:
        quit_app(app)


def test_a_scene_heard_to_its_end_is_kept_heard_in_the_save():
    app, screen = story_app('heard')
    try:
        run_to_end(app.audio, screen.player)
        assert screen.player.phase == SCENE_END
        assert STORY.start() in app.progress.state['heard']
    finally:
        quit_app(app)


def test_restart_story_begins_the_save_afresh():
    app, screen = story_app('restart save')
    try:
        screen.state.set_by_label('fear', 'clowns')
        screen.player.play(spiel('cells'))
        app.key_down('escape', [])
        app.key_down('down', [])
        app.key_down('return', [])                      # Restart story
        app.key_down('down', [])
        app.key_down('return', [])                      # Yes
        assert app.progress.under_way and app.progress.spiel == STORY.start()
        assert app.progress.state['heard'] == []
        assert app.progress.state['variables'][screen.state.variable('fear')] == '0'
    finally:
        quit_app(app)


def test_the_end_clears_the_save_so_the_next_run_offers_start_story():
    app, screen = story_app('end save')
    try:
        screen.player.play(spiel('ending (commercial)'))
        assert app.progress.under_way
        app.audio.spiel.seek(59.6)
        screen.update()
        assert not app.progress.under_way               # quitting in the credits: a new story
        app.key_down('escape', [])
        assert not app.progress.under_way
    finally:
        quit_app(app)
    app, menu = story_app('end save', start=False)
    try:
        assert menu.row_text() == 'Start story'
    finally:
        quit_app(app)


def test_spiel_and_a_debug_jump_write_no_progress():
    app, screen = story_app('debug save', start_spiel=spiel('cells'))
    try:
        assert screen.player.current == spiel('cells') and not app.progress.under_way
    finally:
        quit_app(app)
    app, screen = story_app('debug jump')
    try:
        assert app.progress.spiel == STORY.start()
        screen.stop_saving()                            # as F3's jump does
        screen.player.jump(spiel('cells'))
        assert app.progress.spiel == STORY.start()      # the real progress is kept
    finally:
        quit_app(app)


def test_the_pause_menus_rows_and_settings_from_it():
    from heathcote.game.story_screen import PauseMenu
    from heathcote.ui.settings_screen import SettingsScreen
    app, screen = story_app('pause rows')
    try:
        app.key_down('escape', [])
        assert [r.text for r in app.stack.top.rows()] == ['Resume', 'Restart story', 'Settings',
                                                          'Return to menu']
        app.key_down('down', [])
        app.key_down('down', [])
        app.key_down('return', [])
        assert isinstance(app.stack.top, SettingsScreen) and screen.player.paused
        assert not app.title_music                      # silent while paused
        app.key_down('escape', [])
        assert isinstance(app.stack.top, PauseMenu) and screen.player.paused
    finally:
        app.stack.clear()
        app.audio.close()


def test_restart_story_asks_with_no_first_and_yes_starts_again():
    from heathcote.game.story_screen import RESTART_QUESTION, PauseMenu, StoryScreen
    app, screen = story_app('restart')
    try:
        state = screen.state
        location = state.variable('location')
        state.apply({location: 'offices'})
        state.mark_heard(STORY.start())
        app.key_down('escape', [])
        app.key_down('down', [])
        app.speech.lines.clear()
        app.key_down('return', [])                      # Restart story
        assert app.speech.lines == [RESTART_QUESTION, 'No']
        app.key_down('return', [])                      # No
        assert isinstance(app.stack.top, PauseMenu) and state.get(location) == 'offices'
        app.key_down('return', [])                      # still on Restart story
        app.key_down('escape', [])                      # Escape is No too
        assert isinstance(app.stack.top, PauseMenu)
        app.key_down('return', [])                      # Restart story, at the row it was on
        app.key_down('down', [])
        app.key_down('return', [])                      # Yes
        assert isinstance(app.stack.top, StoryScreen) and app.stack.top is screen
        assert state.get(location) == '0' and not state.heard
        assert screen.player.current == STORY.start() and not screen.player.paused
        assert app.audio.spiel.playing and not app.audio.spiel.paused and app.audio.hush_count == 0
        assert app.speech.lines[-1] == 'The story starts again.'
    finally:
        app.stack.clear()
        app.audio.close()


def test_continue_story_says_its_chapter():
    from heathcote.game.menus import MainMenu
    app, screen = story_app('chapter')
    try:
        screen.state.set_by_label('location', 'cell block C')
        app.key_down('escape', [])
        app.key_down('end', [])
        app.key_down('return', [])                      # Return to menu
        menu = app.stack.top
        assert isinstance(menu, MainMenu)
        assert menu.row_text() == 'Continue story: cell block C.'
        assert [r.text for r in menu.rows()][1:] == ['Settings', 'Credits', 'Quit']
    finally:
        app.stack.clear()
        app.audio.close()


def test_the_end_credits_open_over_the_story_which_plays_on_with_its_ending_music():
    from heathcote.game.credits import EndCredits
    from heathcote.game.menus import MainMenu
    from heathcote.platform.keymap import STORY_VOLUMES
    app, screen = story_app('the end')
    try:
        screen.player.play(spiel('ending (commercial)'))
        app.audio.spiel.seek(59.6)                      # just past "end becomes 1"
        app.speech.lines.clear()
        screen.update()
        credits = app.stack.top
        assert isinstance(credits, EndCredits) and screen.state.ended
        assert app.speech.lines == ['The story has ended. Credits.', 'Back']
        assert app.audio.spiel.playing and not app.audio.spiel.paused   # it plays on beneath
        assert credits.volume_group() == STORY_VOLUMES and not app.title_music
        app.audio.spiel.seek(68.5)                      # past the music's fade to "ending"
        credits.update()
        assert 'ending' in os.path.basename(app.audio.slot('bgm').path).lower()
        app.key_down('escape', [])                      # leaving the credits
        menu = app.stack.top
        assert isinstance(menu, MainMenu) and app.title_music
        assert menu.row_text() == 'Start story' and app.paused_story is None
        assert not screen.state.ended and screen.state.get_by_label('location') == '0'
        assert not app.audio.spiel.playing
    finally:
        app.stack.clear()
        app.audio.close()


def test_back_in_the_end_credits_leaves_them_too():
    from heathcote.game.credits import EndCredits
    from heathcote.game.menus import MainMenu
    app, screen = story_app('the end, back')
    try:
        screen.player.play(spiel('ending (commercial)'))
        app.audio.spiel.seek(59.6)
        screen.update()
        assert isinstance(app.stack.top, EndCredits)
        app.key_down('return', [])                      # Back, the row it opens on
        assert isinstance(app.stack.top, MainMenu) and not screen.state.ended
    finally:
        app.stack.clear()
        app.audio.close()


def test_the_opening_plays_the_police_radio_on_sfx_and_enter_stops_it():
    from heathcote.app import App
    from heathcote.game.menus import MainMenu
    from heathcote.game.opening import NoticeScreen, OpeningScreen
    from heathcote.platform.keymap import KeyMap
    from heathcote.platform.runloop import RunLoop
    from heathcote.platform.speech import Speech
    folder = os.path.join(_quiet.FOLDER, 'opening')
    settings = Settings(os.path.join(folder, 'settings.json'))
    app = App(types.SimpleNamespace(debug=False, exit_after=None), speech=Speech(), settings=settings,
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop(),
              progress=Progress(os.path.join(folder, 'progress.json')))
    app.audio.open()
    sfx = app.audio.slot('sfx')
    try:
        app.stack.push(OpeningScreen(app))
        assert sfx.playing and 'ident' in os.path.basename(sfx.path)
        assert not app.title_music                      # not until the main menu
        app.stack.top.update()
        assert isinstance(app.stack.top, OpeningScreen)  # still playing
        app.key_down('return', [])
        assert not sfx.playing and isinstance(app.stack.top, NoticeScreen)
        app.key_down('return', [])
        assert isinstance(app.stack.top, MainMenu) and app.audio.slot('titleBgm').playing
    finally:
        app.stack.clear()
        app.audio.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
