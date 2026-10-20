"""Every key the player uses, and their changes from the F1 screen.

The actions and their default keys are the ones agreed in aidocks/plans/foundation_plan.md,
aidocks/plans/story_engine_plan.md and aidocks/plans/audio_plan.md. Every one is
rebindable, the arrows included (the dev, 2026-10-19: "I want the arrow keys to be
rebindable, so yes."). Only the F1 screen's own keys are fixed, so there is always a way
to put the others right.

Each action belongs to a group, by where it works:

    menu           every spoken menu, the story's actions menu included
    story          while the story plays
    story volumes  the master, background and interface volumes: in the story only, its
                   actions menu included
    title volume   the title volume: only where the title music plays, such as the main menu

(the dev, 2026-10-19: "Page up/down can adjust this, but only when the music plays
there. Also, the other volume keys should only work when you are in the actual game.")

The same key can do one thing in one place and another elsewhere, as Up, Escape and Page
Up do, so a key clashes only with actions that can be pressed in the same place
(``CLASHES``).

A binding is one key with any of Shift, Control and Alt, written as pygame names it with
the modifiers first, such as ``"page up"`` or ``"shift+page up"``. It matches only with
exactly those modifiers held, so Page Up and Shift+Page Up never both fire. Left and right
Shift count the same.

Keys are stored by name, not keycode, so a saved keymap survives a pygame update, in
``config/keys.json`` in the save folder, written safely like every other file there.
"""
from __future__ import annotations

import logging

from .. import paths
from .files import JsonFile

log = logging.getLogger('keymap')

MENU, STORY, STORY_VOLUMES, TITLE_VOLUME = 'menu', 'story', 'story volumes', 'title volume'
#: The pairs of groups that can be pressed in the same place, besides a group with itself:
#: the story volumes during the story and in its actions menu, and the title volume in the
#: menus the title music plays under.
CLASHES = {frozenset((STORY_VOLUMES, STORY)), frozenset((STORY_VOLUMES, MENU)),
           frozenset((TITLE_VOLUME, MENU))}

#: (action, group, what the F1 screen calls it, default bindings). Debug actions work only
#: in debug mode, and the F1 screen lists them only then.
ACTIONS = (
    ('menu_previous', MENU, 'Menus: previous', ('up', 'left')),
    ('menu_next', MENU, 'Menus: next', ('down', 'right')),
    ('menu_first', MENU, 'Menus: first', ('home',)),
    ('menu_last', MENU, 'Menus: last', ('end',)),
    ('menu_choose', MENU, 'Menus: choose', ('return', 'enter')),
    ('menu_back', MENU, 'Menus: back, or close the actions menu', ('escape',)),
    ('choice_text', MENU, "Actions menu: say the choice's text", ('space',)),
    ('actions_menu', STORY, 'Story: open the actions menu', ('up', 'return', 'enter')),
    ('rewind', STORY, 'Story: rewind', ('left',)),
    ('fast_forward', STORY, 'Story: fast-forward', ('right',)),
    ('pause', STORY, 'Story: pause', ('escape',)),
    ('where', STORY, 'Story: say where you are', ('tab',)),
    ('debug_skip', STORY, 'Debug: skip to the end of the spiel', ('f2',)),
    ('debug_jump', STORY, 'Debug: jump to a spiel', ('f3',)),
    ('debug_variables', STORY, 'Debug: say the variables', ('f4',)),
    ('master_up', STORY_VOLUMES, 'Story: master volume up', ('shift+home',)),
    ('master_down', STORY_VOLUMES, 'Story: master volume down', ('shift+end',)),
    ('backgrounds_up', STORY_VOLUMES, 'Story: background volume up', ('page up',)),
    ('backgrounds_down', STORY_VOLUMES, 'Story: background volume down', ('page down',)),
    ('interface_up', STORY_VOLUMES, 'Story: interface volume up', ('shift+page up',)),
    ('interface_down', STORY_VOLUMES, 'Story: interface volume down', ('shift+page down',)),
    ('title_up', TITLE_VOLUME, 'Title music: title volume up', ('page up',)),
    ('title_down', TITLE_VOLUME, 'Title music: title volume down', ('page down',)),
)

ACTION_IDS = [a[0] for a in ACTIONS]
DEBUG_IDS = [a for a in ACTION_IDS if a.startswith('debug_')]
GROUPS = {a[0]: a[1] for a in ACTIONS}
LABELS = {a[0]: a[2] for a in ACTIONS}
DEFAULTS = {a[0]: list(a[3]) for a in ACTIONS}

#: Never rebindable: they are the F1 screen's way in and out.
FIXED = {'f1': 'Key bindings, from anywhere', 'escape': 'Leave the key bindings'}

MODIFIERS = ('shift', 'ctrl', 'alt')
#: pygame's names for the modifier keys themselves, which are never a binding on their own.
MODIFIER_KEYS = {'left shift', 'right shift', 'left ctrl', 'right ctrl', 'left alt',
                 'right alt', 'left meta', 'right meta', 'left super', 'right super',
                 'caps lock', 'num lock', 'scroll lock', 'mode', 'compose', 'menu'}

#: pygame's terse names, as they should be spoken.
SPOKEN = {
    'left': 'Left Arrow', 'right': 'Right Arrow', 'up': 'Up Arrow', 'down': 'Down Arrow',
    'space': 'Space', 'tab': 'Tab', 'escape': 'Escape', 'return': 'Enter', 'enter': 'Keypad Enter',
    'shift': 'Shift', 'ctrl': 'Control', 'alt': 'Alt',
    ',': 'Comma', '.': 'Full stop', '/': 'Slash', ';': 'Semicolon', "'": 'Apostrophe',
    '[': 'Left bracket', ']': 'Right bracket', '\\': 'Backslash', '-': 'Minus',
    '=': 'Equals', '`': 'Backtick', 'backspace': 'Backspace', 'delete': 'Delete',
    'home': 'Home', 'end': 'End', 'page up': 'Page Up', 'page down': 'Page Down',
    'insert': 'Insert',
}


def binding(key, mods=()):
    """The binding for a key pressed with these modifiers, such as ``shift+page up``."""
    held = [m for m in MODIFIERS if m in set(mods)]
    return '+'.join(held + [key])


def mods_from_pygame(mod_state, pygame):
    """The modifiers held, from pygame's ``event.mod``."""
    held = []
    if mod_state & pygame.KMOD_SHIFT:
        held.append('shift')
    if mod_state & pygame.KMOD_CTRL:
        held.append('ctrl')
    if mod_state & pygame.KMOD_ALT:
        held.append('alt')
    return held


def key_text(name):
    """One key name as it should be spoken."""
    if name in SPOKEN:
        return SPOKEN[name]
    if len(name) == 1:
        return name.upper()
    return name.title()


def binding_text(b):
    """A binding as it should be spoken: 'Shift plus Page Up'."""
    return ' plus '.join(key_text(part) for part in b.split('+') if part)


def bindings_text(bindings):
    if not bindings:
        return 'nothing'
    return ', or '.join(binding_text(b) for b in bindings)


def clashes(group, other):
    """Whether actions in these two groups can be pressed at the same moment."""
    return group == other or frozenset((group, other)) in CLASHES


def _clean(saved):
    """The bindings a file gives an action, keeping only strings that name a key."""
    if not isinstance(saved, list):
        return None
    return [b for b in saved if isinstance(b, str) and b and not b.endswith('+')]


class KeyMap:
    _shared = None

    @classmethod
    def shared(cls):
        if cls._shared is None:
            cls._shared = KeyMap()
        return cls._shared

    def __init__(self, path=None):
        self.file = JsonFile(path or paths.user_path('config', 'keys.json'), order=ACTION_IDS)
        self.bindings = {a: list(DEFAULTS[a]) for a in ACTION_IDS}
        self.debug = False          # debug mode: the debug_ actions are live
        changed = self.file.recovered
        for action in ACTION_IDS:
            saved = _clean(self.file.data.get(action))
            if saved is None:
                changed = True      # a new action, or one the file got wrong
            else:
                self.bindings[action] = saved
        if changed:
            self.save()

    @property
    def actions(self):
        """The actions in play: every one in debug mode, the debug_ ones left out otherwise."""
        if self.debug:
            return list(ACTION_IDS)
        return [a for a in ACTION_IDS if a not in DEBUG_IDS]

    def save(self):
        self.file.data = {a: list(self.bindings[a]) for a in ACTION_IDS}
        self.file.write()

    def reset(self):
        self.bindings = {a: list(DEFAULTS[a]) for a in ACTION_IDS}
        self.save()

    def label(self, action):
        return LABELS[action]

    def keys_text(self, action):
        return bindings_text(self.bindings.get(action, []))

    def action_for(self, key, mods=(), group=MENU):
        """The action in ``group`` that a key pressed with these modifiers does, or None."""
        b = binding(key, mods)
        for action in self.actions:
            if GROUPS[action] == group and b in self.bindings[action]:
                return action
        return None

    def conflicts(self, b, action):
        """The actions that would clash with giving ``action`` this binding."""
        group = GROUPS[action]
        return [a for a in ACTION_IDS
                if a != action and clashes(group, GROUPS[a]) and b in self.bindings[a]]

    def set_binding(self, action, b, replace=True):
        """Give ``action`` this binding, taking it off whatever would clash with it."""
        for other in self.conflicts(b, action):
            self.bindings[other] = [x for x in self.bindings[other] if x != b]
        if replace:
            self.bindings[action] = [b]
        elif b not in self.bindings[action]:
            self.bindings[action] = self.bindings[action] + [b]
        self.save()

    def clear(self, action):
        self.bindings[action] = []
        self.save()
