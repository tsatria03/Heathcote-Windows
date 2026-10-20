"""Read the original's story data as it is, and check it. Standard library only.

    python tools/story.py              a summary, then every problem found
    python tools/story.py --labels     every softRef's label, by category

The data is the export of the original's authoring tool, in game/data/text/:
- system/Heathcote v1.01.bundle.json, the index: `labels` maps each softRef
  to a readable name, and `assets` maps each category to {softRef: record id}.
- story/<record id>.json, one record each.

Every reference inside a record is a softRef, except `file`, which is the id
of the record describing the audio or image file.

The rules for reading the data and finding each recording live in the game's
own package, heathcote/game/storydata.py, and this tool uses them as they are,
so what these checks report is what the game would meet. What is here is the
checking, and the original's images, which the game never ships.

This module only reads; it writes nothing.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from heathcote.game.storydata import (  # noqa: E402  (the game's own rules)
    FOLDERS, LANES, START_LABEL, UNPLAYED_LANES, VARIABLE_DEFAULT, StoryData, disk_name)

IMAGES = os.path.join(ROOT, "game", "images", "story")

# Categories in the index that the original never reads; a broken record in one is only a note.
UNUSED = ("recaps", "describes", "describeSpiels", "recapSpiels", "orphanSpiels")

__all__ = ["FOLDERS", "LANES", "START_LABEL", "UNPLAYED_LANES", "VARIABLE_DEFAULT", "UNUSED",
           "ROOT", "IMAGES", "Story", "disk_name"]


class Story(StoryData):
    """The game's story data, with the checks and the images on top."""

    def graphic_path(self, soft):
        rec = self.record(soft)
        if not rec or not rec.get("file"):
            return None
        return os.path.join(IMAGES, rec["file"] + ".png")

    # The parts of a spiel.

    @staticmethod
    def timed_sets(spiel):
        """[(seconds, {variable softRef: value})] of a spiel, in time order."""
        sets = spiel.get("set") or []
        if isinstance(sets, dict):
            return [(0.0, sets)] if sets else []
        return sorted(((float(s["at"]), s["set"]) for s in sets), key=lambda t: t[0])

    @staticmethod
    def lanes(spiel):
        """{lane: [event]} for a spiel's music and ambience lanes that have events."""
        return {k: spiel[k] for k in LANES if spiel.get(k)}

    def variable_values(self):
        """{variable softRef: set of values it can hold}, the default included."""
        vals = {v: {VARIABLE_DEFAULT} for v in self.refs("variables")}
        for soft in self.refs("actionSpiels"):
            for _, sets in self.timed_sets(self.record(soft) or {}):
                for var, val in sets.items():
                    vals.setdefault(var, {VARIABLE_DEFAULT}).add(val)
        for soft in self.refs("actions"):
            rec = self.record(soft) or {}
            for var, val in (rec.get("set") or {}).items():
                vals.setdefault(var, {VARIABLE_DEFAULT}).add(val)
        return vals

    # Checking.

    def check(self):
        """Return (problems, notes).

        A problem would break the game: a reference to nothing, a missing
        recording, no start. A note is worth knowing but plays as the original
        did: dead content, a record nothing uses, an ambiguity.
        """
        problems, notes = [], []
        for name, why in self.unreadable:
            notes.append("Record %s could not be read (%s); it is skipped." % (name, why))

        def ref(soft, want, where):
            cat = self.category.get(soft)
            if cat is None:
                problems.append("%s names %s, which is not in the index." % (where, soft))
            elif cat != want:
                problems.append("%s names %s (%s), a %s, not a %s." % (where, self.label(soft), soft, cat, want))
            elif self.record(soft) is None:
                problems.append("%s names %s (%s), whose record is missing." % (where, self.label(soft), soft))

        for cat, refs in self.assets.items():
            for soft, rid in refs.items():
                if rid not in self.records:
                    (notes if cat in UNUSED else problems).append(
                        'The %s "%s" (%s) has no readable record.' % (cat, self.label(soft), soft))

        # Every reference leads to a real record of the right kind.
        for soft in self.refs("actions"):
            rec = self.record(soft)
            if not rec:
                continue
            where = 'The action "%s"' % self.label(soft)
            for s in rec.get("actionSpiels", []):
                ref(s, "actionSpiels", where)
            if not rec.get("actionSpiels"):
                problems.append("%s plays no spiel." % where)
            ref(rec.get("systemVoice"), "systemVoice", where)
            for var in rec.get("if", {}):
                ref(var, "variables", where + "'s condition")
        for soft in self.refs("actionSpiels"):
            rec = self.record(soft)
            if not rec:
                continue
            where = 'The spiel "%s"' % self.label(soft)
            for n in rec.get("next", []):
                ref(n["softRef"], "actionSpiels", where + "'s next")
                for var in n.get("if", {}):
                    ref(var, "variables", where + "'s next condition")
            for _, sets in self.timed_sets(rec):
                for var in sets:
                    ref(var, "variables", where + "'s set")
            if rec.get("idleLoop"):
                ref(rec["idleLoop"], "idleLoops", where + "'s idle loop")
            for lane, events in self.lanes(rec).items():
                want = "bgm" if lane == "bgm" else "ambience"
                for e in events:
                    if "fadeTo" in e:
                        ref(e["fadeTo"]["softRef"], want, "%s's %s" % (where, lane))
                    elif "fadeOut" not in e:
                        problems.append("%s's %s has an event that neither fades to nor fades out." % (where, lane))

        # Every recording is on disk.
        for cat in FOLDERS:
            for soft in self.refs(cat):
                rec = self.record(soft)
                if not rec:
                    continue
                if not rec.get("file"):
                    notes.append('The %s "%s" has no recording.' % (cat, self.label(soft)))
                    continue
                path = self.audio_path(soft)
                if path is None:
                    problems.append('The %s "%s" names a file record that is missing.' % (cat, self.label(soft)))
                elif not os.path.exists(path):
                    problems.append('The %s "%s" should be at %s, which is missing.'
                                    % (cat, self.label(soft), os.path.relpath(path, ROOT)))
        for soft in self.refs("graphics"):
            path = self.graphic_path(soft)
            if path and not os.path.exists(path):
                problems.append('The graphic "%s" should be at %s, which is missing.'
                                % (self.label(soft), os.path.relpath(path, ROOT)))

        # Every value a condition asks for can happen. One that cannot is dead
        # content in the original, never offered, rather than a break.
        values = self.variable_values()
        def wanted(cond, where):
            for var, val in cond.items():
                if val not in values.get(var, {VARIABLE_DEFAULT}):
                    notes.append('%s is never offered: it asks for %s to be "%s", which nothing ever sets.'
                                 % (where, self.label(var), val))
        for soft in self.refs("actions"):
            wanted((self.record(soft) or {}).get("if", {}), 'The action "%s"' % self.label(soft))
        for soft in self.refs("actionSpiels"):
            for n in (self.record(soft) or {}).get("next", []):
                wanted(n.get("if", {}), 'The spiel "%s"\'s next "%s"' % (self.label(soft), self.label(n["softRef"])))

        # Every spiel can be reached from the start.
        start = self.start()
        if start is None:
            problems.append('No spiel is labelled "%s", so the story cannot start.' % START_LABEL)
        else:
            unreached = set(self.refs("actionSpiels")) - self.reachable(start)
            for soft in sorted(unreached, key=self.label):
                notes.append('The spiel "%s" is never reached from the start, by a next or an action that can be offered.'
                             % self.label(soft))

        # Two next entries that can both be true when a spiel ends. The first
        # listed wins (+[Sound tick], 0x100020930), so this is precedence, not
        # a fault; it is noted so the order is never changed by accident.
        for soft in self.refs("actionSpiels"):
            nexts = (self.record(soft) or {}).get("next", [])
            for i in range(len(nexts)):
                for j in range(i + 1, len(nexts)):
                    a, b = nexts[i].get("if", {}), nexts[j].get("if", {})
                    if not any(k in b and b[k] != v for k, v in a.items()):
                        notes.append('The spiel "%s" has next entries "%s" and "%s" that can both be true; the first, "%s", wins.'
                                     % (self.label(soft), self.label(nexts[i]["softRef"]),
                                        self.label(nexts[j]["softRef"]), self.label(nexts[i]["softRef"])))

        # Fades on a lane the original never plays.
        for soft in self.refs("actionSpiels"):
            for lane in UNPLAYED_LANES:
                if (self.record(soft) or {}).get(lane):
                    notes.append('The spiel "%s" has fades on the plain %s lane, which the original never played.'
                                 % (self.label(soft), lane))

        # Labels that more than one softRef in a category share.
        for cat in ("actionSpiels", "actions"):
            seen = {}
            for soft in self.refs(cat):
                seen.setdefault(self.label(soft), []).append(soft)
            for lab, softs in sorted(seen.items()):
                if len(softs) > 1:
                    notes.append('%d %s share the label "%s".' % (len(softs), cat, lab))
        return problems, notes

    def reachable(self, start):
        """Spiels reachable from the start through next entries and actions.

        An action counts once every value its condition asks for can happen; it
        does not follow which values hold together at a given moment, so this
        can call a spiel reachable that in play is not. It never misses one.
        """
        values = self.variable_values()
        open_actions = [s for s in self.refs("actions")
                        if all(v in values.get(k, {VARIABLE_DEFAULT})
                               for k, v in (self.record(s) or {}).get("if", {}).items())]
        seen, todo = set(), [start]
        for a in open_actions:
            todo += (self.record(a) or {}).get("actionSpiels", [])
        while todo:
            soft = todo.pop()
            if soft in seen or self.record(soft) is None:
                continue
            seen.add(soft)
            todo += [n["softRef"] for n in self.record(soft).get("next", [])]
        return seen


def main(args):
    story = Story()
    if args[:1] == ["--labels"]:
        for cat, refs in story.assets.items():
            if refs:
                print("%s (%d):" % (cat, len(refs)))
                for soft in refs:
                    print("  %s: %s" % (soft, story.label(soft)))
        return 0
    print("Index: %d labels, %d records read." % (len(story.labels), len(story.records)))
    for cat, refs in story.assets.items():
        if refs:
            print("  %s: %d" % (cat, len(refs)))
    print('Start: "%s".' % story.label(story.start()) if story.start() else "Start: none.")
    problems, notes = story.check()
    print()
    print("%d problems." % len(problems))
    for p in problems:
        print("  " + p)
    print("%d notes." % len(notes))
    for n in notes:
        print("  " + n)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
