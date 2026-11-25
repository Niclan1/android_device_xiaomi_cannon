#!/usr/bin/env python3
"""Reconstruct the recorded release trees from exact public Git bases."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def git(project, *args, env=None):
    return subprocess.check_output(
        ["git", "-C", str(project), *args], text=True, env=env
    ).strip()


def apply(root, sources):
    pending = []
    for row in json.loads((sources / "overlays.json").read_text()):
        project = (root / row["path"]).resolve(strict=True)
        patch = (sources / row["patch"]).resolve(strict=True)
        if not project.is_relative_to(root) or not patch.is_relative_to(sources):
            raise RuntimeError("Source index contains an escaping path")
        if hashlib.sha256(patch.read_bytes()).hexdigest() != row["sha256"]:
            raise RuntimeError("Patch checksum mismatch: " + row["path"])
        if git(project, "rev-parse", "HEAD") != row["base"]:
            raise RuntimeError("Wrong source base: " + row["path"])
        if git(project, "diff", "--name-only") or git(
            project, "ls-files", "--others", "--exclude-standard"
        ):
            raise RuntimeError("Uncommitted worktree files: " + row["path"])
        tree = git(project, "write-tree")
        if tree == row["reconstructed_tree"]:
            print("Already reconstructed:", row["path"])
            continue
        if tree != git(project, "rev-parse", "HEAD^{tree}"):
            raise RuntimeError("Unexpected staged changes: " + row["path"])
        subprocess.run(
            ["git", "-C", str(project), "apply", "--check", "--index", str(patch)],
            check=True,
        )
        with tempfile.TemporaryDirectory(prefix="release-source-index-") as scratch:
            env = dict(os.environ, GIT_INDEX_FILE=str(Path(scratch) / "index"))
            git(project, "read-tree", "HEAD", env=env)
            subprocess.run(
                ["git", "-C", str(project), "apply", "--cached", str(patch)],
                env=env, check=True,
            )
            if git(project, "write-tree", env=env) != row["reconstructed_tree"]:
                raise RuntimeError("Patch does not produce recorded tree: " + row["path"])
        pending.append((project, patch, row))
    for project, patch, row in pending:
        subprocess.run(
            ["git", "-C", str(project), "apply", "--index", str(patch)], check=True
        )
        if git(project, "write-tree") != row["reconstructed_tree"]:
            raise RuntimeError("Reconstructed tree mismatch: " + row["path"])
        print("Verified reconstructed source:", row["path"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-overlays.py ANDROID_SOURCE_ROOT")
    apply(Path(sys.argv[1]).resolve(strict=True), Path(__file__).resolve().parent)
