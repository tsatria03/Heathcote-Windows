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
  (-[Vars setString:to:], 0x100030f48), and ``on_story_end`` is called. The spiel and its
  lanes play on, so the ending music still comes in.

Lockout and the actions menu (section 3; +[StoryView raiseActionsDial], 0x100024204):

* **The menu opens** when ``lockout`` is "0", or when the spiel playing has been heard
  before. Then ``click-good`` plays, the backgrounds hush, the spiel pauses, and
  ``menu-open`` plays.
* **Otherwise it is refused:** ``click-bad`` and ``menu-unavailable`` play, and a 1.5-second
  grace starts, during which pausing is refused too.
* **The choices** are the actions on offer (game/state.py). Each plays its recorded clip
  from ``speech/``; a choice with none is spoken by the screen reader.
* **Accepting** (+[StoryView acceptFromActionsDial], 0x10002477c): ``menu-accepted`` plays,
  the backgrounds unhush, the action is chosen, and its spiel starts 0.25 seconds later.
* **Closing** (+[StoryView lowerActionsDial], 0x10002462c): ``menu-close`` plays, the
  backgrounds unhush, and the spiel plays on.
* **A timed set that turns lockout to "0"** plays ``menu-lockout-ended``
  (+[StoryView spielJustSetVariables:], 0x1000256f4).
* **After a scene ends,** ``menu-reminder`` plays every 7 seconds until something happens
  (-[PlayState tick_played], 0x100033194); ``poke()`` says something did.

The hooks a screen can set: ``on_spiel(soft)`` as each spiel begins, ``on_scene_end(soft)``
when a scene is over, ``on_story_end()``, and ``on_changed(changes)`` after variables change.
"""
from __future__ import annotations

import logging
import time

from .state import LOCATION, LOCKOUT
from .storydata import VARIABLE_DEFAULT

log = logging.getLogger('player')

#: The phases of play.
PLAYING, SCENE_END, STORY_END = 'playing', 'scene end', 'story end'
#: Seconds of the grace after the menu is refused (0x100024560).
GRACE = 1.5
#: Seconds between reminders after a scene ends: 420 ticks.
REMINDER_EVERY = 7.0
#: Seconds from accepting a choice to its spiel starting (WaitState).
ACCEPT_DELAY = 0.25


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
    def __init__(self, audio, story, state, play_sound=None, after=None, clock=time.perf_counter):
        """``after(delay, fn)`` runs ``fn`` later, as the timer loop does; without it, at
        once. ``clock`` is there for the tests."""
        from ..platform.lanes import Lanes
        self.audio = audio
        self.story = story
        self.state = state
        self.play_sound = play_sound or (lambda label: None)
        self.after = after or (lambda delay, fn: fn())
        self.clock = clock
        self.menu_open = False
        self.grace_until = 0.0          # pausing is refused until then, after a refused menu
        self.reminder_at = None         # when the next menu-reminder plays, after a scene ends
        self.pending = None             # an accepted choice's spiel, waiting its 0.25 seconds
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
        self.reminder_at = None
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
        """Follow the spiel: the timed sets and lanes up to its position, then its end; and
        after a scene's end, the reminders."""
        if self.phase != PLAYING:
            if self.phase == SCENE_END:
                self.lanes.update(self.position)
                self._remind()
            elif self.phase == STORY_END:
                # The last spiel plays on under the credits, and its lanes with it, as the
                # original's +[Sound tick] went on: "ending (commercial)" sets end at 59.5
                # seconds, but its music fades to "ending" only at 68.
                self.lanes.update(self.position)
            return
        if self.menu_open:
            return                          # the spiel waits under the menu
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
            lockout = self.state.variable(LOCKOUT)
            if any(var == lockout and new == '0' for var, _old, new in changes):
                self.play_sound('menu-lockout-ended')
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
        self.reminder_at = self.clock() + REMINDER_EVERY
        log.info('end of scene: %s', self.story.label(self.current))
        if self.on_scene_end:
            self.on_scene_end(self.current)
        if changes:
            self.changed(changes)

    # ---- the reminder ------------------------------------------------------------------
    def _remind(self):
        if self.reminder_at is None or self.menu_open or self.paused:
            return
        now = self.clock()
        if now >= self.reminder_at:
            self.play_sound('menu-reminder')
            self.reminder_at = now + REMINDER_EVERY

    def poke(self):
        """Something happened, such as a key: the reminders count their 7 seconds again."""
        if self.reminder_at is not None:
            self.reminder_at = self.clock() + REMINDER_EVERY

    # ---- lockout and the actions menu ----------------------------------------------------
    def can_open_menu(self):
        """``lockout`` is "0", or the spiel playing has been heard before."""
        return not self.state.locked_out or (self.current is not None and self.state.is_heard(self.current))

    @property
    def in_grace(self):
        """Within the 1.5 seconds after a refused menu, when pausing is refused too."""
        return self.clock() < self.grace_until

    def open_menu(self):
        """Open the actions menu, or refuse it; the choices on offer, or None when refused."""
        if self.phase not in (PLAYING, SCENE_END) or self.menu_open or self.pending:
            return None
        self.poke()
        if not self.can_open_menu():
            self.play_sound('click-bad')
            self.play_sound('menu-unavailable')
            self.grace_until = self.clock() + GRACE
            return None
        self.play_sound('click-good')
        self.audio.hush_backgrounds()
        self.audio.spiel.pause()
        self.play_sound('menu-open')
        self.menu_open = True
        return self.state.offered()

    def close_menu(self, quietly=False):
        """Close the menu without choosing: the backgrounds unhush and the spiel plays on.
        ``quietly`` leaves out menu-close, as when losing the window closes it."""
        if not self.menu_open:
            return
        self.menu_open = False
        if not quietly:
            self.play_sound('menu-close')
        self.audio.unhush_backgrounds()
        self.audio.spiel.resume()
        self.poke()

    def accept(self, action):
        """Accept a choice: its spiel starts 0.25 seconds later."""
        if not self.menu_open:
            return
        self.menu_open = False
        self.play_sound('menu-accepted')
        self.audio.unhush_backgrounds()
        self.audio.spiel.stop()
        self.audio.slot('systemVoice').stop()
        self.reminder_at = None
        spiel, changes = self.state.choose(action)
        log.info('chose: %s', self.story.label(action))
        if changes:
            self.changed(changes)
        if spiel is None or self.phase == STORY_END:
            return
        self.pending = spiel

        def begin():
            if self.pending == spiel:
                self.pending = None
                self.play(spiel)
        self.after(ACCEPT_DELAY, begin)

    def choice_clip(self, action):
        """The recorded clip of a choice, from ``speech/``, or None when it has none, as
        "next room" and "just stop" have none."""
        voice = (self.story.record(action) or {}).get('systemVoice')
        rec = self.story.record(voice) if voice else None
        if not rec or not rec.get('file'):
            return None
        return self.story.audio_path(voice)

    def choice_text(self, action):
        """What a choice says: its recording's transcript, or its label."""
        voice = (self.story.record(action) or {}).get('systemVoice')
        text = ((self.story.record(voice) or {}).get('transcript') or '').strip() if voice else ''
        return text or (self.story.label(voice) if voice else '') or self.story.label(action)

    # ---- the keys during play (section 4) ---------------------------------------------
    def rewind(self):
        """Left: the original's rewind, with click-good (-[PlayState right], swipe right). A
        scene that has ended plays again from 1 second before its end, and its idle loop
        stops (+[Sound spotRewind:], 0x1000222cc). True when it rewound."""
        if self.menu_open or self.pending or self.phase not in (PLAYING, SCENE_END) or self.silent:
            return False
        self.play_sound('click-good')
        if self.phase == SCENE_END:
            self.lanes.stop_idle()
            self.phase = PLAYING
            self.reminder_at = None
        return self.audio.spiel.rewind()

    def fast_forward(self):
        """Right: the original's fast-forward, with click-good. True when it runs."""
        if self.menu_open or self.pending or self.phase != PLAYING or self.silent:
            return False
        self.play_sound('click-good')
        return self.audio.spiel.fast_forward()

    @property
    def paused(self):
        return self.audio.story_paused

    def pause(self, click=False):
        """Escape: pause as the original (+[StoryView pause], 0x1000252cc), the backgrounds
        hushed and playing on, the spiel stopped, and pause-pause played. Refused with
        click-bad during the grace after a refused menu (-[PlayState down], 0x100033a40).
        ``click`` plays click-good with pause-pause, for a pause made with a key, unlike the
        original (aidocks/plans/player_feedback_plan.md). True when it paused."""
        if self.paused:
            return False
        if self.in_grace:
            self.play_sound('click-bad')
            return False
        self.audio.pause_story()
        if click:
            self.play_sound('click-good')
        self.play_sound('pause-pause')
        return True

    def resume(self):
        """Unpause (+[StoryView unpause], 0x100025484): unhushed, pause-unpause, and the spiel
        plays on."""
        if not self.paused:
            return
        self.audio.resume_story()
        self.play_sound('pause-unpause')
        self.poke()

    def where(self):
        """What Tab says, as the original's two-finger tap (-[PlayState voiceover],
        0x100033de8), followed by the chapter, the story variable ``location``, once a
        scene has set it (the dev, 2026-10-21: "It doesn't actually say where I'm at in the
        story, like the chapter for example."), in the dev's form (2026-10-21: "Story is
        playing: working late."), such as "Story is at end of scene: offices."."""
        if self.menu_open:
            state = 'Actions menu is open'
        elif self.paused:
            state = 'Story is paused'
        elif self.phase == SCENE_END:
            state = 'Story is at end of scene'
        elif self.phase == STORY_END:
            state = 'Story has ended'
        else:
            state = 'Story is playing'
        chapter = self.state.get_by_label(LOCATION)
        if chapter == VARIABLE_DEFAULT:
            return state + '.'
        return '%s: %s.' % (state, chapter)

    # ---- debug mode (section 5) ----------------------------------------------------------
    def skip(self):
        """F2: to the end of the spiel at once. Its timed sets and lane events still waiting
        fire on the way, so the story stays as it would have been, then it ends as any spiel
        does. True when it skipped."""
        if self.phase != PLAYING or self.menu_open or self.pending or self.paused or self.silent:
            return False
        self.audio.spiel.stop_effects()
        length = self.audio.spiel.length
        self._timed_sets(length)
        if self.phase != PLAYING:
            return True                     # a set on the way ended the story
        self.lanes.update(length)
        self.audio.spiel.seek(length)       # it runs out in a moment and ends as usual
        return True

    def jump(self, soft):
        """F3, and --spiel: play any spiel from its start, the story's state kept as it is,
        so a branch can be set up and then leapt to."""
        if self.menu_open:
            self.menu_open = False
            self.audio.unhush_backgrounds()
        if self.paused:
            self.audio.resume_story()
        self.pending = None
        self.audio.slot('systemVoice').stop()
        self.play(soft)

    def variables_text(self):
        """F4: every variable that is not "0", by label, such as "fear is clowns."."""
        held = self.state.non_default()
        if not held:
            return 'Every variable is 0.'
        return ', '.join('%s is %s' % (label, value) for label, value in held) + '.'

    # ---- what the window shows ------------------------------------------------------
    def transcript(self):
        return ((self.story.record(self.current) or {}).get('transcript') or '').strip()

    def stop(self):
        """Leave the story: the spiel and the idle loop stop, and the lanes fade out."""
        if self.menu_open:
            self.menu_open = False
            self.audio.unhush_backgrounds()
        if self.paused:
            self.audio.resume_story()       # silently: the story is being left
        self.pending = None
        self.reminder_at = None
        self.audio.spiel.stop()
        self.audio.slot('systemVoice').stop()
        self.lanes.stop_all(fade_out=1.0)
        self.phase = None
