#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Apply the three pinned source patches after syncing the release manifest.

Only the three declared checkout paths are accepted. All projects and patch
hashes are checked before any change. Already-applied clean result trees are
left alone. Other revisions, dirty trees and in-progress operations are refused.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ALLOWED = {'tools/extract-utils', 'vendor/lineage', 'external/libmnl'}


def git(repo, *args, env=None):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True, env=env).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    here = Path(__file__).resolve().parent
    config = json.loads((here / 'post-sync-patches.json').read_text())
    assert len(config['components']) == 3
    assert {r['path'] for r in config['components']} == ALLOWED
    plan = []
    for row in config['components']:
        repo = (root / row['path']).resolve()
        assert repo.is_relative_to(root), 'Repository escapes checkout root'
        assert Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() == repo
        assert not git(repo, 'status', '--porcelain'), 'Dirty source tree: ' + row['path']
        for marker in ['rebase-apply', 'rebase-merge', 'MERGE_HEAD', 'CHERRY_PICK_HEAD']:
            path = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-path', marker))
            assert not path.exists(), 'In-progress Git operation: ' + row['path']
        patch = (here / row['patch']).resolve()
        assert patch.is_relative_to(here / 'patches') and patch.is_file()
        assert hashlib.sha256(patch.read_bytes()).hexdigest() == row['patch_sha256']
        head, tree = git(repo, 'rev-parse', 'HEAD'), git(repo, 'rev-parse', 'HEAD^{tree}')
        if tree == row['result_tree']:
            plan.append((row, repo, patch, False))
        else:
            assert head == row['base_revision'] and tree == row['base_tree'], 'Unexpected source revision: ' + row['path']
            subprocess.run(['git', '-C', str(repo), 'apply', '--check', '--cached', str(patch)], check=True)
            plan.append((row, repo, patch, True))
    results = []
    for row, repo, patch, apply in plan:
        if apply:
            env = os.environ.copy()
            env.update(GIT_COMMITTER_NAME=row['committer_name'], GIT_COMMITTER_EMAIL=row['committer_email'])
            subprocess.run(['git', '-C', str(repo), '-c', 'commit.gpgsign=false',
                            '-c', 'core.hooksPath=/dev/null', 'am',
                            '--committer-date-is-author-date', str(patch)], env=env, check=True)
        assert git(repo, 'rev-parse', 'HEAD^{tree}') == row['result_tree']
        assert not git(repo, 'status', '--porcelain')
        results.append({'path': row['path'], 'status': 'APPLIED_CLEAN' if apply else 'ALREADY_APPLIED_CLEAN',
                        'commit': git(repo, 'rev-parse', 'HEAD'), 'tree': row['result_tree']})
    print(json.dumps({'status': 'THREE_POST_SYNC_SOURCE_TREES_VERIFIED', 'components': results}, indent=2))


if __name__ == '__main__':
    main()
