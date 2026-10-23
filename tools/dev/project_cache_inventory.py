"""Serial, no-follow inventory of this repository's generated-cache locations.

No file deletion here. Keep raw evidence, databases, sources and toolchains out
of the scan. Records metadata only and does not open generated binary content.
"""
import ctypes
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path('D:/개발/hwpx-agent')
sys.path.insert(0, str(ROOT/'tools/p09'))
import conservative_maintenance as limits

OUTPUT = ROOT/'implementation/maintenance/cache-inventory-20261023.v1.json'
SCOPES = ['target', 'fuzz/target', 'node_modules', '.ruff_cache'] + [
    f'web/{name}/{folder}' for name in ('local-companion-mcp', 'mcp-staging', 'plan-review-staging', 'plugin-widget')
    for folder in ('node_modules', 'dist')]


def require(ok, code):
    if not ok:
        raise ValueError('CACHE_INVENTORY_'+code)


def kind(relative):
    parts = relative.parts
    for i, name in enumerate(parts):
        if name == 'incremental' and i and parts[i-1] in ('debug', 'release'):
            return 'rust_incremental'
        if name == '.fingerprint' and i and parts[i-1] in ('debug', 'release'):
            return 'rust_fingerprint'
        if name == 'build' and i and parts[i-1] in ('debug', 'release'):
            return 'rust_build_script_output'
    if 'deps' in parts or 'examples' in parts:
        suffix = relative.suffix.casefold()
        if suffix in ('.rlib', '.rmeta', '.pdb', '.d', '.exe', '.dll', '.lib', '.exp', '.obj'):
            return 'rust_generated'+suffix
    return 'other_preserve_until_classified'


def main():
    require(sys.argv[1:] == ['--inspect-only'], 'INSPECT_ONLY')
    require(ROOT.resolve() == ROOT and not ROOT.is_junction() and not ROOT.is_symlink(), 'ROOT')
    require(not OUTPUT.exists(), 'IMMUTABLE_OUTPUT')
    windows = limits.Windows()  # Changes only this process: one CPU / BelowNormal.
    rows = {}
    skipped = []
    start = last_sample = last_notice = time.monotonic()
    samples = []
    count = 0
    high = 0

    def checkpoint(force=False):
        nonlocal last_sample, last_notice, high
        now = time.monotonic()
        if force or now-last_sample >= 1:
            sample = windows.sample()
            samples.append(sample)
            high = high+1 if sample['system_cpu_percent'] >= 75 else 0
            require(sample['system_cpu_percent'] < 90 and high < 4, 'SYSTEM_CPU_PRESSURE')
            require(sample['available_ram_percent'] > 5 and sample['commit_used_percent'] < 95, 'RAM_COMMIT95')
            last_sample = now
        if now-last_notice >= 10:
            print(json.dumps(dict(state='CACHE_INVENTORY_METADATA_ONLY', files=count,
                                  elapsed_seconds=round(now-start, 1), scopes_seen=len(rows))), flush=True)
            last_notice = now

    for scope in SCOPES:
        where = ROOT/scope
        if not where.exists():
            continue
        require(where.is_dir() and not where.is_symlink() and not where.is_junction(), 'SCOPE_NO_REPARSE')
        stack = [where]
        while stack:
            directory = stack.pop()
            checkpoint()
            with os.scandir(directory) as listing:
                for item in listing:
                    path = Path(item.path)
                    stat = item.stat(follow_symlinks=False)
                    if stat.st_file_attributes & 0x400:
                        skipped.append(path.relative_to(ROOT).as_posix())
                        continue
                    if item.is_dir(follow_symlinks=False):
                        stack.append(path)
                        continue
                    require(item.is_file(follow_symlinks=False), 'REGULAR_FILE_ONLY')
                    relative = path.relative_to(where)
                    category = kind(relative) if scope in ('target', 'fuzz/target') else ('pnpm_dependencies' if scope.endswith('node_modules') else 'generated_dist_or_lint_cache')
                    top = relative.parts[0] if scope == 'target' else scope
                    key = (scope, top, category)
                    row = rows.setdefault(key, dict(scope=scope, top=top, category=category, files=0, bytes=0))
                    row['files'] += 1
                    row['bytes'] += stat.st_size
                    count += 1
                    if count % 1000 == 0:
                        time.sleep(.01)
                        checkpoint()
    time.sleep(.1)
    checkpoint(force=True)
    values = sorted(rows.values(), key=lambda row: row['bytes'], reverse=True)
    value = dict(state='INVENTORIED_PROJECT_GENERATED_LOCATIONS_NOT_DELETE_AUTHORITY', root=str(ROOT),
                 scopes=SCOPES, rows=values, skipped_reparse_points=skipped, resource_samples=samples,
                 files=count, logical_bytes=sum(row['bytes'] for row in values), elapsed_seconds=round(time.monotonic()-start, 3),
                 one_logical_cpu=True, priority='BelowNormal', source_or_evidence_deleted=False)
    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    totals = {}
    for row in values:
        totals[row['category']] = totals.get(row['category'], 0)+row['bytes']
    print(json.dumps(dict(state=value['state'], logical_bytes=value['logical_bytes'], files=count,
        elapsed_seconds=value['elapsed_seconds'], category_bytes=totals,
        system_CPU_max=max((s['system_cpu_percent'] for s in samples), default=None),
        available_RAM_min_percent=min((s['available_ram_percent'] for s in samples), default=None),
        receipt=OUTPUT.relative_to(ROOT).as_posix())), flush=True)


if __name__ == '__main__':
    main()
