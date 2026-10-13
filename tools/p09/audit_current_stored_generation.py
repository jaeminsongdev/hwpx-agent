"""Independent current-source249 closing; no build, listing, runtime or Gate PASS."""
import argparse
import json
import re
import time
from unittest.mock import patch
import prepare_current_stored_generation as s

SELF = 'tools/p09/audit_current_stored_generation.py'


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run', type=int, choices=range(1, 100), required=True)
    parser.add_argument('--audit-run', type=int, choices=range(1, 100), required=True); args = parser.parse_args()
    s.require(s.c.Path.cwd().resolve() == s.c.ROOT, 'AUDIT_REPOSITORY_CWD')
    destination = s.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-generation.terminal-audit-run{args.audit_run:02}.v1.json', fresh=True)
    resources = s.SQLRuntimeResources(); q = None; started = time.monotonic()
    out = dict(schema_version='hwpx-agent.p09-current-stored-source-generation-closing/v1', state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False, current_compiled249_qualified=False, full249_current_qualified=False,
        signed16_current_qualified=False, actual_Cargo_Rustc_SQL_Docker_native_or_child_executed=False,
        new_child_or_thread_started=False, raw_logs_included=False, product_complete=False, P09_gate='OPEN',
        A12_gate='OPEN', A13_gate='OPEN', remaining_non_permission_work_units=76,
        PC_freeze_resolved=False, resource_samples=resources.samples)
    try:
        resources.admit(); q = s.LiveSQLReader(resources); q.pin(SELF)
        with patch('subprocess.Popen', side_effect=AssertionError('P152_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run', side_effect=AssertionError('P152_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start', side_effect=AssertionError('P152_AUDIT_THREAD_FORBIDDEN')):
            name = f'implementation/p09/evidence/p09-152-current-stored-generation.prepare-run{args.run:02}.v1.json'
            row = q.json(name); out['preparation_receipt_pin'] = q.reader.snapshots[name]
            s.require(row.get('state') == s.PASS and row['source_closing_exact'] is True
                and row['mode'] == 'prepare' and row['generation'] == s.generation(args.run)
                and row['contract_tests_run'] == row['contract_tests_passed'] == 14 and row['failed_tests'] == []
                and row['current_Rust_input_count'] == 785 and row['source_test_count'] == 249
                and row['source_module_instance_count'] == 59 and row['protected_executables_exact'] == 54
                and row['original_parent_inputs_exact'] == 1185 and row['resource_stop_reason'] is None
                and row['resource_watcher_cleanup_confirmed'] is True, 'AUDIT_PREPARATION_SCOPE')
            for flag in ('current_compiled249_qualified', 'full249_current_qualified', 'signed16_current_qualified',
                    'actual_Cargo_Rustc_SQL_Docker_native_or_child_executed', 'product_complete', 'PC_freeze_resolved'):
                s.require(row.get(flag) is False, 'AUDIT_PREPARATION_NOT_RUNTIME_PROMOTED')
            s.require(row['parent_closing_pin'] == s.PARENT and row['P09_gate'] == 'OPEN', 'AUDIT_IMMUTABLE_GENERATION')
            frozen = s.inputs.inventory(row['bound_input_pins'])
            for path, pin in frozen.items(): s.require(q.pin(path) == pin, 'AUDIT_CURRENT_INPUT')
            s.require(q.pin(s.PARENT['path']) == s.PARENT, 'AUDIT_PARENT_PIN')
            parent = q.json(s.PARENT['path']); original = s.parent_scope(parent)
            s.require(all(frozen.get(n) == p for n, p in original.items()), 'AUDIT_WHOLE_PARENT_CLOSURE')
            rust = {n for n in frozen if n.startswith(('crates/', 'protocol/generated/rust/', 'tools/xtask/'))
                and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
            s.require(len(rust) == 785 and s.inputs.rust_inputs(s.c.ROOT, resources.checkpoint_io) == rust, 'AUDIT_WHOLE_RUST785')
            protected = s.protected_scope(q.json(s.BUILD), parent, original)
            s.require(row['protected_executables'] == list(protected.values()), 'AUDIT_PROTECTED54')
            s.require_fresh_output(args.run, protected)
            def read(path):
                s.require(path in frozen, 'AUDIT_MODULE_INPUT'); value = q.text(path)
                s.require(q.reader.snapshots[path] == frozen[path], 'AUDIT_MODULE_FRESH'); return value
            names, modules = s.profile.signed.previous.parent.recursive_names(read, 'stored-form-tests')
            s.profile.signed.previous.original.select_names(names)
            s.require(len(modules) == 59 and row['source_test_names'] == list(names)
                and row['source_module_instances'] == list(modules), 'AUDIT_SOURCE249_59')
            historical = q.json(s.HISTORICAL_INVENTORY)
            s.require(historical['source_test_names'] == list(names)
                and historical['source_module_instances'] == list(modules)
                and row['historical_inventory_used_for_names_only'] is True, 'AUDIT_HISTORICAL_NOT_COMPILED_PROOF')
            s.require(row['compile_recipe'] == s.recipe(args.run), 'AUDIT_EXACT_UNEXECUTED_RECIPE')
            out.update(s.contracts()); q.finish()
            out.update(state='PASS_CURRENT_RUST785_SOURCE249_CLOSING_ONLY_NOT_COMPILED_RUNTIME_SQL_OR_GATE',
                source_closing_exact=True, current_Rust_input_count=785, source_test_count=249,
                source_module_instance_count=59, protected_executables_exact=54,
                preserved_parent_EXE_input_count=sum(n.endswith('.exe') for n in original),
                historical_compiled_proof_not_promoted=True, original_parent_inputs_exact=1185,
                compile_recipe=s.recipe(args.run), compile_executor_connected=False,
                host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['resource_samples']),
                host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['resource_samples']))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else 'P152_AUDIT_REDACTED_FAILURE'
        out['error_code'] = code if re.fullmatch('[A-Za-z0-9_]{1,160}', code) else 'P152_AUDIT_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try: q.finish(); out['source_closing_exact'] = True
            except (ValueError, OSError): out['final_freshness_error'] = 'P152_AUDIT_FINAL_FRESHNESS'
        s.finish_watcher(resources, out); out['resource_stop_reason'] = resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'): out['state'] = 'FAILED_NOT_ACCEPTED'
        if q is not None: out['IO'] = q.summary(); out['bound_input_pins'] = list(q.reader.snapshots.values())
        out['wall_seconds'] = round(time.monotonic()-started, 4)
        with destination.open('x', encoding='utf-8') as stream: json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'contract_tests_passed', 'source_test_count',
            'protected_executables_exact', 'error_code', 'wall_seconds', 'resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] else 2


if __name__ == '__main__': raise SystemExit(main())
