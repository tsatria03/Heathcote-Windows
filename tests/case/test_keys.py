"""The keys during play (heathcote/game/player.py, story_screen.py): rewind, fast-forward,
pause with the pause menu, Tab, and losing the window, on FMOD's no-sound output."""
import _quiet  # noqa: F401  (first, before the game)

from heathcote.game.progress import Progress  # noqa: E402

import os
import types

from heathcote.game.player import PLAYING, SCENE_END, StoryPlayer
from heathcote.game.state import StoryState
from heathcote.game.storydata import StoryData
from heathcote.platform.audio import Audio
from heathcote.platform.settings import Settings

STORY = StoryData.shared()
N = [0]


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def fresh():
    N[0] += 1
    audio = Audio(Settings(os.path.join(_quiet.FOLDER, 'keys%d' % N[0], 'settings.json')))
    audio.open()
    audio.spiel.rewind_sound = STORY.sound_path('systemSounds', 'rewind')
    state = StoryState(STORY)
    sounds = []
    clock = Clock()
    player = StoryPlayer(audio, STORY, state, sounds.append, clock=clock)
    return audio, state, player, sounds, clock


def test_rewind_and_fast_forward_click_good_and_work():
    audio, _state, player, sounds, _clock = fresh()
    try:
        player.start()
        audio.spiel.seek(8.0)
        assert player.rewind() and sounds == ['click-good'] and audio.spiel.rewinding
        audio.spiel.stop_effects()
        assert player.fast_forward() and sounds == ['click-good', 'click-good']
        assert audio.spiel.fast_forwarding
    finally:
        audio.close()


def test_no_rewind_or_fast_forward_under_the_menu():
    audio, _state, player, sounds, _clock = fresh()
    try:
        player.start()
        player.open_menu()
        sounds.clear()
        assert not player.rewind() and not player.fast_forward() and sounds == []
    finally:
        audio.close()


def test_rewinding_an_ended_scene_plays_it_again_and_stops_the_idle_loop():
    import time
    audio, _state, player, _sounds, _clock = fresh()
    try:
        player.start()
        audio.spiel.seek(audio.spiel.length - 0.05)        # let it truly run out
        end = time.perf_counter() + 1.0
        while time.perf_counter() < end and audio.spiel.playing:
            audio.update()
            time.sleep(0.01)
        player.update()
        assert player.phase == SCENE_END and player.lanes.idle
        assert player.rewind()
        assert player.phase == PLAYING and player.lanes.idle is None
        assert audio.spiel.playing and player.reminder_at is None
    finally:
        audio.close()


def test_pause_hushes_stops_the_spiel_and_resume_brings_it_back():
    audio, _state, player, sounds, _clock = fresh()
    try:
        player.start()
        assert player.pause() and player.paused
        assert sounds == ['pause-pause'] and audio.hush_count == 1 and audio.spiel.paused
        assert not player.pause()                           # already paused
        player.resume()
        assert not player.paused and sounds[-1] == 'pause-unpause' and audio.hush_count == 0
    finally:
        audio.close()


def test_pausing_is_refused_during_the_grace():
    audio, state, player, sounds, clock = fresh()
    try:
        player.start()
        state.set_by_label('lockout', '1')
        player.open_menu()                                  # refused: the grace starts
        sounds.clear()
        assert not player.pause() and sounds == ['click-bad'] and not player.paused
        clock.now += 1.6
        assert player.pause()
    finally:
        audio.close()


def test_tab_says_where_you_are():
    audio, _state, player, _sounds, _clock = fresh()
    try:
        player.start()
        assert player.where() == 'Story is playing.'
        player.open_menu()
        assert player.where() == 'Actions menu is open.'
        player.close_menu()
        player._spiel_ended()
        assert player.where() == 'Story is at end of scene.'
        player.pause()
        assert player.where() == 'Story is paused.'
    finally:
        audio.close()


def test_no_reminder_while_paused():
    audio, _state, player, sounds, clock = fresh()
    try:
        player.start()
        player._spiel_ended()
        player.pause()
        sounds.clear()
        clock.now += 30
        player.update()
        assert 'menu-reminder' not in sounds
    finally:
        audio.close()


def make_app():
    from heathcote.app import App
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

    N[0] += 1
    folder = os.path.join(_quiet.FOLDER, 'app%d' % N[0])
    app = App(types.SimpleNamespace(debug=False, exit_after=None), speech=Listening(),
              settings=Settings(os.path.join(folder, 'settings.json')),
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop(),
              progress=Progress(os.path.join(folder, 'progress.json')))
    app.audio.open()
    return app


def test_a_story_screen_can_be_made_before_fmod_starts():
    """As story_check.py makes its screen before the main loop starts FMOD; this once
    stopped the tool as it opened."""
    from heathcote.game.story_screen import StoryScreen
    app = make_app()
    app.audio.close()                                   # as before App.run() opens it
    try:
        story = StoryScreen(app)
        app.audio.open()
        app.stack.push(story)
        assert app.audio.spiel.rewind_sound.endswith('rewind-try2.mp3')
        assert app.audio.spiel.playing
    finally:
        app.stack.clear()
        app.audio.close()


def test_escape_pauses_with_the_pause_menu_and_resume_plays_on():
    from heathcote.game.story_screen import PauseMenu, StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        app.speech.lines.clear()
        app.key_down('escape', [])
        menu = app.stack.top
        assert isinstance(menu, PauseMenu) and story.player.paused
        assert app.speech.lines == ['Paused.', 'Resume']
        app.key_down('return', [])                          # Resume
        assert app.stack.top is story and not story.player.paused
        assert app.audio.spiel.playing and not app.audio.spiel.paused
        app.key_down('escape', [])
        app.key_down('escape', [])                          # Escape in the pause menu resumes too
        assert app.stack.top is story and not story.player.paused
    finally:
        app.stack.clear()
        app.audio.close()


def test_escape_clicks_with_the_pause_sound_but_losing_the_window_does_not():
    from heathcote.game.story_screen import StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        asked = []
        app.play_sound = asked.append
        story.player.play_sound = asked.append
        app.key_down('escape', [])
        assert asked == ['click-good', 'pause-pause']
        app.key_down('return', [])                          # Resume, which clicks as any menu
        asked.clear()
        story.focus_lost()
        assert asked == ['lost focus', 'pause-pause']
    finally:
        app.stack.clear()
        app.audio.close()


def test_the_keys_reach_the_player_and_tab_speaks():
    from heathcote.game.story_screen import StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        app.audio.spiel.seek(8.0)
        app.key_down('left', [])
        assert app.audio.spiel.rewinding
        app.key_down('right', [])
        assert app.audio.spiel.fast_forwarding
        app.speech.lines.clear()
        app.key_down('tab', [])
        assert app.speech.lines == ['Story is playing.']
        app.key_down('up', [])                              # the actions menu
        app.speech.lines.clear()
        app.key_down('tab', [])
        assert app.speech.lines == ['Actions menu is open.']
    finally:
        app.stack.clear()
        app.audio.close()


def test_tab_says_the_chapter_once_a_scene_has_set_it():
    from heathcote.game.story_screen import StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        story.state.set_by_label('location', '0')
        app.speech.lines.clear()
        app.key_down('tab', [])
        assert app.speech.lines == ['Story is playing.']             # none set yet
        story.state.set_by_label('location', 'approaching Heathcote')
        app.speech.lines.clear()
        app.key_down('tab', [])
        assert app.speech.lines == ['Story is playing: approaching Heathcote.']
        app.key_down('up', [])                                        # the actions menu too
        app.speech.lines.clear()
        app.key_down('tab', [])
        assert app.speech.lines == ['Actions menu is open: approaching Heathcote.']
        app.key_down('escape', [])
        app.key_down('escape', [])                                    # paused
        assert story.player.where() == 'Story is paused: approaching Heathcote.'
    finally:
        app.stack.clear()
        app.audio.close()


def test_losing_the_window_pauses_and_closes_the_actions_menu():
    from heathcote.game.story_screen import PauseMenu, StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        app.key_down('up', [])
        assert story.player.menu_open
        app.stack.top.focus_lost()
        assert not story.player.menu_open and story.player.paused
        assert isinstance(app.stack.top, PauseMenu)
        assert app.audio.hush_count == 1                    # the pause's hush only
        app.key_down('return', [])
        story.focus_lost()                                  # straight from the story
        assert story.player.paused and isinstance(app.stack.top, PauseMenu)
    finally:
        app.stack.clear()
        app.audio.close()


def test_getting_the_window_back_resumes_a_pause_it_made_but_not_one_made_with_escape():
    from heathcote.game.story_screen import PauseMenu, StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        story.focus_lost()
        assert story.player.paused
        app.stack.top.focus_gained()                        # back in the window
        assert app.stack.top is story and not story.player.paused
        assert app.audio.spiel.playing and not app.audio.spiel.paused
        app.key_down('escape', [])                          # paused by hand
        story.focus_lost()                                  # already paused: nothing more
        app.stack.top.focus_gained()
        assert isinstance(app.stack.top, PauseMenu) and story.player.paused
    finally:
        app.stack.clear()
        app.audio.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
