"""Write the whole story as plain text, into analysis/script/Heathcote.txt.
Standard library only.

    python tools/script_text.py

The story is one long episode with branching choices, so it is one file. It
runs in the order the story opens up from the start: each spiel is followed
by the spiels it leads to, through its next entries and through the actions
its variable sets make available. Whatever that walk does not reach comes at
the end, under its own heading.

Each spiel begins with its label on a line of its own, "Spiel: <label>", so a
screen reader's find can jump to it, and the label is what --spiel takes.
Lines are plain text for reading by screen reader: no tables and no markdown.
"""
import os
import sys

from story import ROOT, Story

OUT = os.path.join(ROOT, "analysis", "script", "Heathcote.txt")


def seconds(t):
    t = float(t)
    return ("%g second" % t) + ("" if t == 1 else "s")


class Writer:
    def __init__(self, story):
        self.s = story
        self.lines = []
        # Which actions each (variable, value) pair can open.
        self.opens = {}
        for a in story.refs("actions"):
            for var, val in (story.record(a) or {}).get("if", {}).items():
                self.opens.setdefault((var, val), []).append(a)
        # Which actions lead to each spiel, and which spiels lead to it by next.
        self.by_action, self.by_next = {}, {}
        for a in story.refs("actions"):
            for sp in (story.record(a) or {}).get("actionSpiels", []):
                self.by_action.setdefault(sp, []).append(a)
        for sp in story.refs("actionSpiels"):
            for n in (story.record(sp) or {}).get("next", []):
                self.by_next.setdefault(n["softRef"], []).append(sp)

    def out(self, line=""):
        self.lines.append(line)

    def cond(self, c):
        if not c:
            return "always"
        return ", and ".join('%s is "%s"' % (self.s.label(k), v) for k, v in c.items())

    def actions_opened(self, spiel):
        """Actions whose condition names a value this spiel sets, in menu order."""
        found = []
        for _, sets in self.s.timed_sets(spiel):
            for pair in sets.items():
                for a in self.opens.get(pair, []):
                    if a not in found:
                        found.append(a)
        return sorted(found, key=lambda a: (self.s.record(a) or {}).get("order", 0))

    def order(self):
        """Spiels in the order the story opens up from the start.

        It keeps every (variable, value) pair seen so far, starting with each
        variable at its default. After each spiel it adds that spiel's sets, and
        any action whose whole condition is now among them opens, in menu order,
        queueing its spiel. It follows which values have ever been seen, not
        which hold together, so it is a reading order, not a play-through.
        """
        s = self.s
        known = {(v, "0") for v in s.refs("variables")}
        offered = set()
        seen, out = set(), []
        queue = [s.start()] if s.start() else []
        while queue:
            sp = queue.pop(0)
            if sp in seen or s.record(sp) is None:
                continue
            seen.add(sp)
            out.append(sp)
            rec = s.record(sp)
            queue += [n["softRef"] for n in rec.get("next", [])]
            for _, sets in s.timed_sets(rec):
                known |= set(sets.items())
            ready = [a for a in s.refs("actions") if a not in offered
                     and all(p in known for p in (s.record(a) or {}).get("if", {}).items())]
            for a in sorted(ready, key=lambda a: (s.record(a) or {}).get("order", 0)):
                offered.add(a)
                queue += (s.record(a) or {}).get("actionSpiels", [])
        rest = [sp for sp in s.refs("actionSpiels") if sp not in seen]
        return out, rest

    def spiel(self, sp):
        s = self.s
        rec = s.record(sp)
        self.out("Spiel: %s" % s.label(sp))
        path = s.audio_path(sp)
        self.out("Recording: %s" % (os.path.relpath(path, ROOT).replace("\\", "/") if path else "none, it only chooses what comes next"))
        came = ['the action "%s"' % s.label(a) for a in self.by_action.get(sp, [])]
        came += ['the end of "%s"' % s.label(x) for x in self.by_next.get(sp, [])]
        if came:
            self.out("Reached from: %s." % "; ".join(came))
        text = (rec.get("transcript") or "").replace("\t", " ").strip()
        if text:
            self.out("Transcript:")
            for line in text.splitlines():
                if line.strip():
                    self.out("  " + line.strip())
        for t, sets in s.timed_sets(rec):
            for var, val in sets.items():
                self.out('At %s, %s becomes "%s".' % (seconds(t), s.label(var), val))
        for lane, events in s.lanes(rec).items():
            for e in events:
                if "fadeTo" in e:
                    self.out('At %s, %s fades to "%s" over %s.' % (seconds(e["at"]), lane,
                             s.label(e["fadeTo"]["softRef"]), seconds(e["fadeTo"]["duration"])))
                else:
                    self.out("At %s, %s fades out over %s." % (seconds(e["at"]), lane, seconds(e["fadeOut"]["duration"])))
        if rec.get("idleLoop"):
            self.out('When it ends, the idle loop "%s" plays.' % s.label(rec["idleLoop"]))
        for n in rec.get("next", []):
            self.out('Next: "%s", when %s.' % (s.label(n["softRef"]), self.cond(n.get("if", {}))))
        for a in self.actions_opened(rec):
            self.out('Opens the action "%s".' % s.label(a))
        self.out()

    def action(self, a):
        s = self.s
        rec = s.record(a)
        self.out("Action: %s" % s.label(a))
        voice = s.record(rec.get("systemVoice"))
        spoken = (voice or {}).get("transcript") or s.label(rec.get("systemVoice"))
        self.out('Spoken as: "%s".' % spoken.strip())
        self.out("Offered when %s." % self.cond(rec.get("if", {})))
        self.out("Place in the menu: %s." % rec.get("order"))
        if rec.get("burnAfterReading"):
            self.out("It goes away once chosen.")
        for sp in rec.get("actionSpiels", []):
            self.out('Plays: "%s".' % s.label(sp))
        self.out()

    def write(self):
        s = self.s
        first, rest = self.order()
        self.out("Heathcote: the whole story")
        self.out()
        self.out("Written by tools/script_text.py from the original's data. Do not edit it by hand; run the tool again.")
        self.out("%d spiels and %d actions. Spiels come first, in the order the story opens up from the start; then the spiels that order does not reach; then every action, in menu order." % (len(s.refs("actionSpiels")), len(s.refs("actions"))))
        self.out()
        self.out("Part 1: from the start")
        self.out()
        for sp in first:
            self.spiel(sp)
        self.out("Part 2: spiels not reached by that walk")
        self.out()
        if not rest:
            self.out("None.")
            self.out()
        for sp in rest:
            self.spiel(sp)
        self.out("Part 3: the actions")
        self.out()
        for a in sorted(s.refs("actions"), key=lambda a: ((s.record(a) or {}).get("order", 0), s.label(a))):
            self.action(a)
        return "\n".join(self.lines).rstrip() + "\n"


def main():
    text = Writer(Story()).write()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("Wrote %s, %d lines." % (os.path.relpath(OUT, ROOT), text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
