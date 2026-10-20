"""Short JSON files in the save folder, written so a crash never loses one.

Every file the game keeps (aidocks/plans/saves_plan.md) is one ``JsonFile``:

* A write goes to ``name.tmp`` first, flushed to disk, then the file before it is copied
  to ``name.bak``, and only then is the new one swapped in. A crash or a power cut at any
  moment leaves either the old file or the new one, never half of one.
* A file that cannot be read is set aside as ``name.damaged``, and the game carries on
  from ``name.bak``. An empty file counts as a new, empty one.
* A byte order mark, which Notepad may write, is allowed.
"""
from __future__ import annotations

import json
import logging
import os
import shutil

log = logging.getLogger('files')


def read_json(path):
    """The JSON object at ``path``, {} when the file is empty, or None when it is missing
    or is not one."""
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            text = f.read()
    except FileNotFoundError:
        return None
    except Exception:
        log.exception('could not read %s', path)
        return None
    if not text.strip():
        return {}
    try:
        value = json.loads(text)
    except Exception:
        log.exception('could not read %s', path)
        return None
    if not isinstance(value, dict):
        log.error('%s holds %s, not an object', path, type(value).__name__)
        return None
    return value


class JsonFile:
    """One JSON object in a file, with its backup."""

    def __init__(self, path, order=None):
        self.path = path
        self.backup = path + '.bak'
        self.order = order          # the key order to write in; sorted by name when None
        self.data = {}
        self.recovered = False      # read from the backup, so it wants writing back
        if not os.path.exists(path):
            return
        value = read_json(path)
        if value is None:
            damaged = path + '.damaged'
            try:
                os.replace(path, damaged)
                log.error('%s could not be read; kept as %s', path, damaged)
            except OSError:
                log.exception('could not set the damaged %s aside', path)
            value = read_json(self.backup)
            if value is not None:
                log.warning('carrying on from %s', self.backup)
            self.recovered = True
        self.data = value or {}

    def ordered(self):
        if self.order is None:
            return dict(sorted(self.data.items()))
        first = [(k, self.data[k]) for k in self.order if k in self.data]
        rest = sorted((k, v) for k, v in self.data.items() if k not in self.order)
        return dict(first + rest)

    def write(self):
        """Write the file safely. False, and logged, when it could not be written."""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            temp = self.path + '.tmp'
            with open(temp, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(self.ordered(), f, indent=1, ensure_ascii=False)
                f.write('\n')
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(self.path):
                shutil.copyfile(self.path, self.backup)
            os.replace(temp, self.path)
            self.recovered = False
            return True
        except Exception:
            log.exception('could not write %s', self.path)
            return False
