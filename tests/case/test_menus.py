"""The main loop's keys (heathcote/app.py), the spoken menu, the F1 screen, the stand-in
Settings and main menu, and where each volume key works, driven by key name."""
import _quiet  # noqa: F401  (first, before the game)

import os
import types

from heathcote.app import App
from heathcote.game.menus import MainMenu
from heathcote.platform.keymap import STORY_VOLUMES, KeyMap
from heathcote.platform.runloop import RunLoop
from heathcote.platform.settings import Settings
from heathcote.platform.speech import Speech
from heathcote.ui.keybind_screen import KeyBindScreen
from heathcote.ui.menu import Menu, Row
from heathcote.ui.settings_screen import SettingsScreen

N = [0]


class Listening(Speech):
    """Silent speech that keeps every line, and whether it interrupted."""
    def __init__(self):
        super().__init__()
        self.lines = []

    def speak(self, text, interrupt=True):
        self.lines.append((text, interrupt))
        return super().speak(text, interrupt)


class StoryStandIn(Menu):
    """Takes the story's volume keys, as the story's screens will."""
    name = 'story stand-in'

    def rows(self):
        return [Row('Story')]

    def volume_group(self):
        return STORY_VOLUMES


def make(debug=False):
    N[0] += 1
    folder = os.path.join(_quiet.FOLDER, 'app%d' % N[0])
    app = App(types.SimpleNamespace(debug=debug, exit_after=None), speech=Listening(),
              settings=Settings(os.path.join(folder, 'settings.json')),
              keymap=KeyMap(os.path.join(folder, 'keys.json')), loop=RunLoop())
    return app


def press(app, key, mods=()):
    app.speech.lines.clear()
    app.key_down(key, list(mods))
    return [text for text, _interrupt in app.speech.lines]


def with_main_menu(debug=False):
    app = make(debug)
    app.stack.push(MainMenu(app))
    return app


def test_opening_says_the_title_then_the_row_without_cutting_it_off():
    app = make()
    app.stack.push(MainMenu(app))
    assert app.speech.lines == [('Heathcote.', True), ('Start story', False)]


def test_all_four_arrows_move_and_wrap():
    app = with_main_menu()
    assert press(app, 'down') == ['Settings']
    assert press(app, 'right') == ['Credits']
    assert press(app, 'down') == ['Quit']
    assert press(app, 'down') == ['Start story']       # wraps
    assert press(app, 'left') == ['Quit']              # wraps back
    assert press(app, 'up') == ['Credits']


def test_home_and_end():
    app = with_main_menu()
    assert press(app, 'end') == ['Quit']
    assert press(app, 'home') == ['Start story']


def test_a_key_with_no_use_says_the_row_again():
    app = with_main_menu()
    assert press(app, 'x') == ['Start story']
    assert press(app, 'escape') == ['Start story']     # nothing under the main menu


def test_quit():
    app = with_main_menu()
    press(app, 'end')
    press(app, 'return')
    assert not app.running


def test_settings_opens_on_back_and_back_returns():
    app = with_main_menu()
    press(app, 'down')
    assert press(app, 'return') == ['Settings.', 'Back']
    assert isinstance(app.stack.top, SettingsScreen)
    assert press(app, 'return') == ['Heathcote.', 'Settings']
    assert isinstance(app.stack.top, MainMenu)


def test_debug_mode_turns_on_at_once_and_is_remembered():
    app = with_main_menu()
    press(app, 'down')
    press(app, 'return')
    press(app, 'down')
    assert press(app, 'return') == ['Debug mode, currently on']
    assert app.debug and app.keymap.debug and app.settings.get('debug') is True
    assert app.window_title() == 'Heathcote (debug)'
    press(app, 'return')
    assert not app.debug and app.window_title() == 'Heathcote'


def test_debug_from_the_command_line_is_not_remembered():
    app = make(debug=True)
    assert app.debug and app.settings.get('debug') is False


def test_f1_holds_the_timers_and_resumes_them():
    app = with_main_menu()
    assert press(app, 'f1') == ['Key bindings.', 'Back']
    assert isinstance(app.stack.top, KeyBindScreen) and app.loop.held
    assert press(app, 'f1') == ['Heathcote.', 'Start story']
    assert not app.loop.held


def test_the_f1_screen_keeps_its_own_keys_when_the_menu_keys_are_unbound():
    app = with_main_menu()
    for action in ('menu_previous', 'menu_next', 'menu_choose', 'menu_back'):
        app.keymap.clear(action)
    press(app, 'f1')
    assert press(app, 'down') == ['Menus: previous: nothing']
    assert press(app, 'return') == ['Press the key for Menus: previous.']
    assert press(app, 'up') == ['Menus: previous is now Up Arrow.']


def test_rebinding_says_what_it_took_from():
    app = with_main_menu()
    press(app, 'f1')
    screen = app.stack.top
    screen.index = 1 + app.keymap.actions.index('menu_first')
    press(app, 'return')
    said = press(app, 'home', ['shift'])
    assert said == ['Menus: first is now Shift plus Home. Taken from Master volume up.'], said


def test_escape_and_f1_cannot_be_bound():
    app = with_main_menu()
    press(app, 'f1')
    press(app, 'down')
    press(app, 'return')
    assert press(app, 'escape')[0].startswith('Escape cannot be rebound.')
    assert isinstance(app.stack.top, KeyBindScreen)


def test_reset_asks_first():
    app = with_main_menu()
    app.keymap.clear('pause')
    press(app, 'f1')
    press(app, 'r')
    assert press(app, 'x')[0].startswith('Your bindings are kept.')
    assert app.keymap.bindings['pause'] == []
    press(app, 'r')
    press(app, 'r')
    assert app.keymap.bindings['pause'] == ['escape']


def test_title_volume_and_master_in_the_main_menu():
    app = with_main_menu()
    assert press(app, 'page down') == ['Title volume, 90 percent.']
    assert press(app, 'end', ['shift']) == ['Master volume, 90 percent.']
    assert press(app, 'page down', ['shift']) == ['Start story']   # interface: story only
    assert app.settings.get('interface_volume') == 100


def test_title_volume_in_settings_opened_from_the_main_menu():
    app = with_main_menu()
    press(app, 'down')
    press(app, 'return')
    assert press(app, 'page down') == ['Title volume, 90 percent.']


def test_only_the_master_where_the_title_music_is_silent():
    app = make()
    app.stack.push(Menu(app))                  # such as the pause menu
    assert press(app, 'home', ['shift']) == ['Master volume, 100 percent.']
    assert press(app, 'page down') == ['Nothing here.']
    assert app.settings.get('title_volume') == 100 and app.settings.get('backgrounds_volume') == 100


def test_the_story_volumes_in_the_story():
    app = make()
    app.stack.push(StoryStandIn(app))
    assert press(app, 'page down') == ['Background volume, 90 percent.']
    assert press(app, 'page down', ['shift']) == ['Interface volume, 90 percent.']
    assert press(app, 'end', ['shift']) == ['Master volume, 90 percent.']
    assert app.settings.get('title_volume') == 100


def test_no_volume_keys_on_the_f1_screen():
    app = with_main_menu()
    press(app, 'f1')
    press(app, 'page down')
    assert app.settings.get('title_volume') == 100


def test_a_held_volume_key_repeats_and_stops():
    app = with_main_menu()
    app.key_down('page down', [], now=0.0)
    app.repeat_keys(now=0.3)
    assert app.settings.get('title_volume') == 90       # not yet
    app.repeat_keys(now=0.4)
    app.repeat_keys(now=0.5)
    assert app.settings.get('title_volume') == 70
    app.key_up('page down')
    app.repeat_keys(now=0.6)
    assert app.settings.get('title_volume') == 70


def test_a_held_volume_key_stops_when_the_screen_changes():
    app = with_main_menu()
    app.key_down('page down', [], now=0.0)
    app.title_music = False
    app.stack.push(Menu(app))
    app.repeat_keys(now=0.5)
    assert app.settings.get('title_volume') == 90 and app.held is None


def test_the_opening_gives_the_notice_the_first_time_then_never_again():
    from heathcote.game.opening import NOTICE, NoticeScreen, OpeningScreen
    app = make()
    app.stack.push(OpeningScreen(app))
    assert app.speech.lines == [('Heathcote.', False)]
    app.stack.top.update()                     # no sound here, so the splash is over at once
    assert isinstance(app.stack.top, NoticeScreen)
    assert [t for t, _i in app.speech.lines[1:]] == [NOTICE, 'Press Enter to continue.']
    assert press(app, 'x') == [NOTICE, 'Press Enter to continue.']
    assert app.settings.get('first_run_notice_shown') is False
    assert press(app, 'return') == ['Heathcote.', 'Start story']
    assert isinstance(app.stack.top, MainMenu) and app.title_music
    assert app.settings.get('first_run_notice_shown') is True
    app.stack.reset(OpeningScreen(app))        # the next start
    app.stack.top.update()
    assert isinstance(app.stack.top, MainMenu)


def test_enter_skips_the_splash_and_other_keys_do_not():
    from heathcote.game.opening import NoticeScreen, OpeningScreen
    app = make()
    app.stack.push(OpeningScreen(app))
    app.stack.top.playing = True               # as if the police radio were playing
    app.audio.slot = lambda name: types.SimpleNamespace(playing=True, stop=lambda: None)
    press(app, 'x')
    app.stack.top.update()
    assert isinstance(app.stack.top, OpeningScreen)
    press(app, 'return')
    assert isinstance(app.stack.top, NoticeScreen)


def test_the_notice_names_the_key_that_continues():
    from heathcote.game.opening import NoticeScreen
    app = make()
    app.keymap.bindings['menu_choose'] = ['space']
    screen = NoticeScreen(app)
    assert screen.continue_text() == 'Press Space to continue.'


def test_credits_open_on_back_with_a_row_each_and_fmods_line_last():
    from heathcote.game.credits import CREDITS, CreditsMenu
    app = with_main_menu()
    press(app, 'down')
    press(app, 'down')
    assert press(app, 'return') == ['Credits.', 'Back']
    assert isinstance(app.stack.top, CreditsMenu)
    assert press(app, 'down') == ['Heathcote, version 1.01, by Fabulae Obscurae']
    assert press(app, 'down') == ['Story: Christian Francis, Ben Meares']
    assert press(app, 'return') == ['Story: Christian Francis, Ben Meares']   # said again
    said = press(app, 'end')[0]
    assert 'FMOD' in said and 'Firelight Technologies Pty Ltd.' in said     # its licence's words
    assert 'Windows port: tsatria03' in CREDITS
    assert press(app, 'page down') == ['Title volume, 90 percent.']        # the music plays on
    assert press(app, 'escape') == ['Heathcote.', 'Credits']
    assert isinstance(app.stack.top, MainMenu) and app.title_music


def test_back_in_the_credits_returns_to_the_main_menu():
    from heathcote.game.credits import CreditsMenu
    app = with_main_menu()
    app.stack.push(CreditsMenu(app))
    assert press(app, 'return') == ['Heathcote.', 'Start story']
    assert isinstance(app.stack.top, MainMenu)


def test_the_window_shows_the_rows_and_the_last_line():
    app = with_main_menu()
    assert app.stack.top.lines() == ['Heathcote.', '', '> Start story', '  Settings', '  Credits', '  Quit']
    assert app.speech.last == 'Start story'


if __name__ == '__main__':
    _quiet.run_tests(globals())
