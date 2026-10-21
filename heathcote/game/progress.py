"""The story's progress, kept between runs in ``saves/progress.json`` in the save folder
(aidocks/plans/saves_plan.md, section 1).

    {
     "version": 1,
     "started": true,
     "spiel": "<softRef of the spiel the player was in>",
     "chapter": "approaching Heathcote",
     "lanes": {"bgm": "<softRef>", "ambience1": null, ...},
     "state": {"variables": {...}, "heard": [...], "actioned": {...}}
    }

* ``state`` and ``lanes`` are a snapshot taken as ``spiel`` began, so Continue story can
  play that spiel again from its start, its timed sets applying once and its fades lining
  up as they did. A scene's end adds its spiel to the snapshot's heard spiels.
* ``chapter`` is the story variable ``location`` as it is now, written whenever it changes,
  since each scene sets it just after its snapshot is taken.
* Everything is kept by softRef, which never changes, never by label.
* The file is written safely (platform/files.py): a damaged one is set aside and its backup
  read. A save naming spiels, lanes or a version this game does not know is taken as no
  story under way, rather than stopping the game.
"""
from __future__ import annotations

import logging

from .. import paths
from ..platform.files import JsonFile
from ..platform.lanes import LANES
from .storydata import VARIABLE_DEFAULT, StoryData

log = logging.getLogger('progress')

VERSION = 1
ORDER = ['version', 'started', 'spiel', 'chapter', 'lanes', 'state']


def empty():
    """The progress of a story never started."""
    return {'version': VERSION, 'started': False, 'spiel': None, 'chapter': VARIABLE_DEFAULT,
            'lanes': {lane: None for lane in LANES},
            'state': {'variables': {}, 'heard': [], 'actioned': {}}}


class Progress:
    _shared = None

    @classmethod
    def shared(cls):
        if cls._shared is None:
            cls._shared = Progress()
        return cls._shared

    def __init__(self, path=None, story=None):
        self.story = story or StoryData.shared()
        self.file = JsonFile(path or paths.user_path('saves', 'progress.json'), order=ORDER)
        self.data = self._checked(self.file.data)
        if self.data['started']:
            log.info('a story is under way, at %s, in the chapter %s',
                     self.story.label(self.data['spiel']), self.data['chapter'])
        else:
            log.info('no story is under way')
        if self.file.recovered:
            self.write()

    # ---- reading ---------------------------------------------------------------------
    def _checked(self, saved):
        """The save as the game can use it, or an empty one when it cannot."""
        if not saved:
            return empty()
        if saved.get('version') != VERSION:
            log.warning('the progress file is version %r, not %d, so no story is under way',
                        saved.get('version'), VERSION)
            return empty()
        data = empty()
        if not saved.get('started'):
            return data
        spiel = saved.get('spiel')
        if spiel not in set(self.story.refs('actionSpiels')) or self.story.record(spiel) is None:
            log.warning('the progress file names a spiel this story does not have, %r, so no '
                        'story is under way', spiel)
            return data
        data['started'] = True
        data['spiel'] = spiel
        chapter = saved.get('chapter')
        data['chapter'] = chapter if isinstance(chapter, str) and chapter else VARIABLE_DEFAULT
        lanes = saved.get('lanes') if isinstance(saved.get('lanes'), dict) else {}
        for lane in LANES:
            soft = lanes.get(lane)
            # A lane naming a recording the story does not have starts silent.
            data['lanes'][lane] = soft if isinstance(soft, str) and self.story.record(soft) else None
        state = saved.get('state') if isinstance(saved.get('state'), dict) else {}
        data['state'] = {'variables': state.get('variables') if isinstance(state.get('variables'), dict) else {},
                         'heard': [s for s in state.get('heard') or [] if isinstance(s, str)],
                         'actioned': {a: n for a, n in (state.get('actioned') or {}).items()
                                      if isinstance(n, int) and not isinstance(n, bool) and n > 0}
                         if isinstance(state.get('actioned'), dict) else {}}
        return data

    @property
    def under_way(self):
        """Whether a story was started and not finished or restarted, so Continue story is
        offered."""
        return bool(self.data['started'])

    @property
    def spiel(self):
        return self.data['spiel']

    @property
    def chapter(self):
        return self.data['chapter']

    @property
    def lanes(self):
        return dict(self.data['lanes'])

    @property
    def state(self):
        """The snapshot, for ``StoryState.restore()``."""
        return self.data['state']

    # ---- writing ---------------------------------------------------------------------
    def write(self):
        self.file.data = self.data
        return self.file.write()

    def begin(self, spiel, state, lanes):
        """A spiel begins: it is where Continue story picks up, with the state and the
        lanes as they are now."""
        self.data['started'] = True
        self.data['spiel'] = spiel
        self.data['state'] = state.snapshot()
        self.data['lanes'] = {lane: (lanes or {}).get(lane) for lane in LANES}
        self.write()

    def mark_heard(self, spiel):
        """A scene ended, so its spiel was heard to its end, and may be interrupted when
        Continue story plays it again."""
        if not self.data['started']:
            return
        heard = self.data['state'].setdefault('heard', [])
        if spiel not in heard:
            heard.append(spiel)
            heard.sort()
            self.write()

    def set_chapter(self, chapter):
        """The story's ``location`` changed: the chapter Continue story names."""
        chapter = chapter or VARIABLE_DEFAULT
        if chapter != self.data['chapter']:
            self.data['chapter'] = chapter
            if self.data['started']:
                self.write()

    def clear(self):
        """No story under way: Restart story, or leaving the end credits."""
        self.data = empty()
        self.write()
