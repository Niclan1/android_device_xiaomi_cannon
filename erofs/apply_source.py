#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify/apply the pinned EROFS source patch; publishing is a separate opt-in."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kernel', type=Path, required=True)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--publish', action='store_true', help='Push only this exact commit to its declared optional branch')
    a = ap.parse_args()
    here = Path(__file__).resolve().parent
    r = json.loads((here / 'source.json').read_text())
    repo = a.kernel.resolve(strict=True)
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo or git(repo, 'status', '--porcelain'):
        raise RuntimeError('Exact clean kernel repository required; stop its builders first')
    for marker in ['index.lock', 'MERGE_HEAD', 'CHERRY_PICK_HEAD', 'rebase-apply', 'rebase-merge']:
        p = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-path', marker))
        if p.exists():
            raise RuntimeError('In-progress Git operation: ' + marker)
    tree = git(repo, 'rev-parse', 'HEAD^{tree}')
    if tree not in [r['base_tree'], r['tree']]:
        raise RuntimeError('Unexpected source tree; patch accepts only the published baseline/result')
    patch = here / r['format_patch']
    if patch.parent != here or hashlib.sha256(patch.read_bytes()).hexdigest() != r['format_patch_sha256']:
        raise RuntimeError('Pinned portable patch mismatch')
    if tree == r['base_tree']:
        if git(repo, 'rev-parse', 'HEAD') != r['base_revision']:
            raise RuntimeError('Exact published base commit required for reproducible integration')
        subprocess.run(['git', '-C', str(repo), 'apply', '--check', '--cached', str(patch)], check=True)
        if a.apply:
            env = dict(os.environ, GIT_COMMITTER_NAME=r['committer_name'], GIT_COMMITTER_EMAIL=r['committer_email'])
            subprocess.run(['git', '-C', str(repo), '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
                            'am', '--committer-date-is-author-date', str(patch)], check=True, env=env)
            tree = git(repo, 'rev-parse', 'HEAD^{tree}')
            if tree != r['tree'] or git(repo, 'status', '--porcelain'):
                raise RuntimeError('Applied tree differs; preserve it for review, do not publish')
    head = git(repo, 'rev-parse', 'HEAD')
    if a.publish:
        if tree != r['tree'] or head != r['revision']:
            raise RuntimeError('Publishing requires the exact reviewed source commit')
        ref = 'refs/heads/' + r['branch']
        subprocess.run(['git', '-C', str(repo), 'push', '--porcelain', r['repository'], head + ':' + ref], check=True)
        if git(repo, 'ls-remote', r['repository'], ref).split()[0] != head:
            raise RuntimeError('Remote source revision differs after push')
    print(json.dumps({'status': 'RESULT_SOURCE_VERIFIED' if tree == r['tree'] else 'BASELINE_VERIFIED_APPLY_PENDING',
                      'commit': head, 'tree': tree, 'published': a.publish}, indent=2))


if __name__ == '__main__':
    main()
