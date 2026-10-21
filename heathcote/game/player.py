"""Playing the story by the original's rules (aidocks/plans/story_engine_plan.md, section 2).

``StoryPlayer`` drives the audio (platform/audio.py, spiel.py, lanes.py) from the story's
state (game/state.py). The game's story screen and tests/interact/story_check.py both use
it, so they can never play the story differently.

    player = StoryPlayer(audio, story, state, play_sound)
    player.start()          # the spiel labelled "start"
    player.update()         # once a frame

The rules:

* **Timed sets** apply as playback passes each ``at``. After a jump back they fire again on
  the way forward, since the original stores the new position as the last one even then
  (+[Sound tick], 0x100020fdc); a set assigns, so firing twice changes nothing.
* **The lanes** follow the spiel (platform/lanes.py).
* **When a spiel ends,** its ``next`` entries are tried in order and the first that holds
  plays at once, in the same frame, so a fast-forward carries into it. If none holds, the
  scene is over: its idle loop starts, ``lockout`` becomes "0", ``menu-available``
  plays, and the spiel is marked heard (-[PlayState startPlayed], 0x1000336bc).
* **A spiel with no recording,** such as "east wing dispatch", makes no sound and ends at
  once, as the original's stub synthesizer did (+[Sound playSpiel:], 0x100021d4c).
* **The end:** once the variable labelled ``end`` is not "0", the story is over
  (-[Vars setString:to:], 0x100030f48), and ``on_story_end`` is called.

The hooks a screen can set: ``on_spiel(soft)`` as each spiel begins, ``on_scene_end(soft)``
when a scene is over, ``on_story_end()``, and ``on_changed(changes)`` after variables change.
"""
from __future__ import annotations

import logging

from .state import LOCKOUT

log = logging.getLogger('player')

#: The phases of play.
PLAYING, SCENE_END, STORY_END = 'playing', 'scene end', 'story end'


def timed_sets(record):
    """[(at, {variable: value})] of a spiel, in time order; a lone dict applies at once."""
    sets = (record or {}).get('set') or []
    if isinstance(sets, dict):
        return [(0.0, sets)] if sets else []
    out = []
    for entry in sets:
        try:
            out.append((float(entry.get('at', 0)), entry.get('set') or {}))
        except (TypeError, ValueError):
            log.warning('a timed set could not be read: %r', entry)
    return sorted(out, key=lambda item: item[0])


class StoryPlayer:
    def __init__(self, audio, story, state, play_sound=None):
        from ..platform.lanes import Lanes
        self.audio = audio
        self.story = story
        self.state = state
        self.play_sound = play_sound or (lambda label: None)
        self.lanes = Lanes(audio, story)
        self.current = None             # the spiel playing, or the last one played
        self.phase = None
        self.sets = []
        self.last = -1.0                # the position the timed sets last saw
        self.silent = False             # the spiel has no recording
        self.on_spiel = None
        self.on_scene_end = None
        self.on_story_end = None
        self.on_changed = None

    # ---- starting ------------------------------------------------------------
    def start(self):
        """The story from its beginning: the spiel labelled ``start`` (+[Story justStart],
        0x10001a6e0)."""
        soft = self.story.start()
        if soft is None:
            raise SystemExit('The story has no spiel labelled "start", so it cannot begin.')
        self.play(soft)

    def play(self, soft):
        """Begin a spiel from its start."""
        record = self.story.record(soft)
        if record is None:
            log.error('there is no spiel %s', soft)
            return
        self.current = soft
        self.phase = PLAYING
        self.sets = timed_sets(record)
        self.last = -1.0
        self.lanes.begin_spiel(record)
        path = self.story.audio_path(soft)
        self.silent = not (record.get('file') and path)
        log.info('spiel: %s%s', self.story.label(soft), ' (no recording)' if self.silent else '')
        if self.silent:
            self.audio.spiel.stop()
        elif not self.audio.spiel.play(path):
            self.silent = True              # missing on disk: it passes on, as one with no file
        if self.on_spiel:
            self.on_spiel(soft)

    # ---- once a frame ----------------------------------------------------------
    @property
    def position(self):
        return 0.0 if self.silent else self.audio.spiel.position

    def update(self):
        """Follow the spiel: the timed sets and lanes up to its position, then its end."""
        if self.phase != PLAYING:
            if self.phase == SCENE_END:
                self.lanes.update(self.position)
            return
        position = self.position
        self._timed_sets(position)
        if self.phase != PLAYING:
            return                          # a set just ended the story
        self.lanes.update(position)
        if self.silent or self.audio.spiel.ended:
            self._spiel_ended()

    def _timed_sets(self, position):
        changes = []
        for at, sets in self.sets:
            if self.last < at <= position:
                changes += self.state.apply(sets)
        self.last = position                # even after a jump back, as the original
        if changes:
            self.changed(changes)

    def changed(self, changes):
        """Variables changed: tell the screen, and end the story if ``end`` was set."""
        if self.on_changed:
            self.on_changed(changes)
        if self.state.ended and self.phase != STORY_END:
            self.phase = STORY_END
            log.info('the story has ended')
            if self.on_story_end:
                self.on_story_end()

    def _spiel_ended(self):
        following = self.state.next_spiel(self.current)
        if following is not None:
            self.play(following)            # at once, so a fast-forward carries into it
            return
        record = self.story.record(self.current) or {}
        self.phase = SCENE_END
        if record.get('idleLoop'):
            self.lanes.start_idle(record['idleLoop'])
        changes = self.state.set_by_label(LOCKOUT, '0')
        self.state.mark_heard(self.current)
        self.play_sound('menu-available')
        log.info('end of scene: %s', self.story.label(self.current))
        if self.on_scene_end:
            self.on_scene_end(self.current)
        if changes:
            self.changed(changes)

    # ---- what the window shows ------------------------------------------------------
    def transcript(self):
        return ((self.story.record(self.current) or {}).get('transcript') or '').strip()

    def stop(self):
        """Leave the story: the spiel and the idle loop stop, and the lanes fade out."""
        self.audio.spiel.stop()
        self.lanes.stop_all(fade_out=1.0)
        self.phase = None
