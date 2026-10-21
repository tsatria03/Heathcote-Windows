"""story.dat: the story's recordings, packed and encrypted (aidocks/plans/build_release_plan.md,
section 3).

A build carries every file of game/documents/Audio/story/ in one file, story.dat, beside
Heathcote.exe, so the exe stays small (the dev, 2026-10-21: "I did not want the exe file to
be too big if embedded."). The interface sounds and the story's text are embedded as
normal.

The file:

    b'HEATHPK1'                  8 bytes, the magic; its last character is the version
    index length                 4 bytes, big-endian
    the index, sealed            a JSON object, {"files": {name: [offset, length]}}
    each recording, sealed       one after another, offsets counted from here

Each sealed part is a 12-byte nonce, the AES-256-GCM ciphertext, and its 16-byte tag. The
associated data is the recording's name, or "index" for the index, so one part cannot be
passed off as another. A name is the recording's path inside Audio/story/, with forward
slashes, such as "scene/start.mp3". Nothing is compressed, since MP3s barely shrink.

The key ships inside the game, so this keeps out casual copying, not a determined person.
Each recording is sealed on its own, so the game decrypts only the one it needs, in
memory, and never writes it to disk.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import struct

log = logging.getLogger('pack')

MAGIC = b'HEATHPK1'
KEY = bytes.fromhex('5c33b1c47312ce2525d2ab670fd0104d442d2c6d3c7fdc177d2bc06accdd2fc6')
NONCE = 12
TAG = 16
INDEX_NAME = 'index'
#: How a packed recording is named where a path would be, as StoryData gives it to the
#: audio: this, then its name in the pack.
PREFIX = 'story.dat:'


class PackError(Exception):
    """The pack is missing, is not a pack, or is damaged."""


def _aead():
    # Imported here, so the game starts without cryptography when it never needs the pack.
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(KEY)


def seal(data: bytes, name: str, aead=None) -> bytes:
    nonce = os.urandom(NONCE)
    return nonce + (aead or _aead()).encrypt(nonce, data, name.encode('utf-8'))


def unseal(part: bytes, name: str, aead=None) -> bytes:
    from cryptography.exceptions import InvalidTag
    if len(part) < NONCE + TAG:
        raise PackError('%s is damaged' % name)
    try:
        return (aead or _aead()).decrypt(part[:NONCE], part[NONCE:], name.encode('utf-8'))
    except InvalidTag:
        raise PackError('%s is damaged' % name) from None


def recording_name(path: str, root: str) -> str:
    """A recording's name in the pack: its path inside ``root``, with forward slashes."""
    return os.path.relpath(path, root).replace(os.sep, '/')


def recordings(root: str) -> list:
    """Every file under ``root``, by name, in a fixed order."""
    found = []
    for folder, dirs, names in os.walk(root):
        dirs.sort()
        found += [os.path.join(folder, n) for n in sorted(names)]
    return found


def write_pack(root: str, dest: str, progress=None) -> dict:
    """Pack every file under ``root`` into ``dest``; its fingerprint, {size, sha256, files}.
    Written under a .part name and renamed once whole."""
    aead = _aead()
    files = recordings(root)
    index, parts, offset = {}, [], 0
    for count, path in enumerate(files, 1):
        name = recording_name(path, root)
        with open(path, 'rb') as fh:
            sealed = seal(fh.read(), name, aead)
        index[name] = [offset, len(sealed)]
        parts.append(sealed)
        offset += len(sealed)
        if progress:
            progress(count, len(files))
    sealed_index = seal(json.dumps({'files': index}, sort_keys=True).encode('utf-8'), INDEX_NAME, aead)
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    partial = dest + '.part'
    digest = hashlib.sha256()
    with open(partial, 'wb') as fh:
        for chunk in [MAGIC, struct.pack('>I', len(sealed_index)), sealed_index] + parts:
            fh.write(chunk)
            digest.update(chunk)
    os.replace(partial, dest)
    return {'size': os.path.getsize(dest), 'sha256': digest.hexdigest(), 'files': len(files)}


def fingerprint(path: str) -> dict:
    """A pack's size and SHA-256, read from the file."""
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            digest.update(chunk)
    return {'size': os.path.getsize(path), 'sha256': digest.hexdigest()}


class Pack:
    """An open story.dat: its index in memory, each recording read and decrypted when
    asked for."""

    def __init__(self, path: str):
        self.path = path
        self.aead = _aead()
        try:
            with open(path, 'rb') as fh:
                if fh.read(len(MAGIC)) != MAGIC:
                    raise PackError('%s is not a story pack' % os.path.basename(path))
                head = fh.read(4)
                if len(head) != 4:
                    raise PackError('%s is damaged' % os.path.basename(path))
                size = struct.unpack('>I', head)[0]
                sealed = fh.read(size)
        except OSError as error:
            raise PackError('%s could not be read: %s' % (os.path.basename(path), error)) from None
        try:
            index = json.loads(unseal(sealed, INDEX_NAME, self.aead).decode('utf-8'))['files']
        except PackError:
            raise PackError('%s is damaged' % os.path.basename(path)) from None
        self.start = len(MAGIC) + 4 + size
        self.files = {name: (int(at), int(length)) for name, (at, length) in index.items()}
        log.info('%s holds %d recordings', os.path.basename(path), len(self.files))

    def __contains__(self, name):
        return name in self.files

    def read(self, name: str) -> bytes:
        """A recording's bytes, decrypted in memory."""
        if name not in self.files:
            raise PackError('%s is not in %s' % (name, os.path.basename(self.path)))
        at, length = self.files[name]
        with open(self.path, 'rb') as fh:
            fh.seek(self.start + at)
            part = fh.read(length)
        return unseal(part, name, self.aead)


_shared = None


def shared():
    """The pack the game plays from, once StoryData has opened it, or None."""
    return _shared


def use(pack):
    global _shared
    _shared = pack


def read(reference: str) -> bytes:
    """A packed recording's bytes, by the name StoryData gave it, PREFIX and all."""
    if _shared is None:
        raise PackError('story.dat is not open')
    return _shared.read(reference[len(PREFIX):])
