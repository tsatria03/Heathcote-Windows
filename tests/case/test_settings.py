"""The safe JSON files (heathcote/platform/files.py) and the settings
(heathcote/platform/settings.py)."""
import _quiet  # noqa: F401  (first, before the game)

import json
import os

from heathcote.platform.files import JsonFile
from heathcote.platform.settings import DEFAULTS, Settings

N = [0]


def new_path():
    N[0] += 1
    return os.path.join(_quiet.FOLDER, 'case%d' % N[0], 'settings.json')


def read(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def test_every_setting_is_written_on_the_first_start():
    path = new_path()
    Settings(path)
    assert read(path) == DEFAULTS
    assert list(read(path)) == list(DEFAULTS)     # in the defaults' order


def test_a_change_is_written_at_once_with_a_backup():
    path = new_path()
    s = Settings(path)
    s.set('debug', True)
    assert read(path)['debug'] is True
    assert read(path + '.bak')['debug'] is False


def test_a_damaged_file_is_kept_aside_and_the_backup_read():
    path = new_path()
    s = Settings(path)
    s.set('title_volume', 50)
    s.set('master_volume', 70)                    # the backup now has title 50, master 100
    with open(path, 'w') as f:
        f.write('{not json')
    s = Settings(path)
    assert s.get('title_volume') == 50 and s.get('master_volume') == 100
    assert os.path.exists(path + '.damaged')
    assert read(path)['title_volume'] == 50       # written back at once


def test_a_damaged_file_with_no_backup_gets_the_defaults():
    path = new_path()
    os.makedirs(os.path.dirname(path))
    with open(path, 'w') as f:
        f.write('[1, 2')
    Settings(path)
    assert read(path) == DEFAULTS


def test_bad_values_are_put_back_and_unknown_ones_kept():
    path = new_path()
    os.makedirs(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8-sig') as f:   # Notepad's byte order mark
        json.dump({'master_volume': 55, 'debug': 'yes', 'title_volume': 30, 'later': 1}, f)
    s = Settings(path)
    assert s.get('master_volume') == 100 and s.get('debug') is False
    assert s.get('title_volume') == 30
    assert read(path)['later'] == 1


def test_set_refuses_what_it_cannot_use():
    s = Settings(new_path())
    for key, value in (('master_volume', 101), ('master_volume', 45), ('debug', 1)):
        try:
            s.set(key, value)
        except ValueError:
            continue
        raise AssertionError('%s took %r' % (key, value))
    try:
        s.set('no_such_setting', 1)
    except KeyError:
        return
    raise AssertionError('an unknown setting was taken')


def test_volumes_step_by_ten_within_0_and_100():
    s = Settings(new_path())
    assert s.step_volume('master_volume', 1) == 100
    assert s.step_volume('master_volume', -1) == 90
    for _ in range(12):
        s.step_volume('interface_volume', -1)
    assert s.get('interface_volume') == 0


def test_toggle():
    s = Settings(new_path())
    assert s.toggle('first_run_notice_shown') is True
    assert s.get('first_run_notice_shown') is True


def test_json_file_writes_keys_in_order():
    path = new_path()
    f = JsonFile(path, order=['b', 'a'])
    f.data = {'a': 1, 'z': 3, 'b': 2}
    assert f.write()
    assert list(read(path)) == ['b', 'a', 'z']


if __name__ == '__main__':
    _quiet.run_tests(globals())
