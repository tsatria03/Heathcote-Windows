"""Hear the menus around the story (aidocks/plans/menus_plan.md).

    python tests/interact/menus_check.py

It runs the game itself, from its opening, with a few keys of the tool's own added, each
with Control so it never takes one of the game's. It grows with each section of the menus
plan. For now, section 1:

    the police radio, with "Heathcote." spoken; Enter skips it
    the first time, the first-run notice; Enter continues, and it is not shown again
    the main menu, with the title music under it; Page Up and Page Down set its volume
    Start story fades the title music out over 3 seconds, as the story fades in;
    Escape, then Return to menu, brings it back

The tool's own keys:

    Control+N    forget the notice, and start again from the police radio
    Control+T    say whether the title music is playing, its volume, and the story's level
    Control+Q    quit

It keeps its own save under %APPDATA%\\Heathcote\\interact\\menus_check, so nothing here
ever changes the game's own volumes, keys or progress; the notice shows on its first start.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
os.environ.setdefault('HEATHCOTE_USER_DIR', os.path.join(
    os.environ.get('APPDATA') or os.path.expanduser('~'), 'Heathcote', 'interact', 'menus_check'))

import Heathcote  # noqa: E402  (the game's own options, log and crash file)
from heathcote.app import App  # noqa: E402
from heathcote.game.opening import OpeningScreen  # noqa: E402

INTRO = 'Menus check. Control N starts again with the notice, Control T says the title music, Control Q quits.'


class CheckApp(App):
    """The game's main loop, with the tool's Control keys first."""

    def key_down(self, key, mods, now=None, char=''):
        if mods == ['ctrl'] and key in ('n', 't', 'q'):
            if key == 'n':
                self.start_again()
            elif key == 't':
                self.title_report()
            else:
                self.quit()
            return
        super().key_down(key, mods, now, char)

    def start_again(self):
        self.settings.set('first_run_notice_shown', False)
        self.stop_title_music()
        self.speech.speak('The notice is forgotten. Starting again.')
        self.stack.reset(OpeningScreen(self))

    def title_report(self):
        playing = self.audio.ok and self.audio.slot('titleBgm').playing
        self.speech.speak('Title music %s, title volume %d percent. The story is at %d percent.' % (
            'playing' if playing else 'silent', self.settings.get('title_volume'),
            round(self.audio.story_level() * 100)))


def main():
    import logging
    import pygame
    options = Heathcote.parse_args(sys.argv[1:])        # --exit-after, for a silent start
    Heathcote.start_log(True)
    logging.getLogger('heathcote').info('menus check starting')
    app = CheckApp(options)
    app.speech.speak(INTRO)
    try:
        app.run(OpeningScreen(app), pygame)
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
        logging.getLogger('heathcote').error('the menus check stopped because of an error:\n%s', text)
        path = Heathcote.write_crash(text)
        print(text)
        app.speech.speak('The menus check stopped because of an error. The details are in %s.' % path)
        pygame.time.wait(6000)
        raise


if __name__ == '__main__':
    main()
