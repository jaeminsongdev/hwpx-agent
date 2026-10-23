"""Fixed REF-023 source-style component run; no Hancom, queue replay or publish."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

import run_source_note_api_components as harness
shared = harness.shared
c, a = shared.c, shared.a
OUTPUT = 'implementation/p09/evidence/p09-361-source-note-style-components018.v1.json'
TEST = 'crates/hwpx-package/tests/document_import_note_style.rs'
CARGO = harness.CARGO


def inventory(check):
    return shared.source_inventory(check) | {TEST}


def main():
    c.require(not (c.ROOT / OUTPUT).exists(), 'NOTE_STYLE_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_SOURCE_NOTE_STYLE_COMPONENTS', steps=[], actual_Hangul_or_COM=False,
        Native011_executed=False, prior_Native_replayed=False, accepted_count_delta=0,
        P09_gate='OPEN', P10_started=False, output_ingest_commit_or_publication=False)
    try:
        guard.acquire(); q = a.AcceptanceReader(c.ROOT, guard.check)
        names = inventory(guard.check)
        for name in sorted(names): q.pin(name)
        for module in tuple(sys.modules.values()):
            value = getattr(module, '__file__', None)
            if value:
                path = Path(value).absolute()
                if path.is_relative_to(c.ROOT / 'tools/p09') and path.suffix == '.py':
                    q.pin(path.relative_to(c.ROOT).as_posix())
        q.pin('implementation/p09/evidence/p09-03-note-engine-source-qualification.v1.json')
        old = 'fixtures/target-build/p09-24-note-target-20261002-03/output/'
        q.pin(old + 'fixture-manifest.json')
        q.pin('implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json')
        for i, file in enumerate(('p09-24-c01-footnote.hwpx', 'p09-24-c02-endnote.hwpx', 'p09-24-c03-footnote-endnote.hwpx'), 1):
            q.pin(old + file)
            for lane in ('saved', 'reopened'):
                q.pin(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{lane}.hwpx')
        expected = set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(', q.text(TEST)))
        c.require(len(expected) == 9, 'EXACT_NINE_SOURCE_NOTE_STYLE_TESTS')
        env = dict(os.environ, CARGO_BUILD_JOBS='1', CARGO_TARGET_DIR=str(c.ROOT / 'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true', CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true', CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16', CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0', RUST_TEST_THREADS='1', RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='SOURCE_STYLE_INPUT_PREFLIGHT_COMPLETE', inputs=len(q.snapshots))), flush=True)
        harness.run_one('actual_source_note_style_nine_components',
            [CARGO, 'test', '--offline', '--locked', '-j', '1', '-p', 'hwpx-package',
             '--test', 'document_import_note_style', '--', '--test-threads=1'], expected, guard, env, row)
        c.require(inventory(guard.check) == names, 'FINAL_SOURCE_NOTE_STYLE_INPUT_INVENTORY_DRIFT')
        q.finish(); guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_STYLE_NINE_COMPONENTS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            component_tests=9, note_number_formats=22, note_line_types=18, note_widths=16,
            historical_source_observations=9, historical_native_failures_preserved=True,
            original_source_api_suite_reexecuted=False, compiled_queue_reexecuted=False,
            complete_protection_or_native_layout_qualified=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__, error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}', message) else 'NOTE_STYLE_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']), elapsed_seconds=round(time.monotonic()-started, 3),
            source_pins=[] if q is None else list(q.snapshots.values()), resource_samples=guard.samples)
        samples = guard.samples
        row.update(system_CPU_max=max((s['system_cpu_percent'] for s in samples), default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples), default=None))
        if samples and all(list(s) == list(samples[0]) for s in samples):
            keys = list(samples[0]); values = [[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys, v)) for v in values] == samples, 'LOSSLESS_NOTE_STYLE_RESOURCE_SAMPLES')
            row['resource_samples'] = dict(encoding='lossless_columns_v1', columns=keys, rows=values)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, row, NS(require=c.require, exact=lambda x, y, label:c.require(x==y, label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']], 'pin':pin}), flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
