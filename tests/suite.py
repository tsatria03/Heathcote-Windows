"""Run every test in tests/case, several at once, and keep the results.

    python tests/suite.py               every test file
    python tests/suite.py keymap menus  just these
    python tests/suite.py -j 1          one at a time

Each file runs as its own process, with its own throwaway save and its own silence
(tests/case/_quiet.py). A file that fails is run once more on its own, so a test that only
fails while the others run is told apart from a broken one. Every result goes to
tests/results/results-<date>-<n>.txt, which git ignores, and the exit code is 1 if anything
failed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, 'case')
RESULTS = os.path.join(HERE, 'results')
COUNT = re.compile(r'^(\d+)/(\d+) passed$', re.M)


def files(names):
    found = sorted(f[:-3] for f in os.listdir(CASES) if f.endswith('.py') and not f.startswith('_'))
    if not names:
        return found
    names = [n[:-3] if n.endswith('.py') else n for n in names]
    names = [n if n in found or n.startswith('test_') else 'test_' + n for n in names]
    missing = [n for n in names if n not in found]
    if missing:
        raise SystemExit('No such test file: %s' % ', '.join(missing))
    return names


def run_one(name):
    started = time.perf_counter()
    done = subprocess.run([sys.executable, os.path.join(CASES, name + '.py')], cwd=os.path.dirname(HERE),
                          capture_output=True, text=True, encoding='utf-8', errors='replace')
    output = done.stdout + done.stderr
    match = COUNT.search(output)
    passed, total = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
    ok = done.returncode == 0 and match is not None and passed == total
    return {'name': name, 'ok': ok, 'passed': passed, 'total': total, 'output': output,
            'seconds': time.perf_counter() - started}


def results_path():
    os.makedirs(RESULTS, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    n = 1
    while os.path.exists(os.path.join(RESULTS, 'results-%s-%d.txt' % (stamp, n))):
        n += 1
    return os.path.join(RESULTS, 'results-%s-%d.txt' % (stamp, n))


def main(argv=None):
    parser = argparse.ArgumentParser(prog='suite.py', description='run the tests in tests/case')
    parser.add_argument('names', nargs='*', help='test files to run, with or without test_ and .py')
    parser.add_argument('-j', type=int, default=8, help='how many files run at once')
    args = parser.parse_args(argv)
    names = files(args.names)
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.j)) as pool:
        results = list(pool.map(run_one, names))
    for i, r in enumerate(results):
        if not r['ok']:
            again = run_one(r['name'])
            again['rerun'] = True
            results[i] = again
    seconds = time.perf_counter() - started
    passed = sum(r['passed'] for r in results)
    total = sum(r['total'] for r in results)
    bad = [r for r in results if not r['ok']]

    lines = []
    for r in results:
        state = 'ok' if r['ok'] else 'FAILED'
        note = ', passed when run alone' if r.get('rerun') and r['ok'] else ''
        lines.append('%s: %s, %d of %d, %.1f seconds%s' % (r['name'], state, r['passed'], r['total'],
                                                         r['seconds'], note))
    summary = '%d of %d tests passed across %d files in %.1f seconds.' % (passed, total, len(results), seconds)
    if bad:
        summary += ' Failed: %s.' % ', '.join(r['name'] for r in bad)
    path = results_path()
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(summary + '\n\n' + '\n'.join(lines) + '\n')
        for r in results:
            f.write('\n--- %s\n%s' % (r['name'], r['output'] if not r['ok'] else
                                     '\n'.join(l for l in r['output'].splitlines() if l.startswith('ok ')) + '\n'))
    for line in lines:
        print(line)
    print(summary)
    print('The results are in %s.' % os.path.relpath(path, os.path.dirname(HERE)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
