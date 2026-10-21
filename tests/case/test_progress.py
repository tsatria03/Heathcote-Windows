"""The story's progress between runs (heathcote/game/progress.py), in a throwaway save."""
import _quiet  # noqa: F401  (first, before the game)

import json
import os

from heathcote.game.progress import VERSION, Progress
from heathcote.game.state import StoryState
from heathcote.game.storydata import StoryData

STORY = StoryData.shared()
N = [0]


def path():
    N[0] += 1
    return os.path.join(_quiet.FOLDER, 'progress%d' % N[0], 'progress.json')


def spiel(label):
    return STORY.find('actionSpiels', label)[0]


def a_lane_recording():
    return STORY.refs('bgm')[0]


def test_a_new_save_has_no_story_under_way_and_writes_nothing():
    p = path()
    progress = Progress(p)
    assert not progress.under_way and progress.spiel is None
    assert not os.path.exists(p)


def test_a_spiel_beginning_is_written_and_read_back():
    p = path()
    state = StoryState(STORY)
    state.set_by_label('fear', 'clowns')
    state.mark_heard(spiel('start'))
    bgm = a_lane_recording()
    Progress(p).begin(spiel('cells'), state, {'bgm': bgm, 'ambience1': None})
    again = Progress(p)
    assert again.under_way and again.spiel == spiel('cells')
    assert again.lanes == {'bgm': bgm, 'ambience1': None, 'ambience2': None, 'ambience3': None}
    restored = StoryState(STORY)
    restored.restore(again.state)
    assert restored.get_by_label('fear') == 'clowns' and restored.is_heard(spiel('start'))


def test_the_snapshot_is_taken_as_the_spiel_begins_and_later_changes_do_not_reach_it():
    p = path()
    state = StoryState(STORY)
    progress = Progress(p)
    progress.begin(spiel('cells'), state, {})
    state.set_by_label('fear', 'spiders')               # a timed set after the snapshot
    assert Progress(p).state['variables'][state.variable('fear')] == '0'


def test_the_chapter_is_kept_apart_and_written_as_it_changes():
    p = path()
    progress = Progress(p)
    progress.set_chapter('working late')                # before any story: not written
    assert not os.path.exists(p)
    progress.begin(spiel('start'), StoryState(STORY), {})
    progress.set_chapter('approaching Heathcote')
    assert Progress(p).chapter == 'approaching Heathcote'


def test_a_scene_heard_to_its_end_is_added_to_the_snapshot():
    p = path()
    progress = Progress(p)
    progress.begin(spiel('cells'), StoryState(STORY), {})
    progress.mark_heard(spiel('cells'))
    assert spiel('cells') in Progress(p).state['heard']


def test_clear_leaves_no_story_under_way():
    p = path()
    progress = Progress(p)
    progress.begin(spiel('cells'), StoryState(STORY), {})
    progress.clear()
    assert not Progress(p).under_way


def test_a_damaged_save_is_set_aside_and_its_backup_read():
    p = path()
    progress = Progress(p)
    progress.begin(spiel('start'), StoryState(STORY), {})
    progress.begin(spiel('cells'), StoryState(STORY), {})   # the backup now holds start
    with open(p, 'w', encoding='utf-8') as f:
        f.write('{ not json')
    again = Progress(p)
    assert os.path.exists(p + '.damaged')
    assert again.under_way and again.spiel == spiel('start')
    with open(p, encoding='utf-8') as f:                    # written back from the backup
        assert json.load(f)['spiel'] == spiel('start')


def test_a_save_this_game_cannot_use_is_no_story_under_way():
    for saved in ({'version': VERSION + 1, 'started': True, 'spiel': spiel('cells')},
                  {'version': VERSION, 'started': True, 'spiel': 'not a spiel'},
                  {'version': VERSION, 'started': 'yes'}):
        p = path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(saved, f)
        assert not Progress(p).under_way, saved


def test_unknown_lanes_start_silent_and_bad_counts_are_dropped():
    p = path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    action = STORY.refs('actions')[0]
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'version': VERSION, 'started': True, 'spiel': spiel('cells'),
                   'lanes': {'bgm': 'gone', 'ambience1': 7},
                   'state': {'actioned': {action: 2, 'x': 'two', 'y': True}, 'heard': [3, 'z']}}, f)
    progress = Progress(p)
    assert progress.under_way and progress.lanes['bgm'] is None and progress.lanes['ambience1'] is None
    assert progress.state['actioned'] == {action: 2} and progress.state['heard'] == ['z']
    restored = StoryState(STORY)
    restored.restore(progress.state)                      # 'z' is no spiel, so it is dropped
    assert restored.count(action) == 2 and not restored.heard


def test_the_file_is_written_in_its_order():
    p = path()
    Progress(p).begin(spiel('start'), StoryState(STORY), {})
    with open(p, encoding='utf-8') as f:
        assert list(json.load(f)) == ['version', 'started', 'spiel', 'chapter', 'lanes', 'state']


if __name__ == '__main__':
    _quiet.run_tests(globals())
