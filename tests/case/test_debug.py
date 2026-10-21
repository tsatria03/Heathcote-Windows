"""Debug mode's keys (heathcote/game/player.py, story_screen.py, ui/search.py) and
--spiel's start, on the real story data and FMOD's no-sound output."""
import _quiet  # noqa: F401  (first, before the game)

from heathcote.game.progress import Progress  # noqa: E402

import os
import types

from heathcote.game.storydata import StoryData
from heathcote.platform.settings import Settings

STORY = StoryData.shared()
N = [0]


def spiel(label):
    return STORY.find('actionSpiels', label)[0]


def make_app(debug=True):
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
    folder = os.path.join(_quiet.FOLDER, 'debug%d' % N[0])
    app = App(types.SimpleNamespace(debug=debug, exit_after=None), speech=Listening(),
              settings=Settings(os.path.join(folder, 'settings.json')),
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop(),
              progress=Progress(os.path.join(folder, 'progress.json')))
    app.audio.open()
    return app


def story_on(app, start_at=None):
    from heathcote.game.story_screen import StoryScreen
    sounds = []
    play = app.play_sound
    app.play_sound = lambda label: (sounds.append(label), play(label))
    story = StoryScreen(app, start_at=start_at)
    app.stack.push(story)
    return story, sounds


def type_text(app, text):
    for ch in text:
        app.key_down('space' if ch == ' ' else ch.lower(), [], char=ch)


def test_f4_speaks_the_variables_that_are_not_zero():
    app = make_app()
    try:
        story, _sounds = story_on(app)
        app.speech.lines.clear()
        app.key_down('f4', [])
        assert app.speech.lines == ['Every variable is 0.']
        story.state.apply({STORY.find('variables', 'fear')[0]: 'clowns'})
        app.speech.lines.clear()
        app.key_down('f4', [])
        assert app.speech.lines == ['fear is clowns.']
    finally:
        app.stack.clear()
        app.audio.close()


def test_f2_skips_to_the_end_firing_what_waits():
    app = make_app()
    try:
        story, sounds = story_on(app, start_at=spiel('call opening'))
        story.player.update()
        app.audio.spiel.seek(1.0)
        story.player.update()
        assert story.state.locked_out                       # locked from 0.1 to 44.7 seconds
        app.key_down('f2', [])
        assert not story.state.locked_out and 'menu-lockout-ended' in sounds
        assert app.audio.spiel.position > app.audio.spiel.length - 0.1
    finally:
        app.stack.clear()
        app.audio.close()


def test_f2_does_nothing_while_paused():
    app = make_app()
    try:
        _story, _sounds = story_on(app)
        app.key_down('escape', [])                          # the pause menu has the keys now
        app.stack.top.resume()
        _story.player.pause()
        app.speech.lines.clear()
        assert not _story.player.skip()
    finally:
        app.stack.clear()
        app.audio.close()


def test_f3_finds_a_spiel_by_part_of_its_label_and_jumps_keeping_the_variables():
    from heathcote.ui.search import SearchScreen
    app = make_app()
    try:
        story, _sounds = story_on(app)
        fear = STORY.find('variables', 'fear')[0]
        story.state.apply({fear: 'clowns'})
        app.key_down('f3', [])
        assert isinstance(app.stack.top, SearchScreen)
        app.speech.lines.clear()
        type_text(app, 'CELLs')
        assert app.speech.lines == ['C', 'E', 'L', 'L', 's']
        app.key_down('backspace', [], char='\b')
        app.key_down('s', [], char='s')
        app.speech.lines.clear()
        app.key_down('return', [], char='\r')
        assert app.stack.top is story
        count = sum(1 for s in STORY.refs('actionSpiels')
                    if STORY.record(s) and 'cells' in STORY.label(s).lower())
        first = story.player.current
        assert app.speech.lines[0] == '%s, 1 of %d matches.' % (STORY.label(first), count)
        assert 'cells' in STORY.label(first).lower()
        assert story.state.get(fear) == 'clowns'            # kept
        app.key_down('f3', [])
        type_text(app, 'cells')
        app.key_down('return', [], char='\r')
        assert story.player.current != first                # the same text moves on
    finally:
        app.stack.clear()
        app.audio.close()


def test_f3_with_no_match_says_so_and_escape_gives_up():
    from heathcote.ui.search import SearchScreen
    app = make_app()
    try:
        story, _sounds = story_on(app)
        before = story.player.current
        app.key_down('f3', [])
        type_text(app, 'zzz')
        app.speech.lines.clear()
        app.key_down('return', [], char='\r')
        assert app.speech.lines == ['Nothing has "zzz" in its name.']
        assert isinstance(app.stack.top, SearchScreen)
        app.key_down('escape', [], char='\x1b')
        assert app.stack.top is story and story.player.current == before
    finally:
        app.stack.clear()
        app.audio.close()


def test_the_debug_keys_do_nothing_out_of_debug_mode():
    app = make_app(debug=False)
    try:
        story, _sounds = story_on(app)
        app.speech.lines.clear()
        for key in ('f2', 'f3', 'f4'):
            app.key_down(key, [])
        assert app.stack.top is story and app.speech.lines == []
    finally:
        app.stack.clear()
        app.audio.close()


def test_start_story_begins_at_the_spiel_spiel_named_once():
    from heathcote.game.menus import MainMenu
    app = make_app()
    try:
        app.start_spiel = spiel('cells')
        app.stack.push(MainMenu(app))
        app.key_down('return', [])
        assert app.stack.top.player.current == spiel('cells')
        app.stack.pop()
        app.key_down('return', [])                          # the next Start story is from the start
        assert app.stack.top.player.current == STORY.start()
    finally:
        app.stack.clear()
        app.audio.close()


if __name__ == '__main__':
    _quiet.run_tests(globals())
