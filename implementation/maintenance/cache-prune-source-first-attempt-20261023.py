"""Reviewed one-project cache cleanup. Not cargo clean / git clean / root removal.

Retains executables, DLLs, dep-info, build-script outputs, databases, original
fixtures/evidence, source and shared runtimes. Never follows/deletes a reparse
target. A complete metadata plan must match before the first file deletion.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import project_cache_inventory as inventory

ROOT = inventory.ROOT
PLAN = ROOT/'implementation/maintenance/cache-prune-plan-20261023.v1.json'
RESULT = ROOT/'implementation/maintenance/cache-prune-result-20261023.v1.json'
SCOPES = ('target', 'fuzz/target', '.ruff_cache', 'tools')
KINDS = {'rust_incremental', 'rust_generated.pdb', 'rust_generated.rlib',
         'rust_generated.rmeta', 'rust_generated.lib', 'rust_generated.exp', 'rust_generated.obj'}
INC_SUFFIXES = {'.o', '.obj', '.bin', '.lock', '.rmeta', '.bc', '.a', '.tmp'}


def require(ok, code):
    if not ok:
        raise ValueError('PROJECT_CACHE_'+code)


class Guard:
    def __init__(self):
        self.windows = inventory.limits.Windows()
        self.samples = []
        self.last = time.monotonic()
        self.high = 0
        self.notice = self.last

    def check(self, force=False):
        now = time.monotonic()
        if force or now-self.last >= 1:
            value = self.windows.sample()
            self.samples.append(value)
            self.high = self.high+1 if value['system_cpu_percent'] >= 75 else 0
            require(value['system_cpu_percent'] < 90 and self.high < 4, 'SYSTEM_CPU_PRESSURE_STOP')
            require(value['available_ram_percent'] > 5 and value['commit_used_percent'] < 95, 'RAM_COMMIT95_STOP')
            self.last = now


def candidate(scope, relative):
    if scope in ('target', 'fuzz/target'):
        value = inventory.kind(relative)
        if value == 'rust_incremental' and relative.suffix.casefold() not in INC_SUFFIXES:
            return None
        return value if value in KINDS else None
    if scope == '.ruff_cache':
        return 'ruff_cache'
    if scope == 'tools' and '__pycache__' in relative.parts and relative.suffix in ('.pyc', '.pyo'):
        return 'python_bytecode'
    return None


def entries(guard):
    for scope in SCOPES:
        root = ROOT/scope
        if not root.exists():
            continue
        require(root.is_dir() and root.resolve() == root and not root.is_junction() and not root.is_symlink(), 'EXACT_SCOPE_NO_REPARSE')
        stack = [root]
        count = 0
        while stack:
            directory = stack.pop()
            require(directory.resolve() == directory and not directory.is_junction() and not directory.is_symlink(), 'DIRECTORY_ALIAS_CHANGED')
            guard.check()
            with os.scandir(directory) as listing:
                children = sorted(listing, key=lambda item: item.name.casefold())
            for item in children:
                stat = item.stat(follow_symlinks=False)
                if stat.st_file_attributes & 0x400:
                    continue  # Leave junction/symlink and its target untouched.
                path = Path(item.path)
                if item.is_dir(follow_symlinks=False):
                    stack.append(path)
                elif item.is_file(follow_symlinks=False):
                    kind = candidate(scope, path.relative_to(root))
                    if kind is not None:
                        yield path, stat, kind
                count += 1
                if count % 1000 == 0:
                    time.sleep(.01)
                    guard.check()


def snapshot(guard):
    rows = {}
    digest = hashlib.sha256()
    count = size = 0
    for path, stat, kind in entries(guard):
        relative = path.relative_to(ROOT).as_posix()
        record = (relative+'\0'+str(stat.st_size)+'\0'+str(stat.st_mtime_ns)+'\n').encode('utf-8')
        digest.update(record)
        key = kind
        item = rows.setdefault(key, dict(files=0, bytes=0))
        item['files'] += 1
        item['bytes'] += stat.st_size
        count += 1
        size += stat.st_size
        if time.monotonic()-guard.notice >= 10:
            print(json.dumps(dict(state='CACHE_PLAN_METADATA_SCAN', files=count, bytes=size)), flush=True)
            guard.notice = time.monotonic()
    return dict(metadata_sha256=digest.hexdigest(), files=count, bytes=size, categories=rows)


def publish(path, value):
    require(not path.exists() and not path.is_symlink() and not path.is_junction(), 'IMMUTABLE_RECEIPT')
    require(path.parent.resolve() == ROOT/'implementation/maintenance', 'RECEIPT_DIRECTORY')
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    require(sys.argv[1:] in (['--plan-only'], ['--execute-reviewed-plan']), 'FIXED_MODE')
    require(ROOT.resolve() == ROOT and ROOT.is_dir(), 'FIXED_PROJECT_ROOT')
    guard = Guard()
    start = time.monotonic()
    head = subprocess.check_output(['git', '-c', 'core.fsmonitor=false', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    require(head.startswith('732d555'), 'USER_REQUESTED_COMMIT_MUST_PRECEDE_CLEANUP')
    require(not subprocess.check_output(['git', 'ls-files', '--', 'target', 'fuzz/target', '.ruff_cache'], cwd=ROOT),
            'NO_TRACKED_FILES_IN_CACHE_SCOPES')
    if sys.argv[1] == '--plan-only':
        value = dict(state='REVIEWABLE_PROJECT_CACHE_FILE_PLAN', root=str(ROOT), source_commit=head,
                     scopes=list(SCOPES), deletable_kinds=sorted(KINDS), selection=snapshot(guard),
                     active_web_dist_and_node_modules_preserved=True,
                     source_evidence_exe_dll_depinfo_build_script_outputs_and_databases_preserved=True)
        publish(PLAN, value)
        print(json.dumps(dict(state=value['state'], **value['selection'])), flush=True)
        return
    require(not RESULT.exists(), 'NO_REPEATED_CLEANUP_RUN')
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    require(plan['root'] == str(ROOT) and plan['source_commit'] == head and plan['scopes'] == list(SCOPES)
            and plan['deletable_kinds'] == sorted(KINDS), 'EXACT_REVIEWED_PLAN')
    require(snapshot(guard) == plan['selection'], 'PLAN_METADATA_CHANGED_NO_DELETE')
    row = dict(state='PARTIAL_PROJECT_CACHE_CLEANUP', source_commit=head, plan=PLAN.relative_to(ROOT).as_posix(),
               free_bytes_before=shutil.disk_usage('D:/').free, deleted_files=0, deleted_logical_bytes=0,
               deleted_categories={}, skipped_files=[], source_or_evidence_deleted=False, partial_errors=[])
    try:
        for path, stat, kind in entries(guard):
            # Scope/classification repeated on the current no-follow file stat.
            require(path.is_relative_to(ROOT/'target') or path.is_relative_to(ROOT/'fuzz/target')
                    or path.is_relative_to(ROOT/'.ruff_cache') or path.is_relative_to(ROOT/'tools'), 'EXACT_DELETE_SCOPE')
            guard.check()
            now = path.stat(follow_symlinks=False)
            require(not now.st_file_attributes & 0x400 and now.st_size == stat.st_size
                    and now.st_mtime_ns == stat.st_mtime_ns, 'CURRENT_FILE_CHANGED_NO_DELETE')
            try:
                path.unlink()  # No recursive delete/move, no shell/glob, no reparse traversal.
            except OSError as error:
                row['skipped_files'].append(dict(path=path.relative_to(ROOT).as_posix(), error_type=type(error).__name__))
                continue
            row['deleted_files'] += 1
            row['deleted_logical_bytes'] += stat.st_size
            value = row['deleted_categories'].setdefault(kind, dict(files=0, bytes=0))
            value['files'] += 1
            value['bytes'] += stat.st_size
            if row['deleted_files'] % 100 == 0:
                time.sleep(.05)
                guard.check()
            if time.monotonic()-guard.notice >= 10:
                print(json.dumps(dict(state='DELETING_REBUILDABLE_CACHE_ONLY', deleted_files=row['deleted_files'],
                    deleted_logical_bytes=row['deleted_logical_bytes'], free_bytes=shutil.disk_usage('D:/').free,
                    latest_resource=guard.samples[-1] if guard.samples else None)), flush=True)
                guard.notice = time.monotonic()
        row['state'] = 'PROJECT_REBUILDABLE_CACHE_FILES_REMOVED_SHARED_ACTIVE_AND_EVIDENCE_PRESERVED'
    except (ValueError, OSError, KeyboardInterrupt) as error:
        row['partial_errors'].append(dict(error_type=type(error).__name__,
            code=error.args[0] if isinstance(error, ValueError) else 'CLEANUP_INTERRUPTED_OR_IO_ERROR'))
    finally:
        row.update(free_bytes_after=shutil.disk_usage('D:/').free, elapsed_seconds=round(time.monotonic()-start, 3),
                   resource_samples=guard.samples, one_logical_cpu=True, priority='BelowNormal')
        row['observed_drive_free_increase_bytes'] = row['free_bytes_after']-row['free_bytes_before']
        publish(RESULT, row)
        print(json.dumps({k: v for k, v in row.items() if k not in ('resource_samples', 'skipped_files', 'deleted_categories')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
