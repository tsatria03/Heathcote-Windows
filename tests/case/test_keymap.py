"""The key map (heathcote/platform/keymap.py): the agreed keys, their groups and clashes,
and the keys file."""
import _quiet  # noqa: F401  (first, before the game)

import json
import os

from heathcote.platform.keymap import (ACTION_IDS, DEFAULTS, GROUPS, MASTER_VOLUME, MENU, STORY,
                                       STORY_VOLUMES, TITLE_VOLUME, KeyMap, binding, binding_text,
                                       clashes)

N = [0]


def fresh():
    N[0] += 1
    return KeyMap(os.path.join(_quiet.FOLDER, 'keys%d' % N[0], 'keys.json'))


def test_the_agreed_default_keys():
    km = fresh()
    expect = {
        (MENU, 'up'): 'menu_previous', (MENU, 'left'): 'menu_previous',
        (MENU, 'down'): 'menu_next', (MENU, 'right'): 'menu_next',
        (MENU, 'home'): 'menu_first', (MENU, 'end'): 'menu_last',
        (MENU, 'return'): 'menu_choose', (MENU, 'escape'): 'menu_back',
        (MENU, 'space'): None,                      # no longer the choice's text
        (STORY, 'up'): 'actions_menu', (STORY, 'return'): 'actions_menu',
        (STORY, 'left'): 'rewind', (STORY, 'right'): 'fast_forward',
        (STORY, 'escape'): 'pause', (STORY, 'tab'): 'where',
        (MASTER_VOLUME, 'shift+home'): 'master_up', (MASTER_VOLUME, 'shift+end'): 'master_down',
        (STORY_VOLUMES, 'page up'): 'backgrounds_up', (STORY_VOLUMES, 'page down'): 'backgrounds_down',
        (STORY_VOLUMES, 'shift+page up'): 'interface_up',
        (STORY_VOLUMES, 'shift+page down'): 'interface_down',
        (TITLE_VOLUME, 'page up'): 'title_up', (TITLE_VOLUME, 'page down'): 'title_down',
    }
    for (group, b), action in expect.items():
        key = b.split('+')[-1]
        mods = b.split('+')[:-1]
        assert km.action_for(key, mods, group) == action, (group, b)


def test_a_saved_action_the_game_no_longer_has_is_dropped():
    import json
    km = fresh()
    km.file.data['choice_text'] = ['space']             # as an older keys.json held it
    km.file.write()
    again = KeyMap(km.file.path)
    with open(km.file.path, encoding='utf-8') as f:
        assert 'choice_text' not in json.load(f)
    assert again.action_for('space', [], MENU) is None


def test_modifiers_must_match_exactly():
    km = fresh()
    assert km.action_for('home', [], MASTER_VOLUME) is None
    assert km.action_for('home', ['shift', 'ctrl'], MASTER_VOLUME) is None
    assert km.action_for('page up', ['shift'], TITLE_VOLUME) is None


def test_debug_keys_only_in_debug_mode():
    km = fresh()
    assert km.action_for('f2', [], STORY) is None
    assert 'debug_skip' not in km.actions
    km.debug = True
    assert km.action_for('f2', [], STORY) == 'debug_skip'
    assert km.action_for('f4', [], STORY) == 'debug_variables'


def test_no_default_clashes():
    for a in ACTION_IDS:
        for b in ACTION_IDS:
            if a < b and clashes(GROUPS[a], GROUPS[b]):
                shared = set(DEFAULTS[a]) & set(DEFAULTS[b])
                assert not shared, '%s and %s share %s' % (a, b, shared)


def test_which_groups_clash():
    assert clashes(MENU, MENU)
    assert not clashes(MENU, STORY)
    assert clashes(MASTER_VOLUME, MENU) and clashes(MASTER_VOLUME, STORY)
    assert clashes(MASTER_VOLUME, TITLE_VOLUME) and clashes(MASTER_VOLUME, STORY_VOLUMES)
    assert clashes(STORY_VOLUMES, STORY) and clashes(STORY_VOLUMES, MENU)
    assert clashes(TITLE_VOLUME, MENU)
    assert not clashes(TITLE_VOLUME, STORY_VOLUMES) and not clashes(TITLE_VOLUME, STORY)


def test_a_rebind_takes_the_key_only_from_what_clashes():
    km = fresh()
    km.set_binding('rewind', 'up')            # the story's Up; the menu keeps its own
    assert km.bindings['rewind'] == ['up']
    assert 'up' not in km.bindings['actions_menu']
    assert 'up' in km.bindings['menu_previous']
    km.set_binding('menu_first', 'shift+home')
    assert km.bindings['master_up'] == []


def test_add_and_clear():
    km = fresh()
    km.set_binding('where', 'w', replace=False)
    assert km.bindings['where'] == ['tab', 'w']
    km.set_binding('where', 'w', replace=False)
    assert km.bindings['where'] == ['tab', 'w']
    km.clear('where')
    assert km.bindings['where'] == [] and km.keys_text('where') == 'nothing'


def test_the_file_is_written_and_read_back():
    km = fresh()
    km.set_binding('pause', 'p')
    again = KeyMap(km.file.path)
    assert again.bindings['pause'] == ['p']
    km.reset()
    assert KeyMap(km.file.path).bindings == DEFAULTS


def test_an_old_file_gains_new_actions_and_drops_bad_entries():
    km = fresh()
    os.makedirs(os.path.dirname(km.file.path), exist_ok=True)
    with open(km.file.path, 'w', encoding='utf-8') as f:
        json.dump({'master_up': ['shift+home'], 'rewind': ['a', 7, '', 'shift+'], 'gone': ['x']}, f)
    km = KeyMap(km.file.path)
    assert km.bindings['title_up'] == ['page up']
    assert km.bindings['rewind'] == ['a']


def test_keys_are_spoken_in_full():
    assert binding('page up', ['shift']) == 'shift+page up'
    assert binding('home', ['alt', 'shift']) == 'shift+alt+home'
    assert binding_text('shift+page up') == 'Shift plus Page Up'
    assert fresh().keys_text('menu_choose') == 'Enter, or Keypad Enter'


if __name__ == '__main__':
    _quiet.run_tests(globals())
