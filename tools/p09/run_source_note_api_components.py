"""Fixed v11 source API suite + two exact stored joins, serial and non-Native."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

import run_stored_note_kind_components as shared

c, a = shared.c, shared.a
OUTPUT = 'implementation/p09/evidence/p09-361-source-note-api-components016.v1.json'
SOURCES = ('crates/product-cli/tests/reference_source_product.rs',
           'crates/product-cli/tests/reference_source_product/caption_state.rs',
           'crates/product-cli/tests/reference_source_product/note_selection.rs')
STORED_TESTS = {
    'actual_import::source_note_conversion::stored_note_kind_reference_source_api_json_builds_requests_and_rejects_foreign_stale_or_revoked_access',
    'actual_import::source_note_conversion::stored_note_kind_original_nine_sources_convert_six_and_reject_three_without_rewriting_history',
}
CARGO = r'D:\devdata\Rustup\toolchains\1.96.0-x86_64-pc-windows-msvc\bin\cargo.exe'


def inventory(check):
    return shared.source_inventory(check) | set(SOURCES)


def run_one(label, args, expected, guard, env, row, *, observe_capture=None):
    step = dict(stage=label, cleanup=False)
    row['steps'].append(step)
    owned = capture = None
    begin = announcement = time.monotonic()
    try:
        print(json.dumps(dict(stage=label, state='ONE_OWNED_CARGO_STARTING')), flush=True)
        owned = shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[CARGO],
            cwd=c.ROOT, checkpoint=guard.check, env=env)
        capture = shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check()
            c.require(time.monotonic() - begin < 300, 'STOP_SOURCE_NOTE_API_COMMAND_DEADLINE')
            try:
                stdout, stderr = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                account = owned.observe()
                if time.monotonic() - announcement >= 15:
                    if observe_capture is not None:
                        step['bounded_output_observation'] = observe_capture(capture, expected)
                        print(json.dumps(dict(stage=label, bounded_output_observation=step['bounded_output_observation'])), flush=True)
                    s = guard.samples[-1]
                    print(json.dumps(dict(stage=label, elapsed=round(time.monotonic()-begin, 1),
                        system_CPU=s['system_cpu_percent'], available_RAM_percent=s['available_ram_percent'],
                        job_private_percent=account['peak_job_private_percent'], job_cpu_seconds=account['job_cpu_seconds'])), flush=True)
                    announcement = time.monotonic()
        step.update(exit_code=owned.returncode, stdout_bytes=len(stdout.encode()), stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(), stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED|ignored)$', stdout),
            summaries=[line for line in stdout.splitlines() if line.startswith('test result:')],
            diagnostics=[line for line in stderr.splitlines() if line.startswith(('error:', 'error[', 'warning:', 'warning['))][:20],
            locations=re.findall(r'(?m)^\s*-->\s*(crates/[A-Za-z0-9_./-]+\.rs):([0-9]+):([0-9]+)', stderr.replace('\\', '/')),
            panic_locations=re.findall(r'panicked at ([A-Za-z0-9_./-]+:[0-9]+:[0-9]+)', (stdout+stderr).replace('\\', '/')),
            safe_error_variants=re.findall(r'(?m)^Error: ([A-Za-z0-9_]+)', stdout+stderr))
        c.require(step['exit_code'] == 0, 'SOURCE_NOTE_API_COMMAND_FAILED')
        c.require(len(step['tests']) == len(expected) and {name for name,status in step['tests']} == expected
                  and all(status == 'ok' for name,status in step['tests']), 'EXACT_SOURCE_NOTE_API_EXPECTED_TESTS_NO_SKIPS')
    finally:
        try:
            if observe_capture is not None and capture is not None:
                step['bounded_output_observation'] = observe_capture(capture, expected)
        finally:
            if owned is not None:
                owned.kill(); owned.wait(timeout=2)
                if capture is not None: capture.close()
                owned.close(); step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)
        step['elapsed_seconds'] = round(time.monotonic()-begin, 3)


def main():
    c.require(not (c.ROOT/OUTPUT).exists(), 'SOURCE_NOTE_API_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_SOURCE_NOTE_API_COMPONENTS', steps=[], actual_Hangul_or_COM=False,
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
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py': q.pin(path.relative_to(c.ROOT).as_posix())
        # The source API suite uses one locked historical HYPERLINK specimen.
        q.pin('implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')
        q.pin('fixtures/target-build/p09-24-note-target-20261002-03/output/fixture-manifest.json')
        q.pin('implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json')
        for i, file in enumerate(('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'), 1):
            q.pin('fixtures/target-build/p09-24-note-target-20261002-03/output/'+file)
            for lane in ('saved','reopened'):
                q.pin(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{lane}.hwpx')
        source_tests = set()
        for name, prefix in zip(SOURCES, ('', 'joined_caption_state::', 'source_note_selection::'), strict=True):
            found = re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(', q.text(name))
            source_tests.update(prefix + name for name in found)
        c.require(len(source_tests) == 51, 'EXACT_CURRENT_SOURCE_API_FIFTY_ONE_TEST_INVENTORY')
        env = dict(os.environ, CARGO_BUILD_JOBS='1', CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true', CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true', CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16', CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0', RUST_TEST_THREADS='1', RUSTUP_AUTO_INSTALL='0')
        common = [CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli']
        print(json.dumps(dict(state='SOURCE_AND_FIXTURE_PREFLIGHT_COMPLETE', inputs=len(q.snapshots))), flush=True)
        run_one('v11_source_api_new5_and_affected46', common+['--test','reference_source_product','--','--test-threads=1'], source_tests, guard, env, row)
        run_one('api_json_stored_join_and_affected_original_lane_contract', common+['--test','form_stored_provider','--',*sorted(STORED_TESTS),'--exact','--test-threads=1'], STORED_TESTS, guard, env, row)
        c.require(inventory(guard.check) == names, 'FINAL_SOURCE_NOTE_API_INPUT_INVENTORY_DRIFT')
        q.finish(); guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_API_V11_FIVE_NEW_FORTY_SIX_AFFECTED_AND_TWO_STORED_LINKS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            source_api_tests=51, source_api_new_tests=5, source_api_affected_regressions=46,
            stored_target_tests=2, unaffected_stored_suites_reexecuted=False,
            source_schema='hwpx-agent.product.reference-source-assessment/v11', incomplete_exit_code=3,
            remaining_unresolved_stage_count=4, issuer_or_native_or_full_product_route_qualified=False,
            caller_note_import_required_for_request=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__, error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'SOURCE_NOTE_API_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']), elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()), resource_samples=guard.samples)
        samples = guard.samples
        row.update(system_CPU_max=max((s['system_cpu_percent'] for s in samples), default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples), default=None))
        if samples and all(list(s) == list(samples[0]) for s in samples):
            keys = list(samples[0]); values = [[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values] == samples, 'LOSSLESS_SOURCE_NOTE_API_RESOURCE_SAMPLES')
            row['resource_samples'] = dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, row, NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']], 'pin':pin}), flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
