"""Release Heathcote: set the version, file the changelog, build, zip, commit, tag and
upload, all from this machine.

Section 2 of aidocks/plans/build_release_plan.md. Double-click this file, or run python
releaser.py, and it offers a numbered menu: the whole release, or any one step of it. Every
step says what it is about to do and asks Y or N first, and the window waits for Enter at
the end so you can hear how it went. Enter with nothing typed says the menu again.
compiler.py does the building; this does everything around it.

    1. full release   steps 2 to 8 below, in order
    2. check          everything committed and pushed, the GitHub CLI here and signed in, and
                      5 to 100 changes waiting under "unrelease:" in docks\\changelog.txt, each
                      ending in a full stop; with 1 to 4 it asks whether to release anyway
    3. prepare        VERSION becomes today's date and that day's release number, such as
                      26.10.21-1, counted from the tags, and the lines under "unrelease:" are
                      filed under it
    4. build          the folder build or the single exe, through compiler.py; a failed build
                      puts VERSION and the changelog back
    5. zip            the build becomes dist\\Heathcote-Win-<version>.zip, which extracts to a
                      Heathcote-Windows folder; only a build made for that version
    6. commit         VERSION and the changelog, as "Release <version>", and push
    7. tag            V<version>, and push the tag
    8. upload         the release "Heathcote V<version>" on GitHub, with the zip and that
                      version's changelog lines as its notes

A step answered N is skipped, and each checks for itself that what it needs is there.
Nothing here ever moves or deletes a tag or a release, or replaces a file already on one.
Every recording is inside the zip, fmod.dll with them (aidocks/general/project_no_downloads.md),
so there is nothing else to upload.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import compiler                                                             # noqa: E402
from compiler import (NAME, UNRELEASE, changelog_heading, parse_changelog,  # noqa: E402
                      render_changelog, unreleased_lines)

TITLE_PREFIX = NAME + ' V'
TAG_PREFIX = 'V'
#: A release carries at most this many changelog entries, and at least MIN_ENTRIES, unless
#: the one releasing says to go ahead with fewer (aidocks/general/feedback_changelog.md).
MAX_ENTRIES = 100
MIN_ENTRIES = 5

#: Where the GitHub CLI's installer puts it, when it is not on the PATH.
GH_FALLBACK = r'C:\Program Files\GitHub CLI\gh.exe'

VERSION_FILE = os.path.join(HERE, 'VERSION')
CHANGELOG = os.path.join(HERE, compiler.CHANGELOG)
#: The changelog as git names it.
CHANGELOG_GIT = compiler.CHANGELOG.replace(os.sep, '/')
#: What the compiler builds, and so what gets zipped.
BUILD_DIR = compiler.output_dir()
#: Packing says how far it has got after each quarter of the files.
PACK_STEPS = 4


def say(text: str = '') -> None:
    print(text, flush=True)


def ask(question: str) -> bool:
    """A Y or N question. Anything but Y is no, and so is no keyboard at all."""
    try:
        return input('%s (Y/N): ' % question).strip().upper() == 'Y'
    except EOFError:
        return False


# --- the version -------------------------------------------------------------------------

def today_stamp(now=None) -> str:
    """'26.10.21' on the 21st of October 2026."""
    return time.strftime('%y.%m.%d', time.localtime(now))


def next_version(tags, stamp: str) -> str:
    """Today's version: one past the highest release number tagged for that day, or 1."""
    pattern = re.compile(r'^%s%s-(\d+)$' % (re.escape(TAG_PREFIX), re.escape(stamp)))
    numbers = [int(m.group(1)) for m in (pattern.match(t.strip()) for t in tags) if m]
    return '%s-%d' % (stamp, max(numbers, default=0) + 1)


def tag_for(version: str) -> str:
    return TAG_PREFIX + version


def title_for(version: str) -> str:
    return TITLE_PREFIX + version


def read_version() -> str:
    return compiler.build_version()


# --- the changelog -----------------------------------------------------------------------

def plan_changelog(text: str, version: str):
    """The changelog with its unreleased lines filed under ``version``: (text, changed, notes).

    The lines move to this version's entry, a new one just below unrelease:, or the bottom of
    one already there, and unrelease: stays at the top, empty. A deleted unrelease: line is
    put back."""
    blocks = parse_changelog(text)
    notes = []
    at = next((i for i, (heading, _lines) in enumerate(blocks) if heading == UNRELEASE), None)
    if at is None:
        blocks.insert(0, [UNRELEASE, []])
        at = 0
        notes.append('there was no "%s" line, so one was put back at the top' % UNRELEASE)
    moving, heading = blocks[at][1], changelog_heading(version)
    if moving:
        blocks[at][1] = []
        entry = next((block for block in blocks if block[0] == heading), None)
        if entry is not None:
            entry[1].extend(moving)
            notes.append('%d line(s) from "%s" went to the bottom of %s' % (len(moving), UNRELEASE, heading))
        else:
            blocks.insert(at + 1, [heading, moving])
            notes.append('%d line(s) from "%s" became the new entry %s' % (len(moving), UNRELEASE, heading))
    else:
        notes.append('nothing is under "%s", so no entry was added' % UNRELEASE)
    changed = bool(moving) or len(notes) > 1
    return (render_changelog(blocks) if changed else text), changed, notes


def release_notes(text: str, version: str) -> str:
    """The lines filed under ``version``, one per line: the release page's notes."""
    heading = changelog_heading(version)
    lines = next((lines for h, lines in parse_changelog(text) if h == heading), [])
    return '\n'.join(line.strip() for line in lines)


def without_full_stop(lines) -> list:
    """The entries that do not end in a full stop, a full stop inside a closing quote
    counting (aidocks/general/feedback_changelog.md)."""
    return [line.strip() for line in lines
            if not re.search(r'\.["\u201d\']?$', line.strip())]


def too_few(count: int) -> str:
    return ('only %d change(s) are under "%s", and a release needs at least %d.'
            % (count, UNRELEASE, MIN_ENTRIES))


def release_anyway(count: int) -> bool:
    return ask('Release anyway with %d change(s)?' % count)


def read_changelog() -> str:
    if not os.path.isfile(CHANGELOG):
        return ''
    with open(CHANGELOG, encoding='utf-8-sig') as fh:
        return fh.read()


def write_text(path: str, text: str) -> None:
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


# --- the zip -----------------------------------------------------------------------------

def zip_name(version: str) -> str:
    """Heathcote-Win-26.10.21-1.zip"""
    return '%s-Win-%s.zip' % (NAME, version)


def zip_path(version: str) -> str:
    return os.path.join(HERE, 'dist', zip_name(version))


def built_version(build_dir: str = None) -> str:
    """The version the build carries, from the VERSION beside its exe, or ''."""
    try:
        with open(os.path.join(build_dir or BUILD_DIR, 'VERSION'), encoding='utf-8-sig') as fh:
            return fh.read().strip().splitlines()[0].strip()
    except (OSError, IndexError):
        return ''


def package(build_dir: str, version: str, archive: str = None) -> str:
    """Zip the built folder, everything under one Heathcote-Windows folder, so extracting it
    gives a player a folder rather than a heap of files. It is written under a .part name
    and renamed once whole, so a window closed halfway leaves no zip that looks finished but
    will not open. The recordings are MP3s, which barely shrink, so they are stored as they
    are and only the rest is compressed."""
    archive = archive or zip_path(version)
    partial = archive + '.part'
    for old in (archive, partial):
        if os.path.isfile(old):
            os.remove(old)
    files = []
    for dirpath, dirs, names in os.walk(build_dir):
        dirs.sort()
        files += [os.path.join(dirpath, n) for n in sorted(names)]
    say('packing %d files into %s.' % (len(files), os.path.basename(archive)))
    say('this can take a minute; leave this window open until it says the zip is done.')
    started = time.perf_counter()
    marks = {len(files) * step // PACK_STEPS for step in range(1, PACK_STEPS)}
    with zipfile.ZipFile(partial, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as box:
        for count, full in enumerate(files, 1):
            inside = os.path.join(compiler.FOLDER, os.path.relpath(full, build_dir))
            stored = full.lower().endswith('.mp3')
            box.write(full, inside.replace(os.sep, '/'),
                      compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
            if count in marks:
                say('  %d of %d files packed ...' % (count, len(files)))
    os.replace(partial, archive)
    say('the zip is done: %d files, %.0f MB, in %.0f seconds.'
        % (len(files), os.path.getsize(archive) / (1 << 20), time.perf_counter() - started))
    return archive


def find_zip(version: str):
    path = zip_path(version)
    return path if os.path.isfile(path) else None


# --- running things ----------------------------------------------------------------------

def git(*args, capture=True):
    """Run git in the repository: (ok, output)."""
    proc = subprocess.run(['git'] + list(args), cwd=HERE, capture_output=capture, text=True)
    out = (proc.stdout or '').strip() if capture else ''
    if capture and proc.returncode != 0 and proc.stderr:
        out = (out + '\n' + proc.stderr.strip()).strip()
    return proc.returncode == 0, out


def gh_path():
    """The GitHub CLI: on the PATH, or where its installer puts it."""
    found = shutil.which('gh')
    if found:
        return found
    return GH_FALLBACK if os.path.isfile(GH_FALLBACK) else None


def gh(*args, capture=True):
    """Run the GitHub CLI in the repository: (ok, output)."""
    exe = gh_path()
    if exe is None:
        return False, 'the GitHub CLI was not found'
    proc = subprocess.run([exe] + list(args), cwd=HERE, capture_output=capture, text=True)
    out = ((proc.stdout or '') + (proc.stderr or '')).strip() if capture else ''
    return proc.returncode == 0, out


def release_assets(tag: str):
    """The file names on the GitHub release for ``tag``, or None when it cannot be read."""
    ok, out = gh('release', 'view', tag, '--json', 'assets', '--jq', '.assets[].name')
    if not ok:
        return None
    return [line.strip() for line in out.splitlines() if line.strip()]


def all_tags() -> list:
    """Every tag, here and on GitHub."""
    tags = set()
    ok, out = git('tag', '--list')
    if ok:
        tags.update(t.strip() for t in out.splitlines() if t.strip())
    ok, out = git('ls-remote', '--tags', 'origin')
    if ok:
        for line in out.splitlines():
            ref = line.split('\t')[-1].strip()
            if ref.startswith('refs/tags/'):
                tags.add(ref[len('refs/tags/'):].replace('^{}', ''))
    return sorted(tags)


# --- the steps ---------------------------------------------------------------------------
# Each returns True when it did its work or found it done, False when it could not, and
# None when it was skipped.

def changelog_problems(waiting: list, others: list, ask_fewer: bool) -> list:
    """What is wrong with the changes waiting under unrelease:. ``others`` are the problems
    found so far, since the question about too few is asked only when nothing else is in
    the way, so a Y is never wasted."""
    problems = []
    if not waiting:
        return ['nothing is under "%s" in %s, so there is nothing to release.' % (UNRELEASE, CHANGELOG_GIT)]
    if len(waiting) > MAX_ENTRIES:
        problems.append('%d changes are under "%s", and a release carries no more than %d.'
                        % (len(waiting), UNRELEASE, MAX_ENTRIES))
    bare = without_full_stop(waiting)
    if bare:
        problems.append('%d change(s) under "%s" do not end in a full stop: %s'
                        % (len(bare), UNRELEASE, ' | '.join(bare)))
    if MIN_ENTRIES > len(waiting):
        if others or problems or not ask_fewer:
            problems.append(too_few(len(waiting)))
        else:
            say('  ' + too_few(len(waiting)))
            if release_anyway(len(waiting)):
                say('  releasing anyway with %d change(s).' % len(waiting))
            else:
                problems.append(too_few(len(waiting)))
    elif not problems:
        say('  %d change(s) are waiting to be released, which is fine.' % len(waiting))
    return problems


def step_check() -> bool:
    """Everything a release needs before it starts. Each problem is said as it is found, and
    named again at the end."""
    say('checking the repository ...')
    problems = []

    def problem(text, details=()):
        say('  ' + text)
        for line in details:
            say('    ' + line)
        problems.append(text)

    ok, out = git('status', '--porcelain')
    if not ok:
        say('  git could not be run here: %s' % out)
        return False
    if out:
        problem('there are changes that are not committed. Commit them first:', out.splitlines())
    git('fetch', 'origin')
    ok, out = git('rev-list', '--left-right', '--count', 'HEAD...@{upstream}')
    if ok:
        ahead, behind = (int(n) for n in out.split())
        if ahead:
            problem('%d commit(s) are not pushed yet. Push them first.' % ahead)
        if behind:
            problem('GitHub has %d commit(s) this copy does not. Pull them first.' % behind)
    else:
        problem('could not compare this branch with GitHub: %s' % out)
    if gh_path() is None:
        problem('the GitHub CLI, gh, was not found. Install it from cli.github.com.')
    else:
        ok, _out = gh('auth', 'status')
        if not ok:
            problem('the GitHub CLI is not signed in. Run gh auth login.')
    for text in changelog_problems(unreleased_lines(read_changelog()), problems, ask_fewer=True):
        problem(text)
    if not problems:
        say('  everything is ready.')
        return True
    say('  the release cannot go ahead until %s fixed:'
        % ('this is' if len(problems) == 1 else 'these %d are' % len(problems)))
    for n, text in enumerate(problems, 1):
        say('    %d. %s' % (n, text))
    return False


def step_prepare(forced=False):
    """Set VERSION to today's release and file the changelog under it. Returns the version
    and what the two files held before, so a failed build can put them back; or None.
    ``forced``: the check has already been told to release with fewer than MIN_ENTRIES."""
    version = next_version(all_tags(), today_stamp())
    text = read_changelog()
    waiting = unreleased_lines(text)
    if not waiting:
        say('nothing is under "%s", so there is nothing to file.' % UNRELEASE)
        return None
    if len(waiting) > MAX_ENTRIES:
        say('%d changes are under "%s", and a release carries no more than %d.'
            % (len(waiting), UNRELEASE, MAX_ENTRIES))
        return None
    if len(waiting) < MIN_ENTRIES and not forced:
        say(too_few(len(waiting)))
        if not release_anyway(len(waiting)):
            say('nothing was filed.')
            return None
    say('this release will be %s, tagged %s, with %d change(s).'
        % (title_for(version), tag_for(version), len(waiting)))
    if not ask('Set VERSION to %s and file the changelog under it?' % version):
        say('skipped.')
        return None
    old_version = None
    if os.path.isfile(VERSION_FILE):
        with open(VERSION_FILE, encoding='utf-8') as fh:
            old_version = fh.read()
    new, _changed, notes = plan_changelog(text, version)
    write_text(VERSION_FILE, version + '\n')
    write_text(CHANGELOG, new)
    say('VERSION is now %s.' % version)
    for note in notes:
        say('changelog: %s' % note)
    return version, old_version, text


def restore(saved) -> None:
    """Put VERSION and the changelog back as step_prepare found them."""
    _version, old_version, old_changelog = saved
    if old_version is None:
        if os.path.isfile(VERSION_FILE):
            os.remove(VERSION_FILE)
    else:
        write_text(VERSION_FILE, old_version)
    write_text(CHANGELOG, old_changelog)
    say('VERSION and %s are back as they were.' % CHANGELOG_GIT)


BUILDS = ('  1. the folder build: the exe, with a folder of Python files and the game folder beside it',
          "  2. the single exe: Python, the libraries and the game's data all inside it",
          '  0. skip the build')


def choose_build():
    """Which build: the folder or the single exe; None to skip. Enter with nothing typed
    says the choices again."""
    say('which build should the release carry?')
    for line in BUILDS:
        say(line)
    while True:
        try:
            choice = input('Type a number and press Enter: ').strip()
        except EOFError:
            return None
        if not choice:
            for line in BUILDS:
                say(line)
            continue
        if choice == '0':
            return None
        if choice == '1':
            return []
        if choice == '2':
            return ['--embed']
        say('There is no choice "%s". Type 0, 1 or 2.' % choice)


def step_build(saved=None):
    """compiler.py, into dist\\Heathcote-Windows. After step_prepare, a failed build undoes
    it."""
    flags = choose_build()
    if flags is None:
        say('skipped the build.')
        return None
    say()
    try:
        code = compiler.main(flags)
    except Exception as error:                  # a crash in the build counts as a failure
        say('the build stopped with an error: %r' % error)
        code = 1
    os.chdir(HERE)
    if code != 0:
        say('the build failed.')
        if saved is not None:
            restore(saved)
        return False
    return True


def step_package(version: str):
    """Zip the build. Refuses one made for another version, so an old build can never go out
    under a new name."""
    if not os.path.isdir(BUILD_DIR):
        say('there is no build in %s. Build it first.' % BUILD_DIR)
        return False
    carries = built_version()
    if carries != version:
        say('the build in %s is for %s, not %s. Build it again first.'
            % (BUILD_DIR, carries or 'no version', version))
        return False
    if not ask('Zip the build into %s?' % zip_name(version)):
        say('skipped the zip.')
        return None
    try:
        package(BUILD_DIR, version)
    except OSError as error:
        say('the zip could not be written: %s' % error)
        return False
    return True


def step_commit(version: str) -> bool:
    """Commit VERSION and the changelog as the release, and push."""
    ok, out = git('status', '--porcelain', '--', 'VERSION', CHANGELOG_GIT)
    if not out:
        say('VERSION and %s have nothing to commit.' % CHANGELOG_GIT)
        return True
    if not ask('Commit VERSION and %s as "Release %s", and push?' % (CHANGELOG_GIT, version)):
        say('skipped.')
        return False
    ok, out = git('add', '--', 'VERSION', CHANGELOG_GIT)
    if ok:
        ok, out = git('commit', '-m', 'Release %s' % version, '--', 'VERSION', CHANGELOG_GIT)
    if not ok:
        say('the commit failed: %s' % out)
        return False
    say('committed.')
    ok, out = git('push', 'origin', 'HEAD')
    if not ok:
        say('the push failed: %s' % out)
        return False
    say('pushed.')
    return True


def step_tag(version: str) -> bool:
    """Push the branch, then tag the current commit V<version> and push the tag. The branch
    goes first, so GitHub never has a tag on a commit its branch lacks. An existing tag is
    never moved."""
    tag = tag_for(version)
    if tag in all_tags():
        say('the tag %s already exists, so it is left where it is.' % tag)
        return True
    ok, head = git('log', '-1', '--format=%h %s')
    if not ask('Push the branch, tag %s as %s, and push the tag?' % (head, tag)):
        say('skipped.')
        return False
    ok, out = git('push', 'origin', 'HEAD')
    if not ok:
        say('the branch could not be pushed, so nothing was tagged: %s' % out)
        return False
    ok, out = git('tag', tag)
    if not ok:
        say('the tag could not be made: %s' % out)
        return False
    ok, out = git('push', 'origin', tag)
    if not ok:
        say('the tag could not be pushed: %s' % out)
        return False
    say('tagged %s and pushed it.' % tag)
    return True


def add_to_release(tag: str, path: str) -> bool:
    """Add a file to a release already on GitHub, unless one of that name is there; nothing
    on a release is ever replaced."""
    name = os.path.basename(path)
    assets = release_assets(tag)
    if assets is None:
        say('the files on the release %s could not be read.' % tag)
        return False
    if name in assets:
        say('the release %s already has %s, so it is left as it is.' % (tag, name))
        return True
    say('the release %s is on GitHub without %s (%.0f MB).'
        % (tag, name, os.path.getsize(path) / (1 << 20)))
    if not ask('Add it to the release?'):
        say('skipped.')
        return False
    say('uploading; this can take a few minutes for a file this size. Leave this window open.')
    ok, _out = gh('release', 'upload', tag, path, capture=False)
    if not ok:
        say('the upload failed. What gh said is above.')
        return False
    say('%s is on the release %s.' % (name, tag))
    return True


def create_release(tag: str, path: str, title: str, notes: str, *extra) -> bool:
    """A new release on GitHub with one file, its notes passed through a file."""
    handle, notes_file = tempfile.mkstemp(suffix='.txt', prefix='release-notes-')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as fh:
            fh.write(notes + '\n')
        say('uploading; this can take a few minutes for a file this size. Leave this window open.')
        ok, _out = gh('release', 'create', tag, path, '--title', title, '--notes-file', notes_file,
                      *extra, capture=False)
    finally:
        os.remove(notes_file)
    if not ok:
        say('the upload failed. What gh said is above.')
    return ok


def step_upload(version: str) -> bool:
    """The GitHub release, with the zip and that version's changelog lines."""
    tag, title = tag_for(version), title_for(version)
    archive = find_zip(version)
    if archive is None:
        say('there is no zip for %s at %s. Build and zip it first.' % (version, zip_path(version)))
        return False
    if tag not in all_tags():
        say('the tag %s does not exist yet. Tag the release first.' % tag)
        return False
    ok, _out = gh('release', 'view', tag)
    if ok:
        return add_to_release(tag, archive)
    notes = release_notes(read_changelog(), version)
    if not notes:
        say('the changelog has nothing under %s, so the release notes would be empty.'
            % changelog_heading(version))
    say('the release will be "%s", tag %s, with %s (%.0f MB).'
        % (title, tag, os.path.basename(archive), os.path.getsize(archive) / (1 << 20)))
    if not ask('Upload it to GitHub?'):
        say('skipped.')
        return False
    if not create_release(tag, archive, title, notes, '--verify-tag'):
        return False
    say('the release %s is on GitHub.' % title)
    return True


def full_release() -> None:
    """Steps 2 to 8, in order. A step answered N is skipped; one that fails stops it."""
    if not step_check():
        return
    say()
    # The check passed, so any shortfall below MIN_ENTRIES was already answered Y there.
    saved = step_prepare(forced=True)
    version = saved[0] if saved else read_version()
    if not version:
        say('there is no version to release.')
        return
    say()
    if step_build(saved) is False:
        return
    say()
    if step_package(version) is False:
        return
    say()
    if not step_commit(version):
        return
    say()
    if not step_tag(version):
        return
    say()
    step_upload(version)


# --- the menu ----------------------------------------------------------------------------

MENU = (
    ('Full release: every step below from 2 to 8, in order', full_release),
    ('Check that everything is ready', step_check),
    ('Set the version and file the changelog', lambda: step_prepare()),
    ('Build', lambda: step_build()),
    ('Zip the build', lambda: step_package(read_version())),
    ('Commit and push the version and changelog', lambda: step_commit(read_version())),
    ('Tag the release', lambda: step_tag(read_version())),
    ('Upload the release to GitHub', lambda: step_upload(read_version())),
)


def show_menu() -> None:
    say()
    say('Heathcote releaser. VERSION is %s.' % (read_version() or 'missing'))
    say()
    for number, (text, _action) in enumerate(MENU, 1):
        say('  %d. %s' % (number, text))
    say('  0. Quit')
    say()


def menu() -> None:
    """The steps, until 0. Enter with nothing typed says the menu again, as the compiler's
    does."""
    show_menu()
    while True:
        try:
            choice = input('Type a number and press Enter: ').strip()
        except EOFError:
            return
        if not choice:
            show_menu()
            continue
        if choice == '0':
            return
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            text, action = MENU[int(choice) - 1]
            say('%s.' % text.split(':')[0])
            say()
            action()
            show_menu()
            continue
        say('There is no choice "%s". Type a number from 0 to %d.' % (choice, len(MENU)))


def run() -> int:
    os.chdir(HERE)
    try:
        menu()
    finally:
        say()
        try:
            input('Finished. Press Enter to close this window.')
        except EOFError:
            pass
    return 0


if __name__ == '__main__':
    sys.exit(run())
