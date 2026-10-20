"""Try the game's speech and timer loop by ear (aidocks/plans/foundation_plan.md, section 2).

    python tests/interact/speech_check.py

It speaks through whatever the game would use: NVDA, another screen reader through
Prism, or a Windows voice. The keys:

    Enter    say what is speaking, such as NVDA
    1        a line that cuts off what is being said, as a key press does
    2        a line that waits its turn, as a line the game says by itself does
    T        count down 3, 2, 1 on the timer loop, then say "Done"
    P        hold the timer loop, or resume it; a held countdown carries on where it was
    S        stop speaking
    Escape   quit

It keeps its own save under %APPDATA%\\Heathcote\\interact\\speech_check, so the log
never touches the game's own.
"""
from __future__ import annotations

import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
os.environ.setdefault('HEATHCOTE_USER_DIR', os.path.join(
    os.environ.get('APPDATA') or os.path.expanduser('~'), 'Heathcote', 'interact', 'speech_check'))

import pygame  # noqa: E402

from heathcote import paths  # noqa: E402
from heathcote.platform.runloop import RunLoop  # noqa: E402
from heathcote.platform.speech import Speech  # noqa: E402

LONG_LINE = ('This is a long line, so you can hear whether the next key press cuts it off, '
             'or waits for it to finish before speaking.')


def main():
    logging.basicConfig(filename=os.path.join(paths.logs_dir(), 'log.txt'), filemode='w',
                        level=logging.DEBUG, encoding='utf-8',
                        format='%(asctime)s %(levelname)-7s %(name)-9s %(message)s')
    speech = Speech.shared()
    loop = RunLoop.main()
    countdown = []

    def stop_countdown():
        for call in countdown:
            call.cancel()
        countdown.clear()

    def count_down():
        stop_countdown()
        speech.speak('Counting down.')
        for n, word in enumerate(('3', '2', '1'), start=1):
            countdown.append(loop.after(n, speech.speak, word))
        countdown.append(loop.after(4, speech.speak, 'Done.'))

    pygame.display.init()
    pygame.display.set_caption('Heathcote speech check')
    pygame.display.set_mode((640, 480))
    speech.speak('Speech check. Speaking through %s. Press Escape to quit.' % speech.which)
    clock = pygame.time.Clock()
    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type != pygame.KEYDOWN:
                    continue
                key = event.key
                if key == pygame.K_ESCAPE:
                    return
                if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    speech.speak('Speaking through %s.' % speech.which)
                elif key == pygame.K_1:
                    speech.speak(LONG_LINE)
                elif key == pygame.K_2:
                    speech.speak('This line waited its turn.', interrupt=False)
                elif key == pygame.K_t:
                    count_down()
                elif key == pygame.K_p:
                    if loop.held:
                        loop.resume()
                        speech.speak('Resumed.')
                    else:
                        loop.hold()
                        speech.speak('Held.')
                elif key == pygame.K_s:
                    speech.stop()
            loop.pump()
            clock.tick(60)
    finally:
        stop_countdown()
        pygame.display.quit()


if __name__ == '__main__':
    main()
