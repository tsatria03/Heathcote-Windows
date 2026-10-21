"""Lockout and the actions menu (heathcote/game/player.py, actions_menu.py), on the real
story data and FMOD's no-sound output. The player's clock is moved by hand."""
import _quiet  # noqa: F401  (first, before the game)

import os
import types

from heathcote.game.player import ACCEPT_DELAY, GRACE, REMINDER_EVERY, SCENE_END, StoryPlayer
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
    audio = Audio(Settings(os.path.join(_quiet.FOLDER, 'actions%d' % N[0], 'settings.json')))
    audio.open()
    state = StoryState(STORY)
    sounds, later = [], []
    clock = Clock()
    player = StoryPlayer(audio, STORY, state, sounds.append,
                         after=lambda delay, fn: later.append((delay, fn)), clock=clock)
    return audio, state, player, sounds, later, clock


def test_a_locked_spiel_refuses_the_menu_with_a_grace():
    audio, state, player, sounds, _later, clock = fresh()
    try:
        player.start()
        state.set_by_label('lockout', '1')
        assert player.open_menu() is None and not player.menu_open
        assert sounds == ['click-bad', 'menu-unavailable']
        assert player.in_grace
        clock.now += GRACE + 0.01
        assert not player.in_grace
        assert audio.hush_count == 0
    finally:
        audio.close()


def test_a_heard_spiel_opens_even_when_locked():
    audio, state, player, _sounds, _later, _clock = fresh()
    try:
        player.start()
        state.set_by_label('lockout', '1')
        state.mark_heard(STORY.start())
        assert player.open_menu() is not None
    finally:
        audio.close()


def test_opening_hushes_pauses_and_offers_the_choices():
    audio, state, player, sounds, _later, _clock = fresh()
    try:
        player.start()
        choices = player.open_menu()
        assert choices == state.offered() and player.menu_open
        assert sounds == ['click-good', 'menu-open']
        assert audio.hush_count == 1 and audio.spiel.paused
        assert player.open_menu() is None                  # already open
    finally:
        audio.close()


def test_closing_unhushes_and_plays_on():
    audio, _state, player, sounds, _later, _clock = fresh()
    try:
        player.start()
        player.open_menu()
        player.close_menu()
        assert not player.menu_open and sounds[-1] == 'menu-close'
        assert audio.hush_count == 0 and not audio.spiel.paused and audio.spiel.playing
    finally:
        audio.close()


def test_accepting_chooses_and_starts_its_spiel_a_quarter_second_later():
    audio, state, player, sounds, later, _clock = fresh()
    try:
        player.start()
        action = player.open_menu()[0]
        player.accept(action)
        assert sounds[-1] == 'menu-accepted' and audio.hush_count == 0
        assert state.count(action) == 1 and not audio.spiel.playing
        assert [delay for delay, _fn in later] == [ACCEPT_DELAY]
        assert player.open_menu() is None                  # nothing opens while it waits
        later[0][1]()
        assert player.current == STORY.record(action)['actionSpiels'][0]
        assert audio.spiel.playing and player.pending is None
    finally:
        audio.close()


def test_a_timed_set_turning_lockout_off_plays_menu_lockout_ended():
    audio, state, player, sounds, _later, _clock = fresh()
    try:
        lockout = state.variable('lockout')
        player.start()
        state.apply({lockout: '1'})
        player.sets = [(0.0, {lockout: '0'})]
        player.update()
        assert 'menu-lockout-ended' in sounds
        sounds.clear()
        player.sets = [(0.0, {lockout: '0'})]
        player.last = -1.0
        player.update()                                     # no change, no sound
        assert sounds == []
    finally:
        audio.close()


def test_after_a_scene_ends_the_reminder_plays_every_7_seconds():
    audio, _state, player, sounds, _later, clock = fresh()
    try:
        player.start()
        player._spiel_ended()
        assert player.phase == SCENE_END
        sounds.clear()
        clock.now += REMINDER_EVERY - 0.1
        player.update()
        assert sounds == []
        clock.now += 0.2
        player.update()
        assert sounds == ['menu-reminder']
        clock.now += 5
        player.poke()                                       # a key: count again
        clock.now += 5
        player.update()
        assert sounds == ['menu-reminder']
        clock.now += 2.1
        player.update()
        assert sounds == ['menu-reminder', 'menu-reminder']
    finally:
        audio.close()


def test_choices_have_clips_or_text():
    audio, state, player, _sounds, _later, _clock = fresh()
    try:
        for action in STORY.refs('actions'):
            clip = player.choice_clip(action)
            assert clip is None or os.path.isfile(clip)
            assert player.choice_text(action)
        # "next room" and "just stop" have no recording, but no action uses them, so every
        # choice in the story has its clip.
        assert all(player.choice_clip(a) for a in STORY.refs('actions'))
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
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop())
    app.audio.open()
    return app


def test_the_actions_menu_screen_plays_clips_speaks_and_accepts():
    from heathcote.game.actions_menu import ActionsMenu
    from heathcote.game.story_screen import StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        app.key_down('up', [])                              # open the menu
        menu = app.stack.top
        assert isinstance(menu, ActionsMenu) and story.player.menu_open
        assert len(menu.choices) == 1                       # at the start, only "landline"
        menu.choices = STORY.refs('actions')[:3]            # three to move through
        voice = app.audio.slot('systemVoice')
        menu.announce()
        assert voice.path == story.player.choice_clip(menu.action)     # the first clip plays
        app.key_down('down', [])
        assert menu.index == 1 and voice.path == story.player.choice_clip(menu.action)
        app.key_down('end', [])
        app.key_down('right', [])
        assert menu.index == 0                              # wrapped
        app.speech.lines.clear()
        app.key_down('space', [])
        assert app.speech.lines == [story.player.choice_text(menu.action)]
        action = menu.action
        app.key_down('return', [])                          # accept
        assert app.stack.top is story and not story.player.menu_open
        app.loop.pump(now=app.loop._calls[0].due)           # the 0.25 seconds pass
        assert story.player.current == STORY.record(action)['actionSpiels'][0]
    finally:
        app.stack.clear()
        app.audio.close()


def test_a_choice_with_no_clip_is_spoken_and_escape_closes():
    from heathcote.game.story_screen import StoryScreen
    app = make_app()
    try:
        story = StoryScreen(app)
        app.stack.push(story)
        app.key_down('up', [])
        menu = app.stack.top
        # No choice in the story lacks a clip, so a made-up one shows the screen reader
        # taking over, as it would for "next room" or "just stop".
        voice = STORY.find('systemVoice', 'next room')[0]
        STORY.records['__test__'] = {'actionSpiels': [STORY.start()], 'systemVoice': voice}
        STORY.assets['actions']['__fake__'] = '__test__'
        STORY.category['__fake__'] = 'actions'
        try:
            menu.choices.insert(0, '__fake__')
            app.speech.lines.clear()
            app.key_down('home', [])
            assert app.speech.lines == ['next room']
            assert not app.audio.slot('systemVoice').playing
        finally:
            del STORY.records['__test__'], STORY.assets['actions']['__fake__'], STORY.category['__fake__']
        app.key_down('escape', [])
        assert app.stack.top is story and not story.player.menu_open
        assert app.audio.spiel.playing and not app.audio.spiel.paused
    finally:
        app.stack.clear()
        app.audio.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
