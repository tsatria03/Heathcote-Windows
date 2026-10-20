"""The four background lanes, music and three ambiences, following each spiel's timed
events, and the idle loop (aidocks/plans/audio_plan.md, section 3).

A spiel lists events for each lane, such as

    "ambience1": [{"at": 0.1, "fadeTo": {"softRef": "...", "duration": 2}}]

Each fires when the spiel's playback passes its ``at`` time (+[Sound tick], 0x1000208a8):

* ``fadeTo`` crossfades the lane to that recording over ``duration`` seconds, and loops
  it (playFilePath:toFadeInWithDuration:). The old recording fades out on its own channel
  as the new one fades in. A lane already playing that recording carries on.
* ``fadeOut`` fades the lane out over ``duration`` seconds and stops it.

The lanes carry on from spiel to spiel: a lane changes only when an event says so. The
plain ``ambience`` lane is never played, as in the original, which never reads it.

After a jump backwards, each lane is set up again from what it held when the spiel opened,
with its events replayed up to the new position, so the right recording plays there; one
caught part way through a crossfade picks the crossfade up part way
(coldConfigureWithFromFilePath:toFilePath:fadeDuration:fadeProgress:).

When the story opens, the lanes held when the resumed spiel began start again, each
fading in over 0.5 seconds (+[StoryView go], 0x100025ce8).

The idle loop starts, with no fade, when a spiel ends with nothing to follow, and stops
when the next spiel begins (+[Sound playSpiel:], 0x100021af0) or a rewind replays the
ended spiel.

What each lane holds is kept by softRef, as the saves keep it (aidocks/plans/saves_plan.md).
"""
from __future__ import annotations

import logging

log = logging.getLogger('lanes')

LANES = ('bgm', 'ambience1', 'ambience2', 'ambience3')
OPEN_FADE = 0.5
#: How far back the position must move to count as a jump back, not jitter.
JUMP_BACK = 0.05


def lane_events(record):
    """{lane: [(at, softRef or None, duration)]} for a spiel's four lanes, in time order;
    a softRef of None is a fade out."""
    out = {}
    for lane in LANES:
        events = []
        for e in (record or {}).get(lane) or []:
            try:
                at = float(e.get('at', 0))
                if 'fadeTo' in e:
                    events.append((at, e['fadeTo']['softRef'], float(e['fadeTo'].get('duration', 0))))
                elif 'fadeOut' in e:
                    events.append((at, None, float(e['fadeOut'].get('duration', 0))))
            except (TypeError, ValueError, KeyError):
                log.warning('a %s event could not be read: %r', lane, e)
        out[lane] = sorted(events, key=lambda ev: ev[0])
    return out


class Lanes:
    """The four lanes and the idle loop, for a story whose data ``story`` gives each
    softRef's recording (heathcote/game/storydata.py)."""

    def __init__(self, audio, story):
        self.audio = audio
        self.story = story
        self.holding = {lane: None for lane in LANES}   # the softRef each lane holds now
        self.opening = dict(self.holding)               # what each held as the spiel began
        self.events = {lane: [] for lane in LANES}
        self.last = -1.0                                # the position last followed
        self.idle = None                                # the idle loop's softRef, while it plays

    def _path(self, soft):
        return self.story.audio_path(soft) if soft else None

    # ---- following a spiel -------------------------------------------------------
    def begin_spiel(self, record):
        """A spiel begins: remember what the lanes hold, take its events, and stop the idle
        loop."""
        self.stop_idle()
        self.opening = dict(self.holding)
        self.events = lane_events(record)
        self.last = -1.0

    def update(self, position):
        """Called once a frame with the spiel's position: fire the events passed, or set the
        lanes up again after a jump back."""
        if position < self.last - JUMP_BACK:
            self.rebuild(position)
            return
        for lane, events in self.events.items():
            for at, soft, duration in events:
                if self.last < at <= position:
                    self._fire(lane, soft, duration)
        self.last = max(self.last, position)

    def _fire(self, lane, soft, duration):
        slot = self.audio.slot(lane)
        self.holding[lane] = soft
        if soft is None:
            slot.stop(fade_out=duration)
            return
        path = self._path(soft)
        if path is None:
            log.warning('%s has no recording to fade to (%s)', lane, soft)
            return
        if slot.playing and slot.path == path:
            return                          # already playing it: it carries on
        slot.stop(fade_out=duration)
        slot.play(path, fade_in=duration)

    # ---- after a jump back -----------------------------------------------------------
    def state_at(self, lane, position):
        """(what the lane holds at ``position``, and the crossfade under way there, as
        (from softRef, to softRef, progress 0 to 1, seconds left), or None)."""
        holding = self.opening[lane]
        fading = None
        for at, soft, duration in self.events[lane]:
            if at > position:
                break
            before, holding = holding, soft
            if duration > 0 and position < at + duration:
                fading = (before, soft, (position - at) / duration, at + duration - position)
            else:
                fading = None
        return holding, fading

    def rebuild(self, position):
        """Set every lane up again for ``position``, from what it held as the spiel began."""
        for lane in LANES:
            holding, fading = self.state_at(lane, position)
            slot = self.audio.slot(lane)
            self.holding[lane] = holding
            if fading is not None:
                before, after, progress, left = fading
                slot.stop()
                if before is not None and self._path(before):
                    slot.play_fading_out(self._path(before), 1.0 - progress, left)
                if after is not None and self._path(after):
                    slot.play(self._path(after), fade_in=left, start_level=progress)
            elif holding is None:
                slot.stop()
            elif not (slot.playing and slot.path == self._path(holding)):
                slot.stop()
                slot.play(self._path(holding))
        self.last = position

    # ---- opening the story -----------------------------------------------------------
    def restore(self, held):
        """The story opens: start what each lane held as the resumed spiel began, fading in
        over 0.5 seconds. ``held`` is {lane: softRef or None}, as the saves keep it."""
        for lane in LANES:
            soft = (held or {}).get(lane)
            self.holding[lane] = soft
            slot = self.audio.slot(lane)
            slot.stop()
            if soft and self._path(soft):
                slot.play(self._path(soft), fade_in=OPEN_FADE)
        self.opening = dict(self.holding)

    def stop_all(self, fade_out=0.0):
        for lane in LANES:
            self.audio.slot(lane).stop(fade_out=fade_out)
            self.holding[lane] = None
        self.stop_idle()

    # ---- the idle loop -----------------------------------------------------------
    def start_idle(self, soft):
        """The spiel ended with nothing to follow: its idle loop, with no fade."""
        path = self._path(soft)
        if path is None:
            return
        self.audio.slot('idleLoop').play(path)
        self.idle = soft

    def stop_idle(self):
        if self.idle is not None or self.audio.slot('idleLoop').playing:
            self.audio.slot('idleLoop').stop()
        self.idle = None
