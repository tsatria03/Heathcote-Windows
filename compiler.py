"""Build Heathcote into Heathcote.exe with PyInstaller.

Section 1 of aidocks/plans/build_release_plan.md. It builds into dist\\Heathcote-Windows,
around Heathcote.exe, and nothing else: it never zips and never changes the repository.
Setting the version, filing the changelog, zipping, tagging and uploading are releaser.py's
work, and the releaser calls this to build.

Double-click this file, or run python compiler.py with nothing after it, and it offers a
numbered menu, then waits for Enter at the end so you can hear how it went. Each choice is
one command line, which still works typed out:

    python compiler.py                    the folder build
    python compiler.py --test             the folder build, then started silently to check it
    python compiler.py --embed            a single exe, the game's data inside it
    python compiler.py --embed --test     the single exe, then started silently to check it
    python compiler.py --clean            empty PyInstaller's cache first
    python compiler.py --console          keep a console window, to see why it will not start
    python compiler.py --onefile          one exe, the game's data still beside it
    python compiler.py --no-game          leave the game's data out
    python compiler.py --dry-run          say what a build would do, build nothing

What a build carries:

* inside the exe, or the folder of Python files beside it: the game's code, pygame, Prism
  with its native part, pyfmodex, cryptography, FMOD's fmod.dll and the NVDA client, with
  the third-party licences as licenses\\;
* story.dat beside the exe: every file of game\\documents\\Audio\\story, the story's
  recordings, packed and encrypted (heathcote/platform/pack.py), made fresh by each build
  and every recording read back to check it (the dev, 2026-10-21: "I did not want the exe
  file to be too big if embedded.");
* the rest of the game's data, beside the exe in game\\, or inside it with --embed: only
  what the game reads, the interface sounds in game\\documents\\Audio\\System and the story
  in game\\documents\\text, with story_pack.json, story.dat's size and SHA-256, so the game
  knows its own pack. Nothing else of the original's app bundle: not its binary, its
  images or its certificates;
* beside the exe, always: docks\\ (the readme, the changelog and the todo list), VERSION,
  and the port's licence as license.txt.

fmod.dll is not in the repository (aidocks/general/project_fmod.md): copy it into
vendor\\fmod\\ from the FMOD Engine install before building, or the build stops and says so.

--test starts the finished build for a few seconds with --exit-after, silently, with no
window or sound device and on a throwaway save, and reads the log it wrote: it must find
its game data, open story.dat, start FMOD, close by itself and leave no crash.txt.
"""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.metadata
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = 'Heathcote'
ENTRY = NAME + '.py'
EXE = NAME + '.exe'
#: The folder a build lands in, and the one a release's zip extracts to.
FOLDER = NAME + '-Windows'

#: What the game cannot run without: the module, and what pip calls it.
PLAY_PACKAGES = (('pygame', 'pygame'), ('prism', 'prismatoid'), ('pyfmodex', 'pyfmodex'),
                 ('cryptography', 'cryptography'))
#: The vendored DLLs, and the folder each goes to inside the build (heathcote/paths.py).
BINARIES = (('vendor/nvda/nvdaControllerClient64.dll', 'vendor/nvda'),
            ('vendor/fmod/fmod.dll', 'vendor/fmod'))
FMOD_DLL = 'vendor/fmod/fmod.dll'
#: The game's data a build carries, inside game\: the folders the game reads, whole, less
#: the story's recordings, which go into story.dat instead.
GAME_DATA = ('documents/Audio', 'documents/text')
#: The folder story.dat packs (heathcote/platform/pack.py), left out of game\.
PACKED = 'documents/Audio/story'
PACK = 'story.dat'
#: The pack's fingerprint, inside the build's game\ (heathcote/paths.py).
FINGERPRINT = 'story_pack.json'
#: The file that tells the game its data is there (heathcote/paths.py).
BUNDLE = 'documents/text/system/Heathcote v1.01.bundle.json'

#: The documents a player reads, copied beside the exe: what it is called here, and there.
#: LICENSE has no extension, so it ships as a .txt that Windows opens by itself.
DOCKS = 'docks'
CHANGELOG = os.path.join(DOCKS, 'changelog.txt')
SIDE_FILES = ((os.path.join(DOCKS, 'readme.txt'), os.path.join(DOCKS, 'readme.txt')),
              (CHANGELOG, CHANGELOG),
              (os.path.join(DOCKS, 'todo list.txt'), os.path.join(DOCKS, 'todo list.txt')),
              ('VERSION', 'VERSION'),
              ('LICENSE', 'license.txt'))
#: The packages whose own licences, from their installed copy, go inside the build.
LICENSED_PACKAGES = (('prismatoid', 'prism'), ('cffi', 'cffi'), ('pyfmodex', 'pyfmodex'),
                     ('cryptography', 'cryptography'))

#: Where a build gathers what PyInstaller takes as whole folders.
STAGE = os.path.join(HERE, 'build', 'stage')
GAME_STAGE = os.path.join(STAGE, 'game')
LICENSES_STAGE = os.path.join(STAGE, 'licenses')
PACK_STAGE = os.path.join(STAGE, PACK)


def say(text: str = '') -> None:
    print(text, flush=True)


def build_version() -> str:
    """The one line in VERSION, or '' when there is no such file."""
    try:
        with open(os.path.join(HERE, 'VERSION'), encoding='utf-8-sig') as fh:
            return fh.read().strip().splitlines()[0].strip()
    except (OSError, IndexError):
        return ''


# --- the changelog ---------------------------------------------------------------------
# docks\changelog.txt collects what has changed under "unrelease:", at the top. releaser.py
# files those lines under the version it releases; the compiler only reads the changelog,
# and takes an empty unrelease: out of the copy it ships. The parsing lives here, where both
# use it.

UNRELEASE = 'unrelease:'
#: A heading is one word ending in a colon, such as "unrelease:" or "26.10.21-1:". The
#: entries are sentences, so a line with a space in it is never taken for one.
_HEADING = re.compile(r'^[^\s:]+:$')


def changelog_heading(version: str) -> str:
    return version + ':'


def parse_changelog(text: str) -> list:
    """[[heading, [lines]], ...] in the file's order. Blank lines only separate one version
    from the next, so they are not kept."""
    blocks = []
    for line in text.replace('\r\n', '\n').split('\n'):
        if _HEADING.match(line.strip()):
            blocks.append([line.strip(), []])
        elif line.strip():
            if not blocks:
                blocks.append([None, []])
            blocks[-1][1].append(line)
    return blocks


def render_changelog(blocks: list) -> str:
    """Each heading and its lines, with a blank line before the next heading."""
    return '\n\n'.join('\n'.join(([heading] if heading else []) + lines)
                       for heading, lines in blocks) + '\n'


def unreleased_lines(text: str) -> list:
    """The lines under unrelease:, the changes no release has carried yet."""
    return next((lines for heading, lines in parse_changelog(text) if heading == UNRELEASE), [])


def without_unrelease(text: str) -> str:
    """The changelog a player reads: less an empty unrelease:, so it opens on the newest
    version. One with lines under it is kept, rather than lose them."""
    return render_changelog([b for b in parse_changelog(text)
                             if not (b[0] == UNRELEASE and not b[1])])


def strip_shipped_changelog(dest_root: str) -> None:
    """Take an empty unrelease: out of the build's copy of the changelog, the copy only."""
    path = os.path.join(dest_root, CHANGELOG)
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(without_unrelease(text))


def release_warnings(changelog: str) -> list:
    """What would make this build a bad one to release."""
    found = []
    if not build_version():
        found.append('there is no VERSION file, so a release would have no version')
    try:
        with open(changelog, encoding='utf-8') as fh:
            first = fh.readline().strip()
        if first == UNRELEASE:
            found.append('the changelog in this build still opens with "%s", since only '
                         'releaser.py files it under a version' % UNRELEASE)
    except OSError:
        found.append('there is no changelog.txt, so the release notes would be empty')
    return found


# --- what goes in ------------------------------------------------------------------------

def problems_now() -> list:
    """Everything that would stop a build, in plain words."""
    found = []
    if sys.platform != 'win32':
        found.append('this builds on Windows only, and this is %s' % sys.platform)
    if sys.maxsize <= 2 ** 32:
        found.append('use 64-bit Python: the NVDA client and fmod.dll are 64-bit')
    if importlib.util.find_spec('PyInstaller') is None:
        found.append('PyInstaller is not installed in this Python: pip install pyinstaller')
    absent = [pip for mod, pip in PLAY_PACKAGES if importlib.util.find_spec(mod) is None]
    if absent:
        found.append("the game's packages have to be installed here too, to be bundled: "
                     'pip install ' + ' '.join(absent))
    for src, _ in BINARIES:
        if os.path.isfile(os.path.join(HERE, src.replace('/', os.sep))):
            continue
        if src == FMOD_DLL:
            found.append('vendor\\fmod\\fmod.dll is missing. It is not in the repository: install '
                         'the FMOD Engine 2.02.35 for Windows from fmod.com, and copy '
                         'api\\core\\lib\\x64\\fmod.dll from its install into vendor\\fmod\\')
        else:
            found.append('%s is missing; it ships with the repository' % src)
    return found


def package_folder(module: str):
    """Where an installed package's own folder is, or None."""
    spec = importlib.util.find_spec(module)
    if spec is None or not spec.submodule_search_locations:
        return None
    return list(spec.submodule_search_locations)[0]


def prism_native_modules() -> list:
    """Prism's compiled module in its prism\\_native folder, which --collect-all leaves
    behind, since the folder is not a package."""
    folder = package_folder('prism')
    folder = os.path.join(folder, '_native') if folder else None
    if not folder or not os.path.isdir(folder):
        return []
    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    return sorted(os.path.join(folder, n) for n in os.listdir(folder) if n.endswith(suffixes))


def game_source():
    """The repository's game\\ folder, when it holds the game's data, or None."""
    folder = os.path.join(HERE, 'game')
    return folder if os.path.isfile(os.path.join(folder, BUNDLE.replace('/', os.sep))) else None


def game_files(src: str) -> list:
    """Every file of the game's data a build carries, as a path inside game\\: all of
    GAME_DATA but the story's recordings, which go into story.dat."""
    packed = os.path.join(src, PACKED.replace('/', os.sep))
    found = []
    for folder in GAME_DATA:
        top = os.path.join(src, folder.replace('/', os.sep))
        for root, dirs, names in os.walk(top):
            dirs[:] = [d for d in dirs if os.path.join(root, d) != packed]
            for name in names:
                found.append(os.path.relpath(os.path.join(root, name), src))
    return sorted(found)


def packed_folder(src: str) -> str:
    return os.path.join(src, PACKED.replace('/', os.sep))


def missing_game_files(src: str) -> list:
    """The game's data a build needs and the repository lacks."""
    return [folder + '/' for folder in GAME_DATA + (PACKED,)
            if not os.path.isdir(os.path.join(src, folder.replace('/', os.sep)))]


def data_summary(src: str, names: list) -> str:
    """'624 files, 2 MB: 16 interface sounds and 608 story files'."""
    sounds = sum(1 for n in names if n.lower().endswith('.mp3'))
    size = sum(os.path.getsize(os.path.join(src, n)) for n in names)
    return '{:,} files, {:.0f} MB: {:,} interface sounds and {:,} story files'.format(
        len(names), size / 1e6, sounds, len(names) - sounds)


def pack_summary(src: str) -> str:
    """'206 story recordings, 157 MB'."""
    from heathcote.platform import pack
    files = pack.recordings(packed_folder(src))
    return '{:,} story recordings, {:.0f} MB'.format(len(files), sum(os.path.getsize(f) for f in files) / 1e6)


def make_pack(src: str, dest: str) -> dict:
    """story.dat from the story's recordings, every one read back and compared with its
    file; its fingerprint. Raises RuntimeError when one does not read back."""
    from heathcote.platform import pack
    root = packed_folder(src)
    started = time.perf_counter()
    marks = set()

    def progress(count, total):
        quarter = count * 4 // total
        if quarter not in marks and count < total:
            marks.add(quarter)
            if quarter:
                say('  %d of %d recordings packed ...' % (count, total))
    info = pack.write_pack(root, dest, progress)
    opened = pack.Pack(dest)
    for path in pack.recordings(root):
        name = pack.recording_name(path, root)
        with open(path, 'rb') as fh:
            if opened.read(name) != fh.read():
                raise RuntimeError('%s did not read back from %s as it was packed' % (name, PACK))
    say('%s is made and checked: %d recordings, %.0f MB, in %.0f seconds.'
        % (PACK, info['files'], info['size'] / 1e6, time.perf_counter() - started))
    return info


def write_fingerprint(game_dest: str, info: dict) -> None:
    """The pack's size and SHA-256, in the build's game\\, so the game knows its own pack."""
    import json
    os.makedirs(game_dest, exist_ok=True)
    with open(os.path.join(game_dest, FINGERPRINT), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'size': info['size'], 'sha256': info['sha256']}, fh, indent=1)
        fh.write('\n')


def copy_game(src: str, dest_game: str) -> list:
    """Copy the game's data into ``dest_game``, keeping its folders."""
    names = game_files(src)
    for name in names:
        target = os.path.join(dest_game, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(os.path.join(src, name), target)
    return names


def license_files() -> list:
    """Every third-party licence a build carries: (where under licenses\\, where from).

    FMOD's and the NVDA client's sit beside their DLLs in vendor\\. Every package's comes
    out of its installed copy's dist-info, whether in its licenses\\ folder or, for older
    packages such as pyfmodex, as a LICENSE file at the top of it, so a build carries the
    licences of what it bundled. pygame's LGPL is in its own docs. A file with no extension
    gets .txt, so Windows opens it."""
    found = [(os.path.join('fmod', 'license.txt'), os.path.join(HERE, 'vendor', 'fmod', 'license.txt')),
             (os.path.join('nvda-controller-client', 'license.txt'),
              os.path.join(HERE, 'vendor', 'nvda', 'license.txt'))]
    for dist_name, folder in LICENSED_PACKAGES:
        try:
            dist = importlib.metadata.distribution(dist_name)
        except importlib.metadata.PackageNotFoundError:
            found.append((os.path.join(folder, 'LICENSE.txt'), ''))       # reported as missing
            continue
        own = []
        for entry in dist.files or ():
            parts = entry.parts
            if not parts[0].endswith('.dist-info'):
                continue
            if len(parts) > 2 and parts[1] == 'licenses':
                rel = os.path.join(folder, *parts[2:])
            elif len(parts) == 2 and parts[1].upper().startswith(('LICENSE', 'LICENCE', 'COPYING')):
                rel = os.path.join(folder, parts[1])
            else:
                continue
            if not os.path.splitext(rel)[1]:
                rel += '.txt'
            own.append((rel, str(dist.locate_file(entry))))
        found += own or [(os.path.join(folder, 'LICENSE.txt'), '')]
    pygame = package_folder('pygame')
    found.append((os.path.join('pygame', 'LGPL.txt'),
                  os.path.join(pygame, 'docs', 'generated', 'LGPL.txt') if pygame else ''))
    return found


LICENSED = 'FMOD, the NVDA client, Prism, cffi, pyfmodex, cryptography and pygame'


def stage_licenses() -> int:
    """The third-party licences, gathered fresh into LICENSES_STAGE."""
    if os.path.isdir(LICENSES_STAGE):
        shutil.rmtree(LICENSES_STAGE)
    os.makedirs(LICENSES_STAGE)
    copied = 0
    for rel, src in license_files():
        if not src or not os.path.isfile(src):
            say('  the licence %s was not found, so it was not copied.' % rel)
            continue
        target = os.path.join(LICENSES_STAGE, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(src, target)
        copied += 1
    say('%d licence files, of %s, go inside the build as licenses%s.' % (copied, LICENSED, os.sep))
    return copied


# --- the command -------------------------------------------------------------------------

def one_file(args) -> bool:
    return bool(args.onefile or args.embed)


def output_dir() -> str:
    """dist\\Heathcote-Windows, whichever kind of build."""
    return os.path.join(HERE, 'dist', FOLDER)


def pyinstaller_dir() -> str:
    """Where PyInstaller makes a folder build, named after the exe; moved to output_dir()."""
    return os.path.join(HERE, 'dist', NAME)


def command(args, embed_game=False) -> list:
    """The PyInstaller command line."""
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--noupx', '--name', NAME]
    for src, dest in BINARIES:
        cmd += ['--add-binary', src + os.pathsep + dest]
    # Prism is imported only once NVDA is found not to be running, so it is named outright,
    # with its compiled half and cffi's, which nothing names either.
    cmd += ['--collect-all', 'prism', '--hidden-import', '_cffi_backend']
    for src in prism_native_modules():
        cmd += ['--add-binary', src + os.pathsep + 'prism/_native']
    # pyfmodex is imported only once fmod.dll is found (platform/audio.py), and loads its
    # own modules by name, so every one of them is named outright.
    cmd += ['--hidden-import', 'pyfmodex', '--collect-submodules', 'pyfmodex']
    # story.dat's cipher is imported only when the pack is first opened (platform/pack.py).
    cmd += ['--hidden-import', 'cryptography.hazmat.primitives.ciphers.aead']
    if not args.console:
        cmd += ['--windowed']
    if one_file(args):
        # The one file lands in dist\Heathcote-Windows too, so every build is one folder.
        cmd += ['--onefile', '--distpath', output_dir()]
    if embed_game:
        cmd += ['--add-data', GAME_STAGE + os.pathsep + 'game']
    cmd += ['--add-data', LICENSES_STAGE + os.pathsep + 'licenses']
    if args.clean:
        cmd += ['--clean']
    return cmd + [ENTRY]


def clear_output(dest_root: str) -> None:
    """Empty the build's folder and PyInstaller's own first, so no older file stays."""
    for folder in (dest_root, pyinstaller_dir()):
        if os.path.isdir(folder):
            shutil.rmtree(folder)


def move_folder_build(dest_root: str) -> None:
    built = pyinstaller_dir()
    if os.path.isdir(built):
        os.replace(built, dest_root)


def copy_side_files(dest_root: str) -> None:
    """The text a player reads, beside the exe: docks\\, VERSION and the licence."""
    for name, shipped_as in SIDE_FILES:
        src = os.path.join(HERE, name)
        if not os.path.isfile(src):
            say('  %s is not here, so it was not copied.' % name)
            continue
        target = os.path.join(dest_root, shipped_as)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(src, target)
        say('%s is in the build%s.' % (shipped_as, '' if shipped_as == name else ', from %s' % name))


# --- the test ----------------------------------------------------------------------------
# --test starts the build it has just made, for TEST_SECONDS, and reads the log the game
# wrote. It runs as the tests do: silent, with no sound device, no window and a throwaway
# save, so it never speaks, plays or touches a player's save.

TEST_SECONDS = 6
#: Long enough for a single exe to unpack itself, 150 MB of recordings included, and start.
TEST_TIMEOUT = 180
TEST_QUIET = {'HEATHCOTE_SILENT': '1', 'HEATHCOTE_NOSOUND': '1',
              'SDL_AUDIODRIVER': 'dummy', 'SDL_VIDEODRIVER': 'dummy'}


def read_log(save: str):
    """The log a test run wrote in its save folder, and its crash report; '' for one absent."""
    found = []
    for name in ('log.txt', 'crash.txt'):
        try:
            with open(os.path.join(save, 'logs', name), encoding='utf-8', errors='replace') as fh:
                found.append(fh.read())
        except OSError:
            found.append('')
    return found[0], found[1]


def judge_test(code, log_text: str, crash: str) -> list:
    """What went wrong with a test run, or nothing: it must have found its game data, started
    FMOD, closed by itself, left no crash report and ended with 0."""
    problems = []
    if crash:
        problems.append('the game stopped with an error; its crash report:\n' + crash.rstrip())
    if 'game data: ' not in log_text:
        problems.append('the log has no "game data:" line, so the game never found its data'
                        if log_text else 'the game wrote no log at all')
    if log_text and 'FMOD ' not in log_text and not crash:
        problems.append('the log never says FMOD started, so the sound engine did not load')
    if log_text and not crash and not re.search(r'story recordings: .*%s' % re.escape(PACK), log_text):
        problems.append('the log never says the story recordings came from %s' % PACK)
    if 'Heathcote closed' not in log_text and not crash:
        problems.append('the game did not close by itself when --exit-after said to')
    if code is None:
        problems.append('the game was still running after %d seconds and was stopped' % TEST_TIMEOUT)
    elif code != 0:
        problems.append('the game ended with exit code %s' % code)
    return problems


def test_build(exe: str) -> bool:
    """Start the build for TEST_SECONDS, silently on a throwaway save; whether it worked."""
    if not os.path.isfile(exe):
        say('the test cannot start: there is no %s' % exe)
        return False
    say('testing the build: starting it for %d seconds, silently and on a throwaway save...'
        % TEST_SECONDS)
    with tempfile.TemporaryDirectory(prefix='heathcote_build_test_') as save:
        env = dict(os.environ, HEATHCOTE_USER_DIR=save, **TEST_QUIET)
        try:
            code = subprocess.run([exe, '--exit-after', str(TEST_SECONDS)], env=env,
                                  cwd=os.path.dirname(exe), timeout=TEST_TIMEOUT,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        except subprocess.TimeoutExpired:
            code = None
        except OSError as error:
            say('the test could not start the game: %s' % error)
            return False
        log_text, crash = read_log(save)
    problems = judge_test(code, log_text, crash)
    if problems:
        say('the test build FAILED:')
        for problem in problems:
            say('  ' + problem)
        return False
    line = next(l for l in log_text.splitlines() if 'game data: ' in l)
    say('the test build worked: it started, found its %s, opened %s, started FMOD, and closed '
        'by itself.' % (line[line.index('game data: '):], PACK))
    return True


# --- building ----------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='compiler.py', description='build Heathcote with PyInstaller')
    parser.add_argument('--embed', action='store_true',
                        help="a single exe with the game's data inside it")
    parser.add_argument('--onefile', action='store_true',
                        help="a single exe, with the game's data still beside it")
    parser.add_argument('--no-game', action='store_true', help="leave the game's data out")
    parser.add_argument('--console', action='store_true',
                        help='keep a console window, where a failed start prints its traceback')
    parser.add_argument('--clean', action='store_true', help="empty PyInstaller's cache first")
    parser.add_argument('--dry-run', action='store_true', help='say what would be done, build nothing')
    parser.add_argument('--test', action='store_true',
                        help='after building, start the build silently for a few seconds to check it')
    args = parser.parse_args(argv)
    if args.test and args.no_game:
        say("--test needs the game's data in the build, so it cannot go with --no-game.")
        return 2
    if args.embed and args.no_game:
        say("--embed puts the game's data inside the exe, so it cannot go with --no-game.")
        return 2
    os.chdir(HERE)

    found = problems_now()
    src = None if args.no_game else game_source()
    if src is not None:
        missing = missing_game_files(src)
        if missing:
            found.append("the game's data is missing %s" % ', '.join(missing))
    elif not args.no_game:
        found.append("there is no game\\%s, so the game's data cannot be built in"
                     % BUNDLE.replace('/', '\\'))
    if found:
        say('this would stop the build:' if args.dry_run else 'the build cannot start:')
        for problem in found:
            say('  ' + problem)
        if not args.dry_run:
            return 2
        say()

    dest_root = output_dir()
    embed_game = bool(args.embed and src)
    cmd = command(args, embed_game)
    say('running: python ' + ' '.join(cmd[1:]))
    exe = os.path.join(dest_root, EXE)
    if args.dry_run:
        if args.no_game:
            say("the game's data would be left out.")
        elif src is not None:
            say("the game's data would go %s: %s."
                % ('inside the exe' if embed_game else 'into %s' % os.path.join(dest_root, 'game'),
                   data_summary(src, game_files(src))))
            say('%s would be made beside the exe, encrypted, from %s, each read back to check it.'
                % (PACK, pack_summary(src)))
        for name, shipped_as in SIDE_FILES:
            say('%s would be copied beside the exe%s%s'
                % (name, '' if shipped_as == name else ', as %s' % shipped_as,
                   '' if os.path.isfile(os.path.join(HERE, name)) else ', but it is not here'))
        licenses = license_files()
        absent = [rel for rel, lic in licenses if not lic or not os.path.isfile(lic)]
        say('%d licence files, of %s, would go inside the build as licenses%s'
            % (len(licenses) - len(absent), LICENSED, os.sep))
        for rel in absent:
            say('  but the licence %s is not here' % rel)
        for warning in release_warnings(os.path.join(HERE, CHANGELOG)):
            say('before releasing: ' + warning)
        if args.test:
            say('then %s would be started for %d seconds, silently on a throwaway save, to check it'
                % (exe, TEST_SECONDS))
        return 0

    if os.path.isdir(GAME_STAGE):
        shutil.rmtree(GAME_STAGE)
    info = None
    if src is not None:
        say('making %s from %s ...' % (PACK, pack_summary(src)))
        try:
            info = make_pack(src, PACK_STAGE)
        except Exception as error:              # a pack that fails its check stops the build
            say('%s could not be made: %s' % (PACK, error))
            return 1
    if embed_game:
        names = copy_game(src, GAME_STAGE)
        write_fingerprint(GAME_STAGE, info)
        say("the game's data goes inside the exe: %s." % data_summary(src, names))
    stage_licenses()
    clear_output(dest_root)
    started = time.perf_counter()
    if subprocess.run(cmd).returncode != 0:
        say('PyInstaller failed; its own output above says why.')
        return 1
    say('built in %.0f seconds.' % (time.perf_counter() - started))
    if not one_file(args):
        move_folder_build(dest_root)
    if src is not None and not embed_game:
        dest_game = os.path.join(dest_root, 'game')
        say("copying the game's data into %s ..." % dest_game)
        say('  %s.' % data_summary(src, copy_game(src, dest_game)))
        write_fingerprint(dest_game, info)
    if info is not None:
        os.makedirs(dest_root, exist_ok=True)
        os.replace(PACK_STAGE, os.path.join(dest_root, PACK))
        say('%s is beside the exe.' % PACK)
    copy_side_files(dest_root)
    strip_shipped_changelog(dest_root)
    for warning in release_warnings(os.path.join(dest_root, CHANGELOG)):
        say('before releasing: ' + warning)
    say()
    say('the game is %s' % exe)
    say('the folder around it is what releaser.py zips.')
    if args.test:
        say()
        if not test_build(exe):
            return 1
    return 0


# --- the menu ----------------------------------------------------------------------------
# Each choice is exactly one of the command lines above, so the two never disagree.

MENU = (
    ('Folder build: the exe, with a folder of Python files and the game folder beside it', []),
    ('Folder build and test: the folder build, then started silently for a few seconds to check it',
     ['--test']),
    ("Single exe: Python, the libraries and the game's data all inside the exe", ['--embed']),
    ('Single exe and test: the single exe, then started silently for a few seconds to check it',
     ['--embed', '--test']),
    ("Clean build: empty PyInstaller's cache first, for when a build behaves oddly", ['--clean']),
    ('Console build: keep a console window, to see why the game will not start', ['--console']),
    ("One-file build: Python and the libraries inside the exe, the game folder still beside it",
     ['--onefile']),
    ("Build without the game's data", ['--no-game']),
    ('Dry run: say what a build would do, without building anything', ['--dry-run']),
)


def show_menu() -> None:
    say('Heathcote compiler. VERSION is %s.'
        % (build_version() or 'missing; releaser.py sets it as it releases'))
    say()
    for number, (text, _flags) in enumerate(MENU, 1):
        say('  %d. %s' % (number, text))
    say('  0. Quit')
    say()


def menu():
    """Ask which build: the flags for it, or None to quit. Enter with nothing typed says
    the menu again (the dev, 2026-10-21: "Please make it so pressing enter repeats the menu
    if you do not type a number")."""
    show_menu()
    while True:
        try:
            choice = input('Type a number and press Enter: ').strip()
        except EOFError:
            return None
        if not choice:
            show_menu()
            continue
        if choice == '0':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            text, flags = MENU[int(choice) - 1]
            say('%s.' % text.split(':')[0])
            say()
            return list(flags)
        say('There is no choice "%s". Type a number from 0 to %d.' % (choice, len(MENU)))


def run(argv=None) -> int:
    """Flags on the command line build straight away. No flags at a keyboard, a double-click
    or the name typed on its own, opens the menu, and the window waits at the end."""
    argv = sys.argv[1:] if argv is None else argv
    if argv or not sys.stdin.isatty():
        return main(argv)
    chosen = menu()
    if chosen is None:
        return 0
    try:
        return main(chosen)
    finally:
        say()
        try:
            input('Finished. Press Enter to close this window.')
        except EOFError:
            pass


if __name__ == '__main__':
    sys.exit(run())
