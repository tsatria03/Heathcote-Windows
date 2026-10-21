"""A spoken search: type part of a name, and Enter finds it (aidocks/plans/story_engine_plan.md,
section 5, for debug mode's F3).

    Letters, digits and spaces   added to the text, each spoken as it is typed, since a screen
                                 reader cannot echo typing into the game's window
    Backspace                    takes the last one off, speaking it
    Enter                        finds: the first name holding the text, in any case; the same
                                 text again moves on to the next match
    Escape                       gives up

It is the same search as tests/interact/audio_check.py's S key. The keys here are fixed, not
from the key map, since they type.
"""
from __future__ import annotations

from .screens import Screen


class SearchScreen(Screen):
    name = 'search'

    def __init__(self, app, prompt, names, found, last=None):
        """``names`` is [(name, item)]; ``found(item, name, match_number, matches)`` is
        called with what Enter finds; ``last`` is (text, index) of the search before, so the
        same text moves on."""
        super().__init__(app)
        self.prompt = prompt
        self.names = names
        self.found = found
        self.last = last
        self.text = ''
        self.result = None              # (text, index) of what was found, for the next search

    def opened(self):
        self.say(self.prompt)

    def speak_char(self, char):
        self.say(char if char.strip() else 'space')

    def handle_key(self, key, mods):
        if key == 'escape':
            self.stack.pop()
            self.say('Search cancelled.')
        elif key in ('return', 'enter'):
            self.find()
        elif key == 'backspace':
            if self.text:
                gone, self.text = self.text[-1], self.text[:-1]
                self.speak_char(gone)
        else:
            char = self.app.last_char
            if char and char.isprintable():
                self.text += char
                self.speak_char(char)
        return True

    def find(self):
        text = self.text.strip().lower()
        if not text:
            self.say('Nothing typed.')
            return
        matches = [i for i, (name, _item) in enumerate(self.names) if text in name.lower()]
        if not matches:
            self.say('Nothing has "%s" in its name.' % text)
            return
        index = matches[0]
        if self.last and self.last[0] == text:
            later = [i for i in matches if i > self.last[1]]
            index = later[0] if later else matches[0]
        self.result = (text, index)
        name, item = self.names[index]
        self.stack.pop()
        self.found(item, name, matches.index(index) + 1, len(matches))

    def lines(self):
        return [self.prompt, '', 'Find: %s' % self.text]
