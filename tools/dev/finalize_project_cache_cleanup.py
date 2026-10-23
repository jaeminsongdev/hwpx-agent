"""Finish only standard Cargo profile-root sidecars and empty cache folders.
Run AFTER the reviewed main cleanup. EXE/DLL/dep-info/source/data stay untouched.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import time

import prune_project_build_cache as primary

ROOT = primary.ROOT
OUTPUT = ROOT/'implementation/maintenance/cache-prune-profile-roots-20261023.v1.json'
SUFFIXES = {'.pdb', '.rlib', '.rmeta', '.lib', '.exp', '.obj'}


def profile_roots():
    for root in (ROOT/'target', ROOT/'fuzz/target'):
        if not root.is_dir():
            continue
        for cargo in (root, *(p for p in root.iterdir() if p.is_dir() and not p.is_symlink() and not p.is_junction())):
            for label in ('debug', 'release'):
                profile = cargo/label
                if profile.is_dir() and (profile/'deps').is_dir() and (profile/'.fingerprint').is_dir():
                    primary.require(profile.resolve() == profile and not profile.is_junction(), 'PROFILE_NO_ALIAS')
                    yield profile


def remove_empty(root, guard):
    """No recursive delete: rmdir succeeds only for already-empty directories."""
    if not root.is_dir() or root.is_symlink() or root.is_junction():
        return 0
    removed = 0
    for directory, dirs, files in os.walk(root, topdown=False, followlinks=False):
        guard.check()
        path = Path(directory)
        if path.is_symlink() or path.is_junction() or path.resolve() != path:
            continue
        try:
            guard.pace_delete(0)
            path.rmdir()
            removed += 1
        except OSError:
            pass  # Nonempty or in use means preserve, never force/remove children.
    return removed


def main():
    primary.require(sys.argv[1:] == ['--finalize-after-main'], 'FIXED_FINALIZER_MODE')
    primary.require(not OUTPUT.exists(), 'FINALIZER_ONCE')
    done = json.loads(primary.RESULT.read_text(encoding='utf-8'))
    primary.require(done['state'] == 'PROJECT_REBUILDABLE_CACHE_FILES_REMOVED_SHARED_ACTIVE_AND_EVIDENCE_PRESERVED'
                    and not done['partial_errors'] and not done['skipped_files'], 'MAIN_CLEANUP_COMPLETED_FIRST')
    guard = primary.Guard()
    start = time.monotonic()
    profiles = list(profile_roots())
    files = []
    for profile in profiles:
        for path in profile.iterdir():
            if path.is_file() and path.suffix.casefold() in SUFFIXES:
                primary.require(path.resolve() == path and not path.is_symlink() and not path.is_junction(), 'SIDECAR_NO_ALIAS')
                stat = path.stat()
                files.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=stat.st_size, modified_ns=stat.st_mtime_ns))
    row = dict(state='PARTIAL_PROFILE_ROOT_CACHE_FINALIZATION', free_bytes_before=shutil.disk_usage('D:/').free,
               planned_files=files, deleted_files=0, deleted_logical_bytes=0, empty_cache_directories_removed=0,
               partial_errors=[], active_web_node_modules_dist_and_all_evidence_preserved=True)
    try:
        for item in files:
            path = ROOT/item['path']
            current = path.stat(follow_symlinks=False)
            primary.require(path.parent in profiles and not current.st_file_attributes & 0x400
                and current.st_size == item['bytes'] and current.st_mtime_ns == item['modified_ns'], 'EXACT_CURRENT_SIDECAR')
            guard.pace_delete(current.st_size)
            path.unlink()
            row['deleted_files'] += 1
            row['deleted_logical_bytes'] += current.st_size
        for profile in profiles:
            guard.check()
            row['empty_cache_directories_removed'] += remove_empty(profile/'incremental', guard)
        row['empty_cache_directories_removed'] += remove_empty(ROOT/'.ruff_cache', guard)
        for directory, dirs, files in os.walk(ROOT/'tools', topdown=True, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(directory)/d).is_symlink() and not (Path(directory)/d).is_junction()]
            if '__pycache__' in dirs:
                row['empty_cache_directories_removed'] += remove_empty(Path(directory)/'__pycache__', guard)
                dirs.remove('__pycache__')
            guard.check()
        row['state'] = 'FINALIZED_PROFILE_ROOT_CACHES_AND_EMPTY_CACHE_FOLDERS'
    except (ValueError, OSError, KeyboardInterrupt) as error:
        row['partial_errors'].append(dict(error_type=type(error).__name__,
            code=error.args[0] if isinstance(error, ValueError) else 'FINALIZER_IO_OR_INTERRUPT'))
    finally:
        row.update(free_bytes_after=shutil.disk_usage('D:/').free, resource_samples=guard.samples,
                   elapsed_seconds=round(time.monotonic()-start, 3))
        primary.publish(OUTPUT, row)
        print(json.dumps({k: v for k, v in row.items() if k not in ('planned_files', 'resource_samples')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
