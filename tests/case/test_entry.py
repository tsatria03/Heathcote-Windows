"""Heathcote.py: its options, the log, the crash file and --spiel."""
import _quiet  # noqa: F401  (first, before the game)

import logging
import os
import types

import Heathcote
from heathcote import paths


def _crash_text():
    with open(os.path.join(paths.logs_dir(), 'crash.txt'), encoding='utf-8') as f:
        return f.read()


def test_options():
    o = Heathcote.parse_args(['--debug', '--spiel', 'start', '-v', '--exit-after', '1.5'])
    assert o.debug and o.spiel == 'start' and o.verbose and o.exit_after == 1.5
    o = Heathcote.parse_args([])
    assert not o.debug and o.spiel is None and not o.verbose and o.exit_after is None


def test_log_keeps_the_run_before():
    root = logging.getLogger()
    for handler in [h for h in root.handlers if isinstance(h, logging.FileHandler)]:
        root.removeHandler(handler)         # Windows will not move a log that is still open
        handler.close()
    folder = paths.logs_dir()
    with open(os.path.join(folder, 'log.txt'), 'w', encoding='utf-8') as f:
        f.write('the run before\n')
    Heathcote.start_log(False)
    logging.getLogger('heathcote').info('this run')
    with open(os.path.join(folder, 'log.old.txt'), encoding='utf-8') as f:
        assert f.read() == 'the run before\n'


def test_crash_file_says_what_happened():
    Heathcote.write_crash('Traceback: something broke\n')
    text = _crash_text()
    assert text.startswith('Heathcote stopped because of an error.')
    assert 'Running from: source' in text and 'something broke' in text


def test_an_error_writes_the_crash_file_and_returns_1():
    saved = Heathcote.get_speech
    Heathcote.get_speech = lambda: None
    import heathcote.app
    saved_run = heathcote.app.App.run
    heathcote.app.App.run = lambda self, first, pygame: 1 / 0
    try:
        assert Heathcote.main([]) == 1
    finally:
        heathcote.app.App.run = saved_run
        Heathcote.get_speech = saved
    assert 'ZeroDivisionError' in _crash_text()


def test_spiel_needs_debug_mode_and_a_spiels_label():
    from heathcote.game.storydata import StoryData
    story = StoryData.shared()
    o = types.SimpleNamespace(spiel='cells')
    assert Heathcote.spiel_from_options(o, debug=False) is None
    assert Heathcote.spiel_from_options(o, debug=True) == story.find('actionSpiels', 'cells')[0]
    o.spiel = 'no such spiel'
    assert Heathcote.spiel_from_options(o, debug=True) is None
    o.spiel = 'fear'                                    # a variable's label, not a spiel's
    assert Heathcote.spiel_from_options(o, debug=True) is None


def test_a_silent_run_quits_by_itself():
    assert Heathcote.main(['--exit-after', '0.2']) == 0


if __name__ == '__main__':
    _quiet.run_tests(globals())
