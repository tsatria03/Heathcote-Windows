"""Where things are (heathcote/paths.py), and that every test keeps quiet."""
import _quiet  # noqa: F401  (first, before the game)

import os

from heathcote import paths

CASES = os.path.dirname(os.path.abspath(__file__))


def test_every_test_file_imports_quiet_first():
    for name in sorted(os.listdir(CASES)):
        if not name.endswith('.py') or name.startswith('_'):
            continue
        with open(os.path.join(CASES, name), encoding='utf-8') as f:
            code = [line for line in f if line.strip() and not line.lstrip().startswith(('#', '"""'))
                    and (line.startswith('import') or line.startswith('from'))]
        assert code and code[0].startswith('import _quiet'), '%s does not import _quiet first' % name


def test_the_save_folder_is_the_throwaway_one():
    assert paths.user_dir() == _quiet.FOLDER
    assert paths.logs_dir().startswith(_quiet.FOLDER)


def test_the_game_data_is_found_by_its_bundle():
    assert os.path.isfile(paths.bundle())
    assert os.path.isdir(paths.story_records())
    assert os.path.isdir(paths.audio())


def test_missing_data_stops_with_a_message():
    saved = paths.ROOT, paths.EXE_DIR
    paths.ROOT = paths.EXE_DIR = _quiet.FOLDER
    try:
        paths.game()
    except SystemExit as stop:
        assert 'was not found' in stop.code and paths.BUNDLE_NAME in stop.code
    else:
        raise AssertionError('no SystemExit')
    finally:
        paths.ROOT, paths.EXE_DIR = saved


def test_version_is_read():
    assert paths.version() != 'unknown'


if __name__ == '__main__':
    _quiet.run_tests(globals())
