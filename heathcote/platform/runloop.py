"""Delayed and repeating calls, run from the main loop once a frame.

Everything timed in the game goes through here: a spiel's timed variable sets, the
lockout's grace, the reminders and the fades (aidocks/plans/foundation_plan.md).

    loop = RunLoop.main()
    call = loop.after(12.5, story.set_variable, 'lights', '1')     # once, in 12.5 seconds
    tick = loop.every(1.0, window.redraw)                           # every second until cancelled
    call.cancel()

Delays are wall-clock, read from ``clock`` (``time.perf_counter``, not ``time.monotonic``,
whose 15.6 ms steps on Windows would round short delays). A slow frame makes calls late,
never bunched: everything due runs in order of when it was due, the earlier scheduled first
when two fall due together, and a repeating call that missed beats skips them rather than
catching up.

``hold()`` stops the clock, for a pause or the F1 screen, and ``resume()`` moves every
waiting call on by the time held, so a timed set still comes at the same point in its spiel.
A call made during a hold counts its delay from the moment the clock stopped, so it too
waits its full delay once the clock starts again.

An error inside a call is logged and the loop carries on; the call never runs twice.
"""
from __future__ import annotations

import heapq
import itertools
import logging
import time

log = logging.getLogger('runloop')

#: The loop's clock, in seconds.
clock = time.perf_counter


class Call:
    """One waiting call. ``cancel()`` stops it, before or between its runs."""

    __slots__ = ('due', 'interval', 'fn', 'args', 'seq', 'cancelled')

    def __init__(self, due, interval, fn, args, seq):
        self.due = due
        self.interval = interval        # None for a call that runs once
        self.fn = fn
        self.args = args
        self.seq = seq
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    @property
    def active(self):
        return not self.cancelled

    def __lt__(self, other):
        return (self.due, self.seq) < (other.due, other.seq)


class RunLoop:
    _instance = None

    @classmethod
    def main(cls):
        if cls._instance is None:
            cls._instance = RunLoop()
        return cls._instance

    def __init__(self):
        self._calls = []                # heap of Call
        self._seq = itertools.count()
        self._held_at = None            # when hold() stopped the clock

    def _now(self):
        """The loop's own time: while held, the moment the clock stopped, so a call made
        during a hold waits its full delay after ``resume``."""
        return self._held_at if self._held_at is not None else clock()

    def after(self, delay, fn, *args):
        """Run ``fn(*args)`` once, ``delay`` seconds from now."""
        call = Call(self._now() + max(0.0, float(delay)), None, fn, args, next(self._seq))
        heapq.heappush(self._calls, call)
        return call

    def every(self, interval, fn, *args):
        """Run ``fn(*args)`` every ``interval`` seconds, the first time ``interval`` from now."""
        interval = float(interval)
        if interval <= 0:
            raise ValueError('a repeating call needs an interval above 0')
        call = Call(self._now() + interval, interval, fn, args, next(self._seq))
        heapq.heappush(self._calls, call)
        return call

    def pump(self, now=None):
        """Run everything due, earliest first. Called once a frame by the main loop."""
        if self._held_at is not None:
            return
        now = clock() if now is None else now
        while self._calls:
            call = self._calls[0]
            if call.cancelled:
                heapq.heappop(self._calls)
                continue
            if call.due > now:
                break
            heapq.heappop(self._calls)
            try:
                call.fn(*call.args)
            except Exception:
                log.exception('call %s', getattr(call.fn, '__qualname__', call.fn))
            if call.interval is not None and not call.cancelled:
                call.due += call.interval
                if call.due <= now:
                    call.due = now + call.interval      # skip missed beats
                call.seq = next(self._seq)
                heapq.heappush(self._calls, call)
            else:
                call.cancelled = True

    def hold(self):
        """Stop the clock: nothing runs until ``resume``."""
        if self._held_at is None:
            self._held_at = clock()

    def resume(self):
        """Start the clock again, moving every waiting call on by the time held."""
        if self._held_at is None:
            return
        gap = clock() - self._held_at
        self._held_at = None
        for call in self._calls:
            call.due += gap
        heapq.heapify(self._calls)

    @property
    def held(self):
        return self._held_at is not None

    def remaining(self, call, now=None):
        """Seconds until ``call`` is due, counting a hold as time that has not passed."""
        if call.cancelled:
            return 0.0
        now = self._held_at if self._held_at is not None else (clock() if now is None else now)
        return max(0.0, call.due - now)

    def reset(self):
        self._held_at = None
        self._calls.clear()
