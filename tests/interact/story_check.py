"""Play the story by ear, by the original's rules (aidocks/plans/story_engine_plan.md).

    python tests/interact/story_check.py

It runs the game's own main loop and story screen, with the tool's keys added, so what is
heard here is what the game does, F1 and the volume keys included. It grew with each
section of the story engine plan, and now has all of it: the story plays from its start,
moving on by itself wherever a spiel leads straight into the next, with its music and
ambience in context; the actions menu chooses what happens next; the game's own keys work
during play; debug mode, which the tool turns on for itself without remembering it, gives
F2 to F4; and the tool can say the story's state as it goes.

The game's keys:

    Up or Enter          open the actions menu, or hear it refused while the spiel is locked out
    In the actions menu: the arrows move, Home and End jump, Enter accepts, Escape closes,
                         Space speaks the choice's text, and Tab says the menu is open
    Left and Right       rewind and fast-forward
    Escape               pause, with the stand-in pause menu: Resume, or Return to menu, which quits
    Tab                  say where you are, as the game does
    Shift+Home, Shift+End        the master volume
    Page Up, Page Down           the background volume
    Shift+Page Up, Shift+Page Down   the interface volume
    F1                   the key bindings
    F2                   debug: skip to the end of the spiel, its waiting sets and cues firing
    F3                   debug: find a spiel by part of its label and jump there, the variables
                         kept; each letter is spoken, Backspace takes one off, Enter jumps, the
                         same text again moves to the next match, and Escape gives up
    F4                   debug: say every variable that is not 0

The tool's own keys:

    R                    start the story again from its beginning, with its state reset
    Comma and Full stop  choose a spiel, saying its label, and "leads on" when it has next spiels;
                         with Shift, 10 at a time
    3                    play the spiel chosen, with the story's state as it is
    S                    say the spiel, how far in, and whether it is locked out or has ended
    V                    turn saying each spiel's label as it begins on or off; on at first
    C                    turn saying each variable as it changes on or off, such as "lockout is
                         now 1."; off at first
    H                    say whether the spiel playing has been heard, which lets the menu open
                         through its lockout, and how many spiels have been heard in all
    A                    say the actions the menu would offer now, without opening it
    Q                    quit

It keeps its own save under %APPDATA%\\Heathcote\\interact\\story_check, so nothing here
ever changes the game's own volumes, keys or progress.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
os.environ.setdefault('HEATHCOTE_USER_DIR', os.path.join(
    os.environ.get('APPDATA') or os.path.expanduser('~'), 'Heathcote', 'interact', 'story_check'))

import Heathcote  # noqa: E402  (the game's own log and crash file)
from heathcote.game.player import PLAYING, SCENE_END, STORY_END  # noqa: E402
from heathcote.game.story_screen import StoryScreen  # noqa: E402

INTRO = ('Story check, in debug mode. The story starts now, with the game\'s own keys, and F2 '
         'to F4. R starts again, Comma and Full stop choose a spiel and 3 plays it, S says where '
         'the story is, V turns the spiel labels on or off, C the variable changes, H says what '
         'is heard, and A the actions on offer. Q quits.')


class CheckScreen(StoryScreen):
    """The game's story screen, with the tool's keys first."""

    name = 'story check'

    def __init__(self, app):
        super().__init__(app)
        self.spiels = [s for s in self.story.refs('actionSpiels') if self.story.record(s)]
        self.spiel_index = 0
        self.announce = True
        self.changes = False            # saying each variable change, with C
        self.player.on_spiel = self.spiel_began
        self.player.on_scene_end = self.scene_ended
        self.player.on_changed = self.variables_changed
        self.introduced = False

    def opened(self):
        if not self.introduced:
            self.introduced = True
            self.say(INTRO)
        super().opened()

    def story_ended(self):
        self.say('The story has ended. Press R to start again.')

    def leave(self):
        """Return to menu, from the pause menu: in the tool, there is no menu, so it quits."""
        self.app.quit()

    # ---- what the tool says ----------------------------------------------------
    def spiel_began(self, soft):
        if self.announce:
            self.say(self.story.label(soft), interrupt=False)

    def scene_ended(self, soft):
        if self.announce:
            self.say('End of scene: %s.' % self.story.label(soft), interrupt=False)

    def variables_changed(self, changes):
        if self.changes:
            self.say(' '.join('%s is now %s.' % (self.story.label(var), new)
                              for var, _old, new in changes), interrupt=False)

    def heard(self):
        p = self.player
        count = len(self.state.heard)
        total = 'heard: %d spiel%s in all' % (count, '' if count == 1 else 's')
        if p.current is None:
            self.say('Nothing is playing; %s.' % total)
            return
        state = 'heard before' if self.state.is_heard(p.current) else 'not heard yet'
        self.say('%s is %s; %s.' % (self.story.label(p.current), state, total))

    def offered(self):
        choices = [self.player.choice_text(a) for a in self.state.offered()]
        if not choices:
            self.say('The menu would offer nothing.')
        else:
            self.say('%d on offer: %s.' % (len(choices), ', '.join(choices)))

    def where(self):
        p = self.player
        if p.current is None:
            self.say('The story has not started.')
            return
        label = self.story.label(p.current)
        if p.paused:
            self.say('Paused, in %s.' % label)
        elif p.menu_open:
            self.say('The actions menu is open, over %s.' % label)
        elif p.phase == SCENE_END:
            self.say('End of scene: %s.' % label)
        elif p.phase == STORY_END:
            self.say('The story has ended, at %s.' % label)
        elif p.phase == PLAYING:
            locked = ', locked out' if not p.can_open_menu() else ''
            self.say('%s, %.0f of %.0f seconds%s.' % (label, p.position, self.app.audio.spiel.length, locked))

    # ---- the tool's keys ---------------------------------------------------------
    def restart(self):
        self.player.stop()
        self.state.reset()
        self.player.start()

    def choose(self, step):
        self.spiel_index = (self.spiel_index + step) % len(self.spiels)
        soft = self.spiels[self.spiel_index]
        rec = self.story.record(soft) or {}
        self.say('%s%s%s, %d of %d.' % (self.story.label(soft), ', leads on' if rec.get('next') else '',
                                        ', no recording' if not rec.get('file') else '',
                                        self.spiel_index + 1, len(self.spiels)))

    def play_chosen(self):
        self.player.stop()
        self.player.play(self.spiels[self.spiel_index])

    def handle_key(self, key, mods):
        if key in (',', '.') and mods in ([], ['shift']):
            self.choose((-1 if key == ',' else 1) * (10 if mods else 1))
        elif mods:
            return super().handle_key(key, mods)
        elif key == 'r':
            self.restart()
        elif key == '3':
            self.play_chosen()
        elif key == 's':
            self.where()
        elif key == 'v':
            self.announce = not self.announce
            self.say('Spiel labels %s.' % ('on' if self.announce else 'off'))
        elif key == 'c':
            self.changes = not self.changes
            self.say('Variable changes %s.' % ('on' if self.changes else 'off'))
        elif key == 'h':
            self.heard()
        elif key == 'a':
            self.offered()
        elif key == 'q':
            self.app.quit()
        else:
            return super().handle_key(key, mods)
        return True


def main():
    import logging
    import pygame
    from heathcote.app import App
    options = Heathcote.parse_args([])
    Heathcote.start_log(True)
    logging.getLogger('heathcote').info('story check starting')
    app = App(options)
    app.set_debug(True, remember=False)     # F2 to F4, for this run only
    try:
        app.run(CheckScreen(app), pygame)
    except SystemExit as stop:
        if isinstance(stop.code, str):
            app.speech.speak(stop.code)
            print(stop.code)
            pygame.time.wait(4000)
        raise
    except Exception:
        # Never close without a word: the error goes to the tool's crash.txt and is spoken,
        # as the game does.
        import traceback
        text = traceback.format_exc()
        logging.getLogger('heathcote').error('the story check stopped because of an error:\n%s', text)
        path = Heathcote.write_crash(text)
        print(text)
        app.speech.speak('The story check stopped because of an error. The details are in %s.' % path)
        pygame.time.wait(6000)
        raise


if __name__ == '__main__':
    main()
