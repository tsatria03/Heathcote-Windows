"""Hear the menus around the story (aidocks/plans/menus_plan.md).

    python tests/interact/menus_check.py

It runs the game itself, from its opening, with a few keys of the tool's own added, each
with Control so it never takes one of the game's. It grows with each section of the menus
plan, and now has all four sections:

    the police radio, with "Heathcote." spoken; Enter skips it
    the first time, the first-run notice; Enter continues, and it is not shown again
    the main menu, with the title music under it; Page Up and Page Down set its volume
    the main menu's rows: Start story, Settings, Credits and Quit
    Credits: Back first, then a row for each credit, with the title music playing on
    Start story fades the title music out over 3 seconds, as the story fades in
    Escape in the story: the pause menu, with Resume, Restart story, Settings and
    Return to menu; Restart story asks first, with No first
    Return to menu leaves the story paused, its muffled backgrounds fading out under the
    title music, and the main menu's first row becomes Continue story, with its chapter,
    which picks the story up exactly there
    the end: the end credits open over the story, which plays on beneath them, its ending
    music coming in; leaving them returns to the main menu, the story reset

The tool's own keys:

    Control+N    forget the notice, and start again from the police radio
    Control+T    say whether the title music is playing and at what volume, and whether the
                 story's sound is faded in, faded out, or fading
    Control+S    say whether a story is under way, playing, paused, or paused under the
                 main menu, with its spiel and chapter
    Control+E    during the story, jump to its last spiel, "ending (commercial)", 7.5
                 seconds before it ends the story, to hear the end credits
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

INTRO = ('Menus check. Control N starts again with the notice, Control T says the title music, '
         'Control S the story, Control E jumps near its end, and Control Q quits.')
#: Seconds into "ending (commercial)" that Control+E jumps to: 7.5 before end is set.
NEAR_THE_END = 52.0


class CheckApp(App):
    """The game's main loop, with the tool's Control keys first."""

    def key_down(self, key, mods, now=None, char=''):
        if mods == ['ctrl'] and key in ('n', 't', 's', 'e', 'q'):
            if key == 'n':
                self.start_again()
            elif key == 'e':
                self.near_the_end()
            elif key == 't':
                self.title_report()
            elif key == 's':
                self.story_report()
            else:
                self.quit()
            return
        super().key_down(key, mods, now, char)

    def start_again(self):
        self.settings.set('first_run_notice_shown', False)
        if self.paused_story is not None:           # a story paused under the menu ends
            self.paused_story.player.stop()
            self.paused_story = None
        self.stop_title_music()
        self.speech.speak('The notice is forgotten. Starting again.')
        self.stack.reset(OpeningScreen(self))

    def near_the_end(self):
        """Jump the story playing to "ending (commercial)", a few seconds before it sets end
        at 59.5 seconds, so the end credits can be heard without playing it all."""
        from heathcote.game.story_screen import StoryScreen
        screen = self.stack.top
        if not isinstance(screen, StoryScreen):
            self.speech.speak('Start the story first, then press Control E during it.')
            return
        found = screen.story.find('actionSpiels', 'ending (commercial)')
        if not found:
            self.speech.speak('The last spiel was not found.')
            return
        screen.player.jump(found[0])
        self.audio.spiel.seek(NEAR_THE_END)
        self.speech.speak('Near the end.')

    def story_report(self):
        from heathcote.game.state import LOCATION
        from heathcote.game.story_screen import StoryScreen
        screen = self.paused_story or next(
            (s for s in self.stack.screens if isinstance(s, StoryScreen)), None)
        if screen is None or screen.player.current is None:
            self.speech.speak('There is no story under way.')
            return
        if screen is self.paused_story:
            where = 'paused under the main menu'
        elif screen.ending:
            where = 'over, playing on under the end credits'
        else:
            where = 'paused' if screen.player.paused else 'playing'
        chapter = screen.state.get_by_label(LOCATION)
        self.speech.speak('The story is %s, at the spiel %s%s.' % (
            where, screen.story.label(screen.player.current),
            '' if chapter == '0' else ', in the chapter %s' % chapter))

    def title_report(self):
        playing = self.audio.ok and self.audio.slot('titleBgm').playing
        if playing:
            title = 'The title music is playing, at a title volume of %d percent.' % self.settings.get('title_volume')
        else:
            title = 'The title music is silent.'
        # The story's sound, spiel and backgrounds together, fades out under the title music
        # and back in with the story, as the original's did.
        level, target = self.audio.story_level(), self.audio.story_target
        if abs(level - target) < 0.005:
            story = "The story's sound is faded %s." % ('in' if target else 'out')
        else:
            story = "The story's sound is fading %s." % ('in' if target else 'out')
        self.speech.speak('%s %s' % (title, story))


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
