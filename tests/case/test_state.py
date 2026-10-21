"""The story's state (heathcote/game/state.py): the variables, heard spiels and action
counts, conditions, next, the actions on offer, and snapshots, on the real story data."""
import _quiet  # noqa: F401  (first, before the game)

from heathcote.game.state import StoryState
from heathcote.game.storydata import StoryData

STORY = StoryData.shared()


def fresh():
    return StoryState(STORY)


def var(label):
    return STORY.find('variables', label)[0]


def test_every_variable_starts_as_text_zero():
    s = fresh()
    assert len(s.variables) == len(STORY.refs('variables')) == 23
    assert set(s.variables.values()) == {'0'}
    assert not s.ended and not s.locked_out and s.non_default() == []


def test_conditions_match_exactly_as_text():
    s = fresh()
    fear = var('fear')
    assert s.holds({}) and s.holds({fear: '0'}) and s.holds({fear: 0})
    s.apply({fear: 'clowns'})
    assert s.holds({fear: 'clowns'})
    assert not s.holds({fear: 'Clowns'}) and not s.holds({fear: 'clowns '})
    s.apply({fear: '1'})
    assert not s.holds({fear: '01'})                    # text, not numbers


def test_every_listed_variable_must_hold():
    s = fresh()
    s.apply({var('rats'): '1'})
    assert not s.holds({var('rats'): '1', var('smoke'): '1'})
    s.apply({var('smoke'): '1'})
    assert s.holds({var('rats'): '1', var('smoke'): '1'})


def test_apply_reports_only_what_changed():
    s = fresh()
    assert s.apply({var('fear'): 'clowns', var('rats'): '0'}) == [(var('fear'), '0', 'clowns')]
    assert s.apply({var('fear'): 'clowns'}) == []


def test_the_end_and_lockout_go_by_their_labels():
    s = fresh()
    s.set_by_label('lockout', '1')
    assert s.locked_out
    s.set_by_label('end', 'clowns')
    assert s.ended
    assert ('end', 'clowns') in s.non_default() and ('lockout', '1') in s.non_default()


def test_next_takes_the_first_entry_that_holds():
    s = fresh()
    dispatch = STORY.find('actionSpiels', 'east wing dispatch')[0]
    entries = STORY.record(dispatch)['next']
    first_free = next((e for e in entries if s.holds(e.get('if'))), None)
    assert s.next_spiel(dispatch) == (first_free or {}).get('softRef')
    start = STORY.start()
    assert s.next_spiel(start) is None or s.next_spiel(start) in STORY.refs('actionSpiels')


def test_the_actions_on_offer_hold_their_conditions_in_order():
    s = fresh()
    offered = s.offered()
    assert offered, 'nothing is offered at the start'
    orders = [STORY.record(a).get('order', 0) for a in offered]
    assert orders == sorted(orders)
    for a in offered:
        assert s.holds(STORY.record(a).get('if'))
    for a in set(STORY.refs('actions')) - set(offered):
        assert not s.holds(STORY.record(a).get('if')) or s.burnt(a)


def test_no_action_in_the_story_sets_anything():
    # Every variable changes through spiels' timed sets; the actions' own set is empty.
    assert all(not STORY.record(a).get('set') for a in STORY.refs('actions'))


def test_choosing_plays_its_spiel_counts_and_applies_its_set():
    s = fresh()
    action = s.offered()[0]
    rec = STORY.record(action)
    spiel, changed = s.choose(action)
    assert spiel == rec['actionSpiels'][0] and s.count(action) == 1 and changed == []
    spiel, _changed = s.choose(action)                  # chosen again: its count goes on
    assert spiel == rec['actionSpiels'][0] and s.count(action) == 2
    # The rule still applies a set, as the original does, should the data ever have one.
    fear = var('fear')
    fake = {'actionSpiels': ['x'], 'set': {fear: 'clowns'}}
    STORY.records['__test__'] = fake
    STORY.assets['actions']['__fake__'] = '__test__'
    STORY.category['__fake__'] = 'actions'
    try:
        assert s.choose('__fake__') == ('x', [(fear, '0', 'clowns')])
    finally:
        del STORY.records['__test__'], STORY.assets['actions']['__fake__'], STORY.category['__fake__']


def test_burn_after_reading_goes_once_chosen():
    s = fresh()
    burner = next(a for a in STORY.refs('actions') if STORY.record(a).get('burnAfterReading'))
    s.apply(STORY.record(burner).get('if'))             # make it offered
    assert burner in s.offered()
    s.choose(burner)
    assert s.burnt(burner) and burner not in s.offered()
    plain = next(a for a in STORY.refs('actions') if not STORY.record(a).get('burnAfterReading'))
    s.apply(STORY.record(plain).get('if'))
    s.choose(plain)
    s.apply(STORY.record(plain).get('if'))
    assert not s.burnt(plain) and plain in s.offered()


def test_heard_spiels():
    s = fresh()
    start = STORY.start()
    assert not s.is_heard(start)
    s.mark_heard(start)
    assert s.is_heard(start)


def test_a_snapshot_is_a_copy_and_restores_everything():
    s = fresh()
    s.apply({var('fear'): 'clowns'})
    s.mark_heard(STORY.start())
    action = s.offered()[0]
    s.choose(action)
    snap = s.snapshot()
    s.apply({var('fear'): 'spiders'})
    s.mark_heard(STORY.refs('actionSpiels')[5])
    s.choose(action)
    assert snap['variables'][var('fear')] == 'clowns'   # untouched by later changes
    s.restore(snap)
    assert s.get(var('fear')) == 'clowns' and s.heard == {STORY.start()}
    assert s.actioned == {action: 1}


def test_restore_drops_what_the_story_does_not_know():
    s = fresh()
    s.restore({'variables': {var('fear'): 3, 'nonsense': 'x'}, 'heard': ['nope', STORY.start()],
               'actioned': {'gone': 2, STORY.refs('actions')[0]: 0}})
    assert s.get(var('fear')) == '3' and 'nonsense' not in s.variables
    assert s.heard == {STORY.start()} and s.actioned == {}


def test_reset_starts_again():
    s = fresh()
    s.apply({var('fear'): 'clowns'})
    s.mark_heard(STORY.start())
    s.choose(s.offered()[0])
    s.reset()
    assert set(s.variables.values()) == {'0'} and not s.heard and not s.actioned


if __name__ == '__main__':
    _quiet.run_tests(globals())
