"""Speech (heathcote/platform/speech.py), with stand-ins for NVDA and Prism: nothing here
ever reaches a real screen reader."""
import _quiet  # noqa: F401  (first, before the game)

import types

from heathcote.platform import speech as speech_module
from heathcote.platform.speech import Speech, _Prism


class FakeNvda:
    def __init__(self, running):
        self.is_running = running
        self.said = []
        self.stopped = 0

    def running(self):
        return self.is_running

    def speak(self, text, interrupt):
        if not self.is_running:
            return False
        self.said.append((text, interrupt))
        return True

    def stop(self):
        self.stopped += 1


class FakeBackend:
    def __init__(self, name, runs=True):
        self.name = name
        self.runs = runs
        self.said = []
        self.features = types.SimpleNamespace(is_supported_at_runtime=runs, supports_output=True)

    def output(self, text, interrupt):
        self.said.append((text, interrupt))

    def stop(self):
        pass


class FakeContext:
    def __init__(self, backends):
        self.backends = backends            # id -> backend
        self.backends_count = len(backends)

    def id_of(self, i):
        return list(self.backends)[i]

    def create(self, bid):
        return self.backends[bid]


IDS = types.SimpleNamespace(**{name: i for i, name in enumerate(speech_module.READERS + speech_module.VOICES)})


def prism_with(backends, narrator=False, clock=lambda: 0.0):
    ctx = FakeContext({getattr(IDS, name): b for name, b in backends.items()})
    return _Prism(loader=lambda: (ctx, IDS), narrator_running=lambda: narrator, clock=clock)


class NoPrism:
    """Fails if Prism is ever asked for, to show NVDA never loads it."""
    def __getattr__(self, name):
        raise AssertionError('Prism was used while NVDA was running')


def test_silent_says_nothing_but_remembers_the_line():
    s = Speech()
    assert s.silent
    assert s.speak('hello') is False
    assert s.last == 'hello' and s.which == 'none'


def test_nvda_first_and_prism_never_loaded():
    nvda = FakeNvda(True)
    s = Speech(nvda=nvda, prism=NoPrism())
    assert s.speak('one') and s.speak('two', interrupt=False)
    assert nvda.said == [('one', True), ('two', False)]
    assert s.which == 'NVDA'


def test_another_screen_reader_through_prism():
    jaws = FakeBackend('JAWS')
    s = Speech(nvda=FakeNvda(False), prism=prism_with({'JAWS': jaws, 'SAPI': FakeBackend('SAPI')}))
    assert s.speak('hello')
    assert jaws.said == [('hello', True)]


def test_a_voice_when_no_screen_reader_runs():
    sapi = FakeBackend('SAPI')
    s = Speech(nvda=FakeNvda(False), prism=prism_with({'JAWS': FakeBackend('JAWS', runs=False), 'SAPI': sapi}))
    assert s.speak('hello')
    assert sapi.said == [('hello', True)]


def test_narrator_only_when_windows_says_it_runs():
    uia = FakeBackend('UIA')
    sapi = FakeBackend('SAPI')
    s = Speech(nvda=FakeNvda(False), prism=prism_with({'UIA': uia, 'SAPI': sapi}, narrator=False))
    s.speak('hello')
    assert uia.said == [] and sapi.said == [('hello', True)]


def test_without_prism_nvda_carries_on_alone():
    def broken():
        raise ImportError('no prism')
    p = _Prism(loader=broken)
    assert p.current_reader() is None and p.current_voice() is None
    s = Speech(nvda=FakeNvda(False), prism=p)
    assert s.speak('hello') is False


if __name__ == '__main__':
    _quiet.run_tests(globals())
