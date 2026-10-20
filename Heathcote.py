"""Heathcote for Windows.

    python Heathcote.py

Options (aidocks/plans/foundation_plan.md):

    --debug               debug mode for this run (source runs only)
    --spiel LABEL         start the story at any spiel by its label, in debug mode only
    -v                    a more detailed log
    --exit-after SECONDS  quit by itself after that many seconds

Every run writes logs/log.txt in the save folder, %APPDATA%\\Heathcote, keeping the
run before as log.old.txt. An error that stops the game writes logs/crash.txt and is
spoken, so a player who cannot see the screen knows why the game closed.
"""
from __future__ import annotations

import argparse
import datetime
import json
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
    """The screen reader speech, or None until it is built (plan 2, section 2) or when it
    cannot start; the game runs without it rather than not at all."""
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


def debug_from_options(options):
    """Whether this run is in debug mode. It never exists in a built game."""
    if not options.debug:
        return False
    if paths.FROZEN:
        log.warning('--debug works only when running from source, so it is ignored')
        return False
    return True


def spiel_from_options(options, debug):
    """The spiel label ``--spiel`` names, when it is allowed and the story has it; or None."""
    if not options.spiel:
        return None
    if not debug:
        log.warning('--spiel works only in debug mode, so it is ignored')
        return None
    with open(paths.bundle(), 'r', encoding='utf-8-sig') as f:
        labels = set(json.load(f).get('labels', {}).values())
    if options.spiel not in labels:
        log.warning('there is no spiel labelled "%s", so it is ignored', options.spiel)
        return None
    return options.spiel


def run_window(pygame, title, exit_after):
    """A plain window until it is closed, Escape is pressed, or ``exit_after`` seconds
    pass. It stands in for the screen loop until plan 2, section 3 builds it."""
    pygame.display.init()
    try:
        pygame.display.set_caption(title)
        pygame.display.set_mode((640, 480))
        clock = pygame.time.Clock()
        started = time.monotonic()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
            if exit_after is not None and time.monotonic() - started >= exit_after:
                log.info('quitting after %g seconds, as --exit-after asked', exit_after)
                return
            clock.tick(60)
    finally:
        pygame.display.quit()


def main(argv=None):
    options = parse_args(argv)
    start_log(options.verbose)
    log.info('Heathcote %s starting, from %s', paths.version(), 'a build' if paths.FROZEN else 'source')
    speech = get_speech()
    try:
        # compiler.py --test looks for this line, to know a build found its data.
        log.info('game data: %s', paths.game())
        debug = debug_from_options(options)
        if debug:
            log.info('debug mode is on')
        spiel = spiel_from_options(options, debug)
        if spiel is not None:
            log.info('the story will start at "%s" once the story engine is built', spiel)
        import pygame
        run_window(pygame, 'Heathcote (debug)' if debug else 'Heathcote', options.exit_after)
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
