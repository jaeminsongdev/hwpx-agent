"""Current24 through real product readers/semantic graphs; no Native or old tests.

One new example build only. Keep source/input and executable bindings fresh at
bundle boundaries; do not reread the whole historical evidence chain per case.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time

import named_style_verification_runtime as r
import inspect_prepared_bookmark633 as previous
import verify_source_field_semantics as dependencies

codec = previous.entry.codec

SELF = 'tools/p09/verify_prepared_bookmark636_graph.py'
EXAMPLE = 'crates/product-cli/examples/p09_prepared_bookmark_graph636.rs'
MANIFEST = 'implementation/p09/evidence/p09-361-prepared-bookmark636-product-inputs.v1.json'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark636-product-graph002.v1.json'
EXE = 'target/debug/examples/p09_prepared_bookmark_graph636.exe'
DEP = 'target/debug/examples/p09_prepared_bookmark_graph636.d'


def require(ok, code):
    r.c.require(ok, 'P636_' + code)


def inputs(check):
    names = {SELF, EXAMPLE, MANIFEST, 'Cargo.toml', 'Cargo.lock'}
    for directory, folders, files in os.walk(r.c.ROOT/'crates', followlinks=False):
        check()
        # Dependency compilation reads workspace library sources, not historical
        # fixture trees. Rust dep-info must later be a subset of these inputs.
        relative = Path(directory).relative_to(r.c.ROOT)
        if len(relative.parts) == 2:
            folders[:] = [name for name in folders if name == 'src']
        for name in folders:
            p = Path(directory)/name
            require(not p.is_symlink() and not p.is_junction(), 'SOURCE_DIRECTORY_NOT_REPARSE')
        for name in files:
            if name == 'Cargo.toml' or ('src' in relative.parts and name.endswith('.rs')):
                names.add((relative/name).as_posix())
        require(len(names) <= 4096, 'SOURCE_INVENTORY_BOUND')
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name)
            if path.is_relative_to(r.c.ROOT/'tools/p09') and path.suffix == '.py':
                names.add(path.relative_to(r.c.ROOT).as_posix())
    return names


def execute(guard, env, row):
    owned = capture = None
    start = time.monotonic()
    step = dict(stage='current24_product_and_graph_readonly', cleanup=False)
    row['steps'].append(step)
    try:
        args = [str(r.c.ROOT/EXE), '--current-captured-graph-readonly']
        owned = r.shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[args[0]],
            cwd=r.c.ROOT, checkpoint=guard.check, env=env)
        capture = r.shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check()
            require(time.monotonic()-start < 90, 'READONLY_EXECUTION_DEADLINE')
            try:
                out, err = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        step.update(exit_code=owned.returncode, stdout_bytes=len(out.encode()), stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(), stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        if err:
            # The executable only emits closed uppercase error codes, never
            # arbitrary dependency error text or source values.
            import re
            safe = err.strip()
            step['safe_error_code'] = safe if re.fullmatch(r'P636_[A-Z0-9_]{1,74}', safe) else 'P636_EXECUTION_FAILED_NO_RAW_VALUES'
        require(owned.returncode == 0 and not err, 'PRODUCT_EXECUTION_FAILED')
        return json.loads(out)
    finally:
        if owned is not None:
            # This Job contains code/build workers only, never Hancom.
            owned.kill()
            owned.wait(timeout=2)
            if capture is not None:
                capture.close()
            owned.close()
            step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)


def main():
    require(sys.argv[1:] == ['--current-captures-no-native'], 'READONLY_MODE')
    require(not (r.c.ROOT/OUTPUT).exists(), 'NEW_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = binary = None
    start = time.monotonic()
    row = dict(state='FAILED636_CURRENT24_PRODUCT_GRAPH', steps=[], actual_native_started=False,
        consumed_native_or_previous_pass_tests_replayed=False, render_qualified=False,
        target_motion_or_rename_qualified=False, full_F11_or_P09_qualified=False, P09_complete=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        names = inputs(guard.check)
        for name in sorted(names):
            q.pin(name)
        manifest = q.json(MANIFEST)
        old = codec.unpack(q.json(previous.OUTPUT), guard.check)
        require(q.snapshots[previous.OUTPUT] == manifest['provenance']
            and manifest['provenance']['sha256'] == '5b6b15d7288734478c696806dd4ae38344b1d6c1937e9e8e53e6a8aced3617df'
            and old['cleanup'] is True and len(old['cases']) == len(manifest['cases']) == 8, 'EXACT_CURRENT633_NOT_HISTORY_REPLAY')
        oldpins = {p['path']: p for p in old['source_pins']}
        require(q.pin(manifest['source']['path']) == manifest['source'] == previous.runtime.prepared.SOURCE_PIN,
            'UNCHANGED_ORIGINAL')
        require(manifest['target_name_sha256'] == old['source_observation']['bookmarks'][0]['name_sha256'], 'ACTUAL_TARGET_NAME_HASH')
        for case, observed in zip(manifest['cases'], old['cases'], strict=True):
            require(case['case_index'] == observed['case_index'] and case['display'] == observed['display']
                and case['hyperlink'] == observed['hyperlink'], 'EXACT_EIGHT_PROFILE')
            for stage, current in case['stages'].items():
                field = observed['stages'][stage]['crossrefs']
                require(len(field) == 1 and current['command_sha256'] == field[0]['command_sha256']
                    and current['display_sha256'] == field[0]['display_sha256']
                    and q.pin(current['pin']['path']) == current['pin'] == oldpins[current['pin']['path']], 'INDEPENDENT_OBSERVATION_AND_ACTUAL_BYTES')
        env = r.audit.environment()
        common = ['--offline', '--locked', '-j', '1', '-p', 'hwpx-agent-cli', '--message-format=short',
            '--config', 'profile.dev.package.hwpx-agent-cli.codegen-units=2']
        r.harness.run_one('build_current24_reader_only', [r.harness.CARGO, 'build', *common, '--example', 'p09_prepared_bookmark_graph636'],
            set(), guard, env, row, observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code'] == 0 and not row['steps'][-1]['diagnostics'], 'CLEAN_BUILD')
        binary = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        row['binary_pin'] = binary.pin(EXE)
        row['dep_info_pin'] = binary.pin(DEP)
        declared = dependencies.dependencies(r.c.ROOT/DEP)
        require({EXAMPLE, MANIFEST} <= declared and declared <= set(q.snapshots), 'ALL_COMPILED_WORKSPACE_INPUTS_BOUND')
        row['compiled_dependency_count'] = len(declared)
        result = execute(guard, env, row)
        require(result['state'].startswith('PASS636_') and len(result['observations']) == 24
            and result['native_started'] is False and result['old_trials_replayed'] is False, 'ACTUAL_PRODUCT24_COMPLETE')
        for observed, expected in zip(result['observations'],
                [(c, s) for c in manifest['cases'] for s in ('initial', 'saved', 'reopened')], strict=True):
            case, stage = expected
            require(observed['case_index'] == case['case_index'] and observed['stage'] == stage
                and observed['source'] == case['stages'][stage]['pin']
                and all(observed['graph'][key] is True for key in ('product_source_bound', 'exact_graph_target_edge',
                    'whole_source_reconstruction', 'graph_serialization_reopened')), 'ALL_CURRENT_GRAPH_PROOFS')
        row['product_observation'] = result
        require(inputs(guard.check) == names, 'FINAL_SOURCE_INVENTORY_UNCHANGED')
        binary.finish()
        q.finish()
        guard.check(force=True)
        row.update(state='QUALIFIED636_CURRENT24_PRODUCT_SOURCE_TARGET_FIELD_CACHE_AND_GRAPH_NOT_RENDER_RENAME_OR_FULL_F11',
            current_documents=24, profile_cases=8, current_source_graph_readback_qualified=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row.update(**previous.runtime.io.safe_failure(error))
        if isinstance(error, ValueError) and re.fullmatch(r'P636_[A-Z0-9_]{1,100}', str(error)):
            row['error_code'] = str(error)
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),
            fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            compiled_fresh_inputs=0 if binary is None else len(binary.snapshots),
            compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            source_pins=[] if q is None else list(q.snapshots.values()), elapsed_seconds=round(time.monotonic()-start, 3),
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        pin = previous.entry.publish(OUTPUT, row)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'cleanup', 'current_documents', 'fresh_inputs',
            'final_fresh_hashes', 'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')},
            'steps': [{k: s.get(k) for k in ('stage', 'exit_code', 'diagnostics', 'safe_error_code', 'locations')} for s in row['steps']],
            'receipt': pin}), flush=True)
    return 0 if row['state'].startswith('QUALIFIED636_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
