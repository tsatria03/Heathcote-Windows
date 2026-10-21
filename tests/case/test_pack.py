"""story.dat (heathcote/platform/pack.py): the format, damaged and foreign packs, FMOD's
no-sound output playing what it holds, and StoryData finding the story there."""
import _quiet  # noqa: F401  (first, before the game)

import json
import os
import shutil

from heathcote import paths
from heathcote.game import storydata
from heathcote.game.storydata import StoryData
from heathcote.platform import pack
from heathcote.platform.audio import Audio
from heathcote.platform.settings import Settings

STORY = StoryData.shared()
REAL_STORY = os.path.join(STORY.audio_root, 'story')
N = [0]


def folder(name):
    N[0] += 1
    path = os.path.join(_quiet.FOLDER, 'pack%d' % N[0], name)
    os.makedirs(path, exist_ok=True)
    return path


def small_story():
    """A story folder with two real recordings in subfolders, and its pack."""
    root = folder('story')
    for sub, label in (('scene', 'start'), ('music', 'title')):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    start = STORY.audio_path(STORY.start())
    title = STORY.sound_path('bgm', 'title')
    shutil.copy2(start, os.path.join(root, 'scene', os.path.basename(start)))
    shutil.copy2(title, os.path.join(root, 'music', os.path.basename(title)))
    dest = os.path.join(os.path.dirname(root), 'story.dat')
    info = pack.write_pack(root, dest)
    return root, dest, info, os.path.basename(start), os.path.basename(title)


def test_every_recording_reads_back_by_its_path_in_the_folder():
    root, dest, info, start, title = small_story()
    opened = pack.Pack(dest)
    assert sorted(opened.files) == sorted(['scene/' + start, 'music/' + title])
    with open(os.path.join(root, 'scene', start), 'rb') as fh:
        assert opened.read('scene/' + start) == fh.read()
    assert info['files'] == 2 and info['size'] == os.path.getsize(dest)
    assert pack.fingerprint(dest)['sha256'] == info['sha256']
    assert not os.path.exists(dest + '.part')


def test_the_pack_hides_its_names_and_its_sound():
    root, dest, _info, start, _title = small_story()
    with open(dest, 'rb') as fh:
        raw = fh.read()
    assert raw.startswith(pack.MAGIC)
    assert start.encode('utf-8') not in raw and b'scene/' not in raw
    with open(os.path.join(root, 'scene', start), 'rb') as fh:
        assert fh.read()[1000:1064] not in raw                      # no stretch of the MP3


def test_a_damaged_recording_a_damaged_index_and_a_foreign_file_are_refused():
    _root, dest, _info, start, _title = small_story()
    opened = pack.Pack(dest)
    at, length = opened.files['scene/' + start]
    with open(dest, 'r+b') as fh:
        fh.seek(opened.start + at + length // 2)
        byte = fh.read(1)
        fh.seek(-1, 1)
        fh.write(bytes([byte[0] ^ 1]))
    try:
        pack.Pack(dest).read('scene/' + start)
    except pack.PackError as error:
        assert 'damaged' in str(error)
    else:
        raise AssertionError('a damaged recording was read')
    with open(dest, 'r+b') as fh:
        fh.seek(len(pack.MAGIC) + 4 + 20)                           # inside the index
        byte = fh.read(1)
        fh.seek(-1, 1)
        fh.write(bytes([byte[0] ^ 1]))
    for bad in (dest, os.path.join(REAL_STORY, 'scene', start)):    # and an MP3 is no pack
        try:
            pack.Pack(bad)
        except pack.PackError:
            pass
        else:
            raise AssertionError('%s opened as a pack' % bad)


def test_one_part_cannot_pass_for_another():
    data = pack.seal(b'hello', 'scene/a.mp3')
    assert pack.unseal(data, 'scene/a.mp3') == b'hello'
    try:
        pack.unseal(data, 'scene/b.mp3')
    except pack.PackError:
        pass
    else:
        raise AssertionError('a part opened under another name')


def test_fmod_plays_a_packed_recording_from_memory_as_a_sample_and_as_a_stream():
    _root, dest, _info, start, title = small_story()
    pack.use(pack.Pack(dest))
    audio = Audio(Settings(os.path.join(folder('settings'), 'settings.json')))
    audio.open()
    try:
        sfx, bgm = audio.slot('sfx'), audio.slot('bgm')
        assert sfx.play(pack.PREFIX + 'scene/' + start, loop=False) and sfx.playing
        assert bgm.play(pack.PREFIX + 'music/' + title) and bgm.playing    # a looping stream
        assert audio.spiel.play(pack.PREFIX + 'scene/' + start) and audio.spiel.length > 1.0
        assert not audio.slot('ambience1').play(pack.PREFIX + 'scene/missing.mp3')
    finally:
        audio.close()
        pack.use(None)


def test_a_packed_stream_keeps_its_bytes_while_fmod_reads_them():
    """Freed too soon, FMOD's stream thread read memory that was gone, and the built game
    closed at the main menu with an access violation (2026-10-21)."""
    import gc
    import time
    _root, dest, _info, _start, title = small_story()
    pack.use(pack.Pack(dest))
    audio = Audio(Settings(os.path.join(folder('settings'), 'settings.json')))
    audio.open()
    try:
        bgm = audio.slot('bgm')
        assert bgm.play(pack.PREFIX + 'music/' + title)
        assert isinstance(bgm.memory, bytes) and len(bgm.memory) > 100000
        gc.collect()
        end = time.perf_counter() + 2.0
        while time.perf_counter() < end:                # FMOD streams on its own thread
            audio.update()
            time.sleep(0.01)
        assert bgm.playing
        bgm.stop(fade_out=0.3)                          # fading, it keeps its bytes too
        assert bgm.memory is None and any(len(item) == 4 and item[3] for item in audio.fading_out)
        file_slot = audio.slot('ambience1')
        file_slot.play(STORY.audio_path(STORY.refs('ambience')[0]))
        assert file_slot.memory is None                 # a file on disk needs none
    finally:
        audio.close()
        pack.use(None)


def story_without_its_folder():
    """A copy of the story's text, with an Audio folder holding no story folder."""
    game = folder('game')
    shutil.copytree(os.path.join(os.path.dirname(STORY.audio_root), 'text'),
                    os.path.join(game, 'documents', 'text'))
    os.makedirs(os.path.join(game, 'documents', 'Audio', 'System'))
    return game


def fingerprint_path(game):
    """Where a build carries story_pack.json: game\\documents\\text\\system\\."""
    return os.path.join(game, 'documents', 'text', 'system', paths.PACK_FINGERPRINT)


def with_pack_at(where, fn):
    saved = paths.story_pack
    paths.story_pack = lambda: where
    try:
        return fn()
    finally:
        paths.story_pack = saved
        pack.use(None)


def test_without_the_folder_the_story_plays_from_the_pack():
    _root, dest, info, start, _title = small_story()
    game = story_without_its_folder()
    with open(fingerprint_path(game), 'w', encoding='utf-8') as fh:
        json.dump({'size': info['size'], 'sha256': info['sha256']}, fh)

    def check():
        story = StoryData(text=os.path.join(game, 'documents', 'text'))
        assert story.pack is not None and pack.shared() is story.pack
        assert story.audio_path(story.start()) == pack.PREFIX + 'scene/' + start
        assert story.sound_path('bgm', 'title').startswith(pack.PREFIX + 'music/')
        assert not story.sound_path('systemSounds', 'click-good').startswith(pack.PREFIX)
    with_pack_at(dest, check)


def test_a_missing_pack_or_one_from_another_build_stops_with_a_message():
    _root, dest, info, _start, _title = small_story()
    game = story_without_its_folder()
    text = os.path.join(game, 'documents', 'text')
    for where, fingerprint, words in ((os.path.join(game, 'nowhere.dat'), None, 'were not found'),
                                      (dest, info['size'] + 1, 'does not belong')):
        if fingerprint is not None:
            with open(fingerprint_path(game), 'w', encoding='utf-8') as fh:
                json.dump({'size': fingerprint, 'sha256': 'x'}, fh)
        try:
            with_pack_at(where, lambda: StoryData(text=text))
        except SystemExit as stop:
            assert words in str(stop.code), stop.code
        else:
            raise AssertionError('no SystemExit for %s' % words)


def test_from_source_the_loose_folder_wins():
    assert STORY.pack is None
    assert os.path.isfile(STORY.audio_path(STORY.start()))
    assert paths.story_pack().endswith(os.path.join('dist', 'story.dat'))


def test_a_build_looks_in_the_data_folder_beside_its_exe():
    saved = paths.FROZEN, paths.EXE_DIR
    paths.FROZEN, paths.EXE_DIR = True, os.path.join('C:\\', 'Games', 'Heathcote-Windows')
    try:
        assert paths.story_pack() == os.path.join('C:\\', 'Games', 'Heathcote-Windows', 'data', 'story.dat')
    finally:
        paths.FROZEN, paths.EXE_DIR = saved
    assert storydata.PACKED_FOLDER == 'story'


if __name__ == '__main__':
    _quiet.run_tests(globals())
