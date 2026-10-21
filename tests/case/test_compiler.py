"""compiler.py's own rules, without building anything: the changelog, what a build carries,
the PyInstaller command line, and how --test judges a run."""
import _quiet  # noqa: F401  (first, before the game)

import os
import types

import compiler

FLAGS = dict(embed=False, onefile=False, console=False, clean=False)


def args(**changed):
    return types.SimpleNamespace(**dict(FLAGS, **changed))


def test_an_empty_unrelease_is_taken_out_of_the_shipped_changelog():
    text = 'unrelease:\n\n26.10.21-1:\nThe game opens.\n'
    assert compiler.without_unrelease(text) == '26.10.21-1:\nThe game opens.\n'
    kept = 'unrelease:\nA new thing.\n\n26.10.21-1:\nThe game opens.\n'
    assert compiler.without_unrelease(kept) == kept                 # lines under it are kept
    assert compiler.unreleased_lines(kept) == ['A new thing.']


def test_a_sentence_ending_in_a_colon_is_never_a_heading():
    blocks = compiler.parse_changelog('unrelease:\nThe pause menu has: Resume.\nTab says:\n')
    assert blocks == [['unrelease:', ['The pause menu has: Resume.', 'Tab says:']]]


def test_the_build_carries_the_interface_sounds_and_the_story_but_not_its_recordings():
    src = compiler.game_source()
    assert src is not None
    names = compiler.game_files(src)
    assert names and all(n.startswith(os.path.join('documents', 'Audio', 'System')) or
                         n.startswith(os.path.join('documents', 'text')) for n in names)
    system = os.path.join(src, 'documents', 'Audio', 'System')
    on_disk = sum(len(files) for _root, _dirs, files in os.walk(system))
    assert sum(1 for n in names if n.startswith(os.path.join('documents', 'Audio'))) == on_disk
    assert not any(n.startswith(os.path.join('documents', 'Audio', 'story')) for n in names)
    assert compiler.BUNDLE.replace('/', os.sep) in names
    assert compiler.missing_game_files(src) == []


def test_the_compiler_makes_a_pack_that_reads_back_and_its_fingerprint():
    import json
    import shutil
    from heathcote.platform import pack
    src = os.path.join(_quiet.FOLDER, 'compiler game')
    scene = os.path.join(src, 'documents', 'Audio', 'story', 'scene')
    os.makedirs(scene, exist_ok=True)
    real = os.path.join(compiler.game_source(), 'documents', 'Audio', 'System', 'misc')
    for name in sorted(os.listdir(real))[:2]:
        shutil.copy2(os.path.join(real, name), os.path.join(scene, name))
    dest = os.path.join(_quiet.FOLDER, 'compiler stage', compiler.PACK)
    info = compiler.make_pack(src, dest)
    assert info['files'] == 2 and len(pack.Pack(dest).files) == 2
    game = os.path.join(_quiet.FOLDER, 'compiler build', 'game')
    compiler.write_fingerprint(game, info)
    assert not os.path.exists(os.path.join(game, compiler.FINGERPRINT))   # never at game\'s top
    with open(os.path.join(game, 'documents', 'text', 'system', compiler.FINGERPRINT),
              encoding='utf-8') as fh:
        assert json.load(fh) == {'size': info['size'], 'sha256': info['sha256']}


def test_the_command_carries_both_dlls_prism_and_pyfmodex():
    cmd = compiler.command(args())
    joined = ' '.join(cmd)
    assert 'vendor/fmod/fmod.dll' + os.pathsep + 'vendor/fmod' in joined
    assert 'vendor/nvda/nvdaControllerClient64.dll' + os.pathsep + 'vendor/nvda' in joined
    assert '--collect-all prism' in joined and '--collect-submodules pyfmodex' in joined
    assert '--hidden-import cryptography.hazmat.primitives.ciphers.aead' in joined
    assert '--windowed' in cmd and '--onefile' not in cmd and cmd[-1] == 'Heathcote.py'
    embedded = compiler.command(args(embed=True), embed_game=True)
    assert '--onefile' in embedded and compiler.GAME_STAGE + os.pathsep + 'game' in embedded
    assert '--windowed' not in compiler.command(args(console=True))


def test_the_licences_include_fmods_and_pyfmodexs():
    rels = [rel for rel, _src in compiler.license_files()]
    assert os.path.join('fmod', 'license.txt') in rels
    assert any(r.startswith('pyfmodex' + os.sep) for r in rels)
    assert any(r.startswith('prism' + os.sep) for r in rels)
    assert any(r.startswith('cryptography' + os.sep) for r in rels)


def test_a_missing_fmod_dll_says_where_to_get_it():
    saved = compiler.HERE
    compiler.HERE = os.path.join(_quiet.FOLDER, 'no repo here')
    try:
        found = ' '.join(compiler.problems_now())
    finally:
        compiler.HERE = saved
    assert 'fmod.dll is missing' in found and 'api\\core\\lib\\x64\\fmod.dll' in found


def test_a_good_run_passes_and_each_bad_one_says_why():
    good = ('00:00:01 INFO game data: x\n00:00:01 INFO story story recordings: C:\\x\\story.dat\n'
            '00:00:01 INFO audio FMOD 2.02.35 started\nHeathcote closed\n')
    assert compiler.judge_test(0, good, '') == []
    loose = good.replace('story recordings: C:\\x\\story.dat\n', '')
    assert any('story.dat' in p for p in compiler.judge_test(0, loose, ''))
    assert any('crash report' in p for p in compiler.judge_test(1, good, 'Traceback'))
    assert any('no "game data:"' in p for p in compiler.judge_test(0, 'FMOD x\nHeathcote closed', ''))
    assert any('FMOD started' in p for p in compiler.judge_test(0, 'game data: x\nHeathcote closed', ''))
    assert any('did not close' in p for p in compiler.judge_test(0, 'game data: x\nFMOD x\n', ''))
    assert any('still running' in p for p in compiler.judge_test(None, good, ''))
    assert compiler.judge_test(0, '', '') and 'no log at all' in compiler.judge_test(0, '', '')[0]


def test_the_test_runs_quiet_and_off_the_real_save():
    assert compiler.TEST_QUIET['HEATHCOTE_SILENT'] == '1'
    assert compiler.TEST_QUIET['HEATHCOTE_NOSOUND'] == '1'
    assert compiler.TEST_QUIET['SDL_VIDEODRIVER'] == 'dummy'


def test_every_menu_choice_is_a_command_line_the_parser_takes():
    for _text, flags in compiler.MENU:
        assert set(flags) <= {'--test', '--embed', '--clean', '--console', '--onefile',
                              '--no-game', '--dry-run'}


def test_enter_with_nothing_typed_says_the_menu_again():
    answers = iter(['', 'x', '2'])
    said = []
    saved_input, saved_say = compiler.input if hasattr(compiler, 'input') else None, compiler.say
    compiler.input = lambda prompt='': next(answers)
    compiler.say = lambda text='': said.append(text)
    try:
        assert compiler.menu() == ['--test']
    finally:
        compiler.say = saved_say
        if saved_input is None:
            del compiler.input
        else:
            compiler.input = saved_input
    assert sum(1 for line in said if line.startswith('Heathcote compiler.')) == 2
    assert any(line.startswith('There is no choice "x"') for line in said)


if __name__ == '__main__':
    _quiet.run_tests(globals())
