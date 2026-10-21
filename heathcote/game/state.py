"""What the story remembers while it is played (aidocks/plans/story_engine_plan.md,
section 1), kept in memory; the saves plan writes it to disk
(aidocks/plans/saves_plan.md).

Three stores, as the original's (aidocks/general/project_original_behaviour.md):

* **story:** every story variable, as text. Each starts as "0"
  (+[Vars createStoryDefaults], 0x1000321e4), and a condition holds only when every
  variable it names equals its value exactly, as text.
* **heard:** the spiels heard to their end. Only a spiel that ends with nothing to follow
  is marked heard (-[PlayState startPlayed], 0x100033704), never one passed through by
  ``next``.
* **actioned:** how many times each action has been chosen.

Everything is kept by softRef, never by label: labels are not always unique, and the ids
never change. What the four background lanes hold is not here but in
platform/lanes.py's ``Lanes``.

``snapshot()`` copies all of it as one, and ``restore()`` puts it back, for Continue story's
replay of a spiel from its start (aidocks/plans/saves_plan.md).
"""
from __future__ import annotations

import copy
import logging

from .storydata import VARIABLE_DEFAULT

log = logging.getLogger('state')

#: The labels of the variables the story engine itself reads.
LOCKOUT = 'lockout'
END = 'end'
LOCATION = 'location'


class StoryState:
    def __init__(self, story):
        self.story = story
        self.variables = {}
        self.heard = set()
        self.actioned = {}
        self.reset()

    # ---- the whole state ----------------------------------------------------
    def reset(self):
        """Back to a story never played, as Restart story and the end's reset do
        (-[ViewController resetGameState], 0x100011068)."""
        self.variables = {v: VARIABLE_DEFAULT for v in self.story.refs('variables')}
        self.heard = set()
        self.actioned = {}

    def snapshot(self):
        """Everything, copied, so later changes never reach it."""
        return {'variables': dict(self.variables), 'heard': sorted(self.heard),
                'actioned': dict(self.actioned)}

    def restore(self, snap):
        """Put a snapshot back. A variable the snapshot does not have keeps its default,
        and one the story does not know is dropped, so an old save still loads."""
        snap = copy.deepcopy(snap or {})
        self.reset()
        for var, value in (snap.get('variables') or {}).items():
            if var in self.variables:
                self.variables[var] = str(value)
        known_spiels = set(self.story.refs('actionSpiels'))
        self.heard = {s for s in snap.get('heard') or [] if s in known_spiels}
        known_actions = set(self.story.refs('actions'))
        self.actioned = {a: int(n) for a, n in (snap.get('actioned') or {}).items()
                         if a in known_actions and int(n) > 0}

    # ---- the variables --------------------------------------------------------
    def variable(self, label):
        """The softRef of the variable with this label, or None."""
        found = self.story.find('variables', label)
        return found[0] if found else None

    def get(self, var):
        return self.variables.get(var, VARIABLE_DEFAULT)

    def get_by_label(self, label):
        var = self.variable(label)
        return self.get(var) if var else VARIABLE_DEFAULT

    def apply(self, sets):
        """Apply a ``set`` of {variable softRef: value}; [(variable, old, new)] for each
        one that changed."""
        changed = []
        for var, value in (sets or {}).items():
            value = str(value)
            old = self.get(var)
            if var not in self.variables:
                log.warning('a set names %s, which is not a variable; it is kept anyway', var)
            self.variables[var] = value
            if value != old:
                changed.append((var, old, value))
        return changed

    def holds(self, condition):
        """Whether every variable in ``condition`` equals its value exactly, as text."""
        return all(self.get(var) == str(value) for var, value in (condition or {}).items())

    @property
    def ended(self):
        """The story is over once the variable labelled ``end`` is anything but "0"
        (-[Vars setString:to:], 0x100030f48)."""
        return self.get_by_label(END) != VARIABLE_DEFAULT

    @property
    def locked_out(self):
        return self.get_by_label(LOCKOUT) != VARIABLE_DEFAULT

    def set_by_label(self, label, value):
        var = self.variable(label)
        return self.apply({var: value}) if var else []

    def non_default(self):
        """[(label, value)] for every variable that is not "0", in the index's order, for
        debug mode's F4."""
        return [(self.story.label(v), self.variables[v]) for v in self.story.refs('variables')
                if v in self.variables and self.variables[v] != VARIABLE_DEFAULT]

    # ---- heard spiels -----------------------------------------------------------
    def mark_heard(self, spiel):
        self.heard.add(spiel)

    def is_heard(self, spiel):
        return spiel in self.heard

    # ---- spiels' next -------------------------------------------------------------
    def next_spiel(self, spiel):
        """The spiel that follows ``spiel`` as it ends: the first of its ``next`` entries
        whose condition holds, tried in order (+[Sound tick], 0x100020930); None when none
        does."""
        for entry in (self.story.record(spiel) or {}).get('next') or []:
            if self.holds(entry.get('if')):
                return entry.get('softRef')
        return None

    # ---- actions ------------------------------------------------------------------
    def count(self, action):
        return self.actioned.get(action, 0)

    def burnt(self, action):
        """An action that burns after reading is gone once chosen as often as it has
        spiels."""
        rec = self.story.record(action) or {}
        return bool(rec.get('burnAfterReading')) and self.count(action) >= len(rec.get('actionSpiels') or [])

    def offered(self):
        """The actions on offer now, as +[Story actionsMenu] (0x10001aaa8) builds them:
        every one whose condition holds and that is not burnt, by ``order``, lowest first.
        Two with the same order keep the index's order."""
        found = []
        for i, action in enumerate(self.story.refs('actions')):
            rec = self.story.record(action)
            if rec is None or self.burnt(action) or not self.holds(rec.get('if')):
                continue
            found.append((rec.get('order', 0), i, action))
        return [action for _order, _i, action in sorted(found)]

    def choose(self, action):
        """Choose an action, as +[Story respondToDecision:] (0x10001b2e8) does: the spiel to
        play is its ``actionSpiels[n]``, n being how often it was chosen before, capped at
        the last; its count goes up by 1, and its ``set`` applies. Returns (the spiel, the
        variables changed)."""
        rec = self.story.record(action) or {}
        spiels = rec.get('actionSpiels') or []
        spiel = spiels[min(self.count(action), len(spiels) - 1)] if spiels else None
        self.actioned[action] = self.count(action) + 1
        changed = self.apply(rec.get('set'))
        return spiel, changed
