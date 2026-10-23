"""One fixed stored-note component run; never Native, queue replay or publication."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

import accept_case112_current_epoch as a
import conservative_maintenance as c
import prepared_run_closure_v1 as host
import preparation_attributed_cpu_v1 as policy
import owned_cpu_baseline_v1 as baseline
import distinct_final_sample_guard_v1 as final
from owned_sql_job import OwnedSQLJobProcess
from bounded_process_progress import BoundedProcessCapture
import successor_preparation_workspace_v1 as publisher

OUTPUT = 'implementation/p09/evidence/p09-361-stored-note-kind-components014.v1.json'
PREFIX = 'actual_import::source_note_conversion::'
TESTS = {
    'stored_note_kind_three_generated_sources_convert_with_original_authorization_and_no_publication',
    'stored_note_kind_digest_keeps_original_format_and_binds_order_source_fingerprint_kind_and_count',
    'stored_note_kind_acl_revoke_and_regrant_never_turn_retained_receipt_or_proof_into_access',
    'stored_note_kind_quarantine_and_aead_tamper_deny_every_output_exposure_and_repreparation',
    'stored_note_kind_each_foreign_scope_cannot_rebind_prepared_output_or_source',
    'stored_note_kind_final_writer_head_boundary_blocks_consumer_and_retained_candidate',
    'stored_note_kind_original_selection_protection_and_finite_limits_remain_fail_closed',
    'stored_note_kind_original_nine_sources_convert_six_and_reject_three_without_rewriting_history',
}
PACKAGES = ('product-cli', 'hwpx-package', 'domain-ir', 'foundation', 'equation-engine',
            'artifact-service', 'revision-service', 'operation-engine')
TREES = tuple('crates/' + p + '/src' for p in PACKAGES) + (
    'crates/product-cli/tests/form_stored_provider', 'crates/hwpx-package/tests/support',
    'crates/hwpx-package/examples/document_import_form_policies_support')


def source_inventory(check):
    """Bounded current dependency/test trees only, no Git, target or history scan."""
    names = {'Cargo.toml', 'Cargo.lock', 'rust-toolchain.toml',
             'crates/product-cli/tests/form_stored_provider.rs'}
    names.update('crates/' + p + '/Cargo.toml' for p in PACKAGES)
    for relative in TREES:
        root = c.ROOT / relative
        c.require(root.is_dir() and not root.is_symlink() and not root.is_junction(), 'NOTE_REGULAR_SOURCE_TREE')
        for directory, dirs, files in os.walk(root, followlinks=False):
            check()
            for name in dirs:
                child = Path(directory) / name
                c.require(not child.is_symlink() and not child.is_junction(), 'NOTE_SOURCE_DIRECTORY_LINK')
            for name in files:
                if name.endswith('.rs'):
                    names.add((Path(directory) / name).relative_to(c.ROOT).as_posix())
                    c.require(len(names) <= 2048, 'NOTE_SOURCE_INVENTORY_BOUND')
    return names


def main():
    # Refuse a second run under this evidence identity before acquiring resources.
    c.require(not (c.ROOT / OUTPUT).exists(), 'NOTE_IMMUTABLE_RUN_ALREADY_EXISTS')
    host.configure_host_policy(c)
    g = baseline.guard_type(policy.guard_type(final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = owned = capture = None
    started = time.monotonic()
    row = dict(state='FAILED_STORED_NOTE_KIND_COMPONENTS', steps=[], actual_Hangul_or_COM=False,
               Native011_executed=False, prior_Native_replayed=False, accepted_count_delta=0,
               P09_gate='OPEN', P10_started=False, output_ingest_commit_or_publication=False)
    try:
        g.acquire()
        q = a.AcceptanceReader(c.ROOT, g.check)
        inventory = source_inventory(g.check)
        for name in sorted(inventory):
            q.pin(name)
        for module in tuple(sys.modules.values()):
            value = getattr(module, '__file__', None)
            if value:
                path = Path(value).absolute()
                if path.is_relative_to(c.ROOT / 'tools/p09') and path.suffix == '.py':
                    q.pin(path.relative_to(c.ROOT).as_posix())
        # Actual fixed fixture inputs only; names never come from untrusted paths.
        generated = 'fixtures/target-build/p09-note-id-allocation-20261019-r01/output/'
        for name in ('fixture-manifest.json', 'p09-24-c01-footnote.hwpx', 'p09-24-c02-endnote.hwpx', 'p09-24-c03-footnote-endnote.hwpx'):
            q.pin(generated + name)
        old = 'fixtures/target-build/p09-24-note-target-20261002-03/output/'
        q.pin(old + 'fixture-manifest.json')
        q.pin('implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json')
        for i, file in enumerate(('p09-24-c01-footnote.hwpx', 'p09-24-c02-endnote.hwpx', 'p09-24-c03-footnote-endnote.hwpx'), 1):
            q.pin(old + file)
            for lane in ('saved', 'reopened'):
                q.pin(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{lane}.hwpx')
        args = [r'D:\devdata\Rustup\toolchains\1.96.0-x86_64-pc-windows-msvc\bin\cargo.exe',
                'test', '--offline', '--locked', '-j', '1', '-p', 'hwpx-agent-cli', '--test',
                'form_stored_provider', '--', PREFIX, '--test-threads=1']
        env = dict(os.environ, CARGO_BUILD_JOBS='1', CARGO_TARGET_DIR=str(c.ROOT / 'target'),
                   CARGO_PROFILE_TEST_OPT_LEVEL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
                   CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true', CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
                   CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true', CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
                   CARGO_PROFILE_DEV_CODEGEN_UNITS='16', CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
                   CARGO_INCREMENTAL='0', RUST_TEST_THREADS='1', RUSTUP_AUTO_INSTALL='0')
        step = dict(stage='fixed_new_stored_note_module_eight_tests', cleanup=False)
        row['steps'].append(step)
        print(json.dumps(dict(stage=step['stage'], source_inputs=len(q.snapshots), state='ONE_OWNED_CARGO_STARTING')), flush=True)
        begin = announcement = time.monotonic()
        owned = OwnedSQLJobProcess(args, windows=g.windows, allowed_executables=[args[0]], cwd=c.ROOT, checkpoint=g.check, env=env)
        capture = BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            g.check()
            c.require(time.monotonic() - begin < 300, 'STOP_STORED_NOTE_COMPONENT_DEADLINE')
            try:
                stdout, stderr = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                account = owned.observe()
                if time.monotonic() - announcement >= 15:
                    sample = g.samples[-1]
                    print(json.dumps(dict(stage=step['stage'], elapsed=round(time.monotonic()-begin, 1),
                        system_CPU=sample['system_cpu_percent'], available_RAM_percent=sample['available_ram_percent'],
                        job_private_percent=account['peak_job_private_percent'], job_cpu_seconds=account['job_cpu_seconds'])), flush=True)
                    announcement = time.monotonic()
        step.update(exit_code=owned.returncode, elapsed_seconds=round(time.monotonic()-begin, 3),
            stdout_bytes=len(stdout.encode()), stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(), stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            diagnostics=[line for line in stderr.splitlines() if line.startswith(('error:', 'error[', 'warning:', 'warning['))][:20],
            locations=re.findall(r'(?m)^\s*-->\s*(crates/[A-Za-z0-9_./-]+\.rs):([0-9]+):([0-9]+)', stderr.replace('\\', '/')),
            tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED|ignored)$', stdout),
            summaries=[line for line in stdout.splitlines() if line.startswith('test result:')],
            panic_locations=re.findall(r'panicked at ([A-Za-z0-9_./-]+:[0-9]+:[0-9]+)', (stdout+stderr).replace('\\', '/')),
            safe_error_variants=re.findall(r'(?m)^Error: ([A-Za-z0-9_]+)', stdout+stderr))
        owned.kill(); owned.wait(timeout=2); capture.close(); capture=None
        owned.close(); step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile); owned=None
        c.require(step['exit_code'] == 0, 'STORED_NOTE_COMPONENT_COMMAND_FAILED')
        c.require(len(step['tests']) == 8 and {name for name, status in step['tests']} == {PREFIX + name for name in TESTS}
                  and all(status == 'ok' for name, status in step['tests']), 'EXACT_NEW_STORED_NOTE_EIGHT_NO_SKIPS')
        c.require(source_inventory(g.check) == inventory, 'FINAL_NOTE_SOURCE_INVENTORY_DRIFT')
        q.finish(); g.check(force=True)
        row.update(state='PASS_STORED_NOTE_KIND_FRESH_SOURCE_WHOLE_PROOF_AND_FINAL_HEAD_EIGHT_COMPONENTS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes, new_contracts_passed=8,
            old_suites_reexecuted=False, preparation_input_reconstruction_reused=True,
            original_nine_converted=6, original_nine_rejected=3, new_generated_inputs=3,
            issuer_or_native_or_full_product_route_qualified=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__, error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}', message) else 'STORED_NOTE_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        if owned is not None:
            owned.kill(); owned.wait(timeout=2)
            if capture is not None: capture.close()
            owned.close(); row['steps'][-1].update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)
        g.close()
        row.update(cleanup=g.cleanup and all(s['cleanup'] for s in row['steps']), elapsed_seconds=round(time.monotonic()-started, 3),
                   source_pins=[] if q is None else list(q.snapshots.values()), resource_samples=g.samples)
        samples = g.samples
        row.update(system_CPU_max=max((s['system_cpu_percent'] for s in samples), default=None),
                   available_RAM_min_percent=min((s['available_ram_percent'] for s in samples), default=None))
        if samples and all(list(s) == list(samples[0]) for s in samples):
            keys = list(samples[0]); values = [[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys, v)) for v in values] == samples, 'LOSSLESS_NOTE_RESOURCE_SAMPLES')
            row['resource_samples'] = dict(encoding='lossless_columns_v1', columns=keys, rows=values)
        pin = publisher.publish(c.ROOT, OUTPUT, row, NS(require=c.require, exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')}, 'steps': [{k:s.get(k) for k in ('exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']], 'pin':pin}), flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
