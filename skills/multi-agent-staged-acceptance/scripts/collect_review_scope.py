#!/usr/bin/env python3
"""Collect Git candidates and content fingerprints; semantic scope is the reviewer's job."""
import argparse
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path


def git(*args, cwd=None):
    return subprocess.check_output(['git', *args], cwd=cwd)


def changed(root, *args):
    parts = git('diff', '--name-status', '-z', '--find-renames', *args, '--', cwd=root).split(b'\0')
    result = []
    pos = 0
    while pos < len(parts) and parts[pos]:
        status = os.fsdecode(parts[pos])
        name = os.fsdecode(parts[pos + 1])
        pos += 2
        item = {'status': status, 'path': name}
        if status[0] in 'RC':
            item['old_path'] = name
            item['path'] = os.fsdecode(parts[pos])
            pos += 1
        result.append(item)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['workspace', 'staged', 'range'], default='workspace')
    parser.add_argument('--base', help='Exact base revision (required for range; no implicit HEAD~1).')
    parser.add_argument('--head', default='HEAD', help='Target revision for range mode.')
    args = parser.parse_args()
    if args.mode == 'range' and not args.base:
        parser.error('--mode range requires --base')
    if args.mode != 'range' and (args.base or args.head != 'HEAD'):
        parser.error('--base / --head are only valid with --mode range')
    root = Path(os.fsdecode(git('rev-parse', '--show-toplevel')).strip())
    head = git('rev-parse', '--verify', 'HEAD^{commit}', cwd=root).decode().strip()
    staged = changed(root, '--cached')
    unstaged = changed(root)
    untracked = [os.fsdecode(p) for p in git('ls-files', '--others', '--exclude-standard', '-z', cwd=root).split(b'\0') if p]
    if git('ls-files', '-u', cwd=root):
        parser.error('Unmerged index entries: resolve or explicitly review conflicts before acceptance.')
    base = head
    target = 'worktree'
    if args.mode == 'workspace':
        candidates = changed(root, 'HEAD')
        known = {f['path'] for f in candidates}
        candidates += [{'status': '?', 'path': p} for p in untracked if p not in known]
    elif args.mode == 'staged':
        candidates = staged
        target = 'index'
    else:
        base = git('rev-parse', '--verify', args.base + '^{commit}', cwd=root).decode().strip()
        target = git('rev-parse', '--verify', args.head + '^{commit}', cwd=root).decode().strip()
        candidates = changed(root, base, target)
    source_paths = {'staged': {f['path'] for f in staged},
                    'unstaged': {f['path'] for f in unstaged}, 'untracked': set(untracked)}
    for item in candidates:
        name = item['path']
        item['sources'] = ([key for key, paths in source_paths.items() if name in paths]
                           if args.mode == 'workspace' else [args.mode])
        if item['status'].startswith('D'):
            content = b''
            item['mode'] = None
        elif args.mode == 'workspace':
            file = root / name
            item['mode'] = oct(stat.S_IMODE(file.lstat().st_mode))
            if file.is_symlink():
                content = os.fsencode(os.readlink(file))
            elif file.is_dir():
                # Submodule contents need their own review; don't label them as hashed files.
                item['needs_separate_scope'] = True
                content = git('diff', 'HEAD', '--', name, cwd=root)
            else:
                content = file.read_bytes()
        else:
            ref = ':' + name if args.mode == 'staged' else target + ':' + name
            content = git('show', ref, cwd=root)
            entry = (git('ls-files', '--stage', '--', name, cwd=root) if args.mode == 'staged'
                     else git('ls-tree', target, '--', name, cwd=root))
            item['mode'] = entry.split()[0].decode()
        item['sha256'] = hashlib.sha256(content).hexdigest()
    drift = []
    if args.mode == 'staged':
        drift = sorted({f['path'] for f in unstaged} | set(untracked))
    elif args.mode == 'range':
        drift = sorted({f['path'] for f in changed(root, target)} | set(untracked))
    report = {'repository': str(root), 'mode': args.mode, 'base': base, 'target': target,
              'head': head, 'candidates': sorted(candidates, key=lambda f: f['path']),
              'empty': not candidates, 'worktree_matches_target': not drift,
              'worktree_drift': drift, 'acceptance_proven': False,
              'note': 'Candidates only. Map diff hunks to the spec, record exclusions and related unchanged code. Collection is not test or acceptance evidence.'}
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
