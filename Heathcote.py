"""Heathcote for Windows.

    python Heathcote.py

Options (aidocks/plans/foundation_plan.md):

    --debug               debug mode for this run (source runs only)
    --spiel LABEL         Start story begins at any spiel by its label, in debug mode only
    -v                    a more detailed log
    --exit-after SECONDS  quit by itself after that many seconds

Every run writes logs/log.txt in the save folder, %APPDATA%\\Heathcote, keeping the
run before as log.old.txt. An error that stops the game writes logs/crash.txt and is
spoken, so a player who cannot see the screen knows why the game closed.
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import platform
import sys
import time
import traceback

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

from heathcote import paths  # noqa: E402

log = logging.getLogger('heathcote')

CRASH_MESSAGE = ('Heathcote has stopped because of an error. The details are in '
                 'crash.txt, in the logs folder of the game\'s save folder.')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog='Heathcote', description='Heathcote for Windows')
    parser.add_argument('--debug', action='store_true', help='debug mode for this run (source runs only)')
    parser.add_argument('--spiel', metavar='LABEL',
                        help='start the story at any spiel by its label, in debug mode only')
    parser.add_argument('-v', '--verbose', action='store_true', help='a more detailed log')
    parser.add_argument('--exit-after', metavar='SECONDS', type=float,
                        help='quit by itself after that many seconds')
    return parser.parse_args(argv)


def start_log(verbose):
    """logs/log.txt for this run, keeping the run before as log.old.txt."""
    folder = paths.logs_dir()
    current = os.path.join(folder, 'log.txt')
    old = os.path.join(folder, 'log.old.txt')
    try:
        if os.path.exists(current):
            os.replace(current, old)
    except OSError:
        pass
    handler = logging.FileHandler(current, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-7s %(name)-9s %(message)s',
                                           '%H:%M:%S'))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    return current


def write_crash(error_text):
    """logs/crash.txt, for the last error that stopped the game."""
    path = os.path.join(paths.logs_dir(), 'crash.txt')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('Heathcote stopped because of an error.\n')
            f.write('When: %s\n' % datetime.datetime.now().isoformat(timespec='seconds'))
            f.write('Version: %s\n' % paths.version())
            f.write('Python: %s\n' % sys.version.replace('\n', ' '))
            f.write('System: %s\n' % platform.platform())
            f.write('Running from: %s\n\n' % ('a build' if paths.FROZEN else 'source'))
            f.write(error_text)
    except OSError:
        pass
    return path


def get_speech():
    """The screen reader speech, or None when it cannot start; the game runs without it
    rather than not at all."""
    try:
        from heathcote.platform.speech import Speech
    except ImportError:
        return None
    try:
        return Speech.shared()
    except Exception:
        log.exception('speech could not start')
        return None


def say_why(speech, text):
    """Speak why the game is closing, and give the screen reader time to say it."""
    if speech is None:
        return
    try:
        speech.speak(text)
        time.sleep(4)
    except Exception:
        pass


def spiel_from_options(options, debug):
    """The softRef of the spiel ``--spiel`` names by its label, when it is allowed and the
    story has a spiel with that label; or None. Labels are the "Spiel:" headings of
    analysis/script/Heathcote.txt; when two spiels share one, the first is taken."""
    if not options.spiel:
        return None
    if not debug:
        log.warning('--spiel works only in debug mode, so it is ignored')
        return None
    from heathcote.game.storydata import StoryData
    found = StoryData.shared().find('actionSpiels', options.spiel)
    if not found:
        log.warning('there is no spiel labelled "%s", so it is ignored', options.spiel)
        return None
    return found[0]


def main(argv=None):
    options = parse_args(argv)
    start_log(options.verbose)
    log.info('Heathcote %s starting, from %s', paths.version(), 'a build' if paths.FROZEN else 'source')
    speech = get_speech()
    try:
        # compiler.py --test looks for this line, to know a build found its data.
        log.info('game data: %s', paths.game())
        if options.debug and paths.FROZEN:
            log.warning('--debug works only when running from source, so it is ignored')
        import pygame
        from heathcote.app import App
        from heathcote.game.opening import first_screen
        app = App(options, speech=speech)
        app.progress                                # read now, so its state is in the log
        app.start_spiel = spiel_from_options(options, app.debug)
        if app.start_spiel is not None:
            log.info('Start story will begin at "%s"', options.spiel)
        app.run(first_screen(app), pygame)
        log.info('Heathcote closed')
        return 0
    except SystemExit as stop:
        if isinstance(stop.code, str):              # a message to give the player, such as missing data
            log.error('%s', stop.code)
            write_crash(stop.code + '\n')
            say_why(speech, stop.code)
            return 1
        raise
    except Exception:
        text = traceback.format_exc()
        log.error('the game stopped because of an error:\n%s', text)
        write_crash(text)
        say_why(speech, CRASH_MESSAGE)
        return 1
    finally:
        logging.shutdown()


if __name__ == '__main__':
    sys.exit(main())
