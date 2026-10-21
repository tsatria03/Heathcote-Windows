"""Pack the story's recordings into dist\\story.dat (aidocks/plans/build_release_plan.md).

    python tools/build_pack.py

compiler.py makes story.dat by itself for every build; this makes one on its own, for a
run from source without game\\documents\\Audio\\story, which then plays from dist\\story.dat
as a build plays from the one beside its exe. Every recording is read back and compared
with its file. It never changes the repository.
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from heathcote.platform import pack  # noqa: E402

SOURCE = os.path.join(ROOT, 'game', 'documents', 'Audio', 'story')
DEST = os.path.join(ROOT, 'dist', 'story.dat')


def main() -> int:
    if not os.path.isdir(SOURCE):
        print('There is no %s to pack.' % SOURCE)
        return 1
    started = time.perf_counter()
    print('Packing %s into %s ...' % (SOURCE, DEST), flush=True)
    info = pack.write_pack(SOURCE, DEST)
    opened = pack.Pack(DEST)
    for path in pack.recordings(SOURCE):
        name = pack.recording_name(path, SOURCE)
        with open(path, 'rb') as fh:
            if opened.read(name) != fh.read():
                print('%s did not read back as it was packed.' % name)
                return 1
    print('Done: %d recordings, %.0f MB, every one read back, in %.0f seconds.'
          % (info['files'], info['size'] / 1e6, time.perf_counter() - started))
    return 0


if __name__ == '__main__':
    code = main()
    if sys.stdin.isatty():
        try:
            input('Press Enter to close this window.')
        except EOFError:
            pass
    sys.exit(code)
