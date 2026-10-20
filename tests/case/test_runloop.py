"""The timer loop (heathcote/platform/runloop.py), on a clock the tests move by hand."""
import _quiet  # noqa: F401  (first, before the game)

from heathcote.platform import runloop
from heathcote.platform.runloop import RunLoop

NOW = [0.0]
runloop.clock = lambda: NOW[0]


def fresh():
    NOW[0] = 0.0
    return RunLoop(), []


def test_calls_run_in_order_of_when_they_are_due():
    loop, out = fresh()
    loop.after(2, out.append, 'b')
    loop.after(1, out.append, 'a')
    loop.after(2, out.append, 'c')         # due with b, scheduled after it
    NOW[0] = 2.0
    loop.pump()
    assert out == ['a', 'b', 'c'], out


def test_nothing_runs_early():
    loop, out = fresh()
    loop.after(1, out.append, 'a')
    NOW[0] = 0.99
    loop.pump()
    assert out == []


def test_a_repeat_skips_missed_beats():
    loop, out = fresh()
    loop.every(1, out.append, 'r')
    NOW[0] = 3.5
    loop.pump()
    assert out == ['r'], out               # late, not bunched
    NOW[0] = 4.4
    loop.pump()
    assert out == ['r'], out
    NOW[0] = 4.5
    loop.pump()
    assert out == ['r', 'r'], out


def test_cancel():
    loop, out = fresh()
    call = loop.after(1, out.append, 'a')
    rep = loop.every(1, out.append, 'r')
    call.cancel()
    NOW[0] = 1.0
    loop.pump()
    rep.cancel()
    NOW[0] = 5.0
    loop.pump()
    assert out == ['r'], out
    assert not call.active


def test_an_error_is_logged_and_the_loop_carries_on():
    loop, out = fresh()
    loop.after(1, lambda: 1 / 0)
    loop.after(1, out.append, 'after')
    NOW[0] = 1.0
    loop.pump()
    assert out == ['after']


def test_hold_and_resume_keep_each_call_its_time():
    loop, out = fresh()
    call = loop.after(3, out.append, 'a')
    NOW[0] = 1.0
    loop.hold()
    NOW[0] = 10.0
    loop.pump()
    assert out == [] and loop.held
    assert loop.remaining(call) == 2.0
    loop.resume()
    assert loop.remaining(call) == 2.0
    NOW[0] = 12.0
    loop.pump()
    assert out == ['a']


def test_a_call_made_during_a_hold_waits_its_full_delay():
    loop, out = fresh()
    loop.hold()
    NOW[0] = 5.0
    call = loop.after(1, out.append, 'a')
    rep = loop.every(2, out.append, 'r')
    assert loop.remaining(call) == 1.0 and loop.remaining(rep) == 2.0
    NOW[0] = 9.0
    loop.resume()
    NOW[0] = 9.99
    loop.pump()
    assert out == []
    NOW[0] = 10.0
    loop.pump()
    assert out == ['a'], out
    NOW[0] = 11.0
    loop.pump()
    assert out == ['a', 'r'], out


def test_a_repeat_needs_an_interval():
    loop, _out = fresh()
    try:
        loop.every(0, print)
    except ValueError:
        return
    raise AssertionError('no ValueError')


if __name__ == '__main__':
    _quiet.run_tests(globals())
