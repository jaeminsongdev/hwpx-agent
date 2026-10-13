"""P150 current build consumption; historical build/driver receipts are immutable."""
import base64
import hashlib
import re
import build_signed_durable_probe as build
import issuer_sql_build_contract as legacy

c=build.c
BUILD_PIN=dict(path='implementation/p09/evidence/p09-150-durable-probe-build.actual-run05.v1.json',
    bytes=370635,sha256='fb766c4981569a0f6d8140c10e066d23a01dc5e5da004616a602d2a684280ce2')
CLOSING_PIN=dict(path='implementation/p09/evidence/p09-150-durable-probe-build.terminal-audit-run01.v1.json',
    bytes=209242,sha256='868bfbc5ca79b71f85863bcb6236e56b913c9b1257841f71d954e22e9edd6257')
ARCHIVE='implementation/p09/source-archive/p09-150-pre-durable-SQL-consumer-r29/source-preimages.v1.json'
DRIVER='tools/p09/run_formula_issuer_live_sql_probe.py'
ADDED_RUST=frozenset({'crates/hwpx-package/src/call_local_xml.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/corpus/changed/cost_profile.rs',
    'crates/product-cli/examples/formula_issuer_product_postgres_probe/durable.rs'})
SOURCE_COUNT=845
SOURCES=['tools/p09/signed_durable_sql_contract.py','tools/p09/signed_durable_sql_root.py',
    'tools/p09/signed_durable_sql_driver.py','tools/p09/tests/test_signed_durable_sql_connection.py',
    'tools/p09/run_signed_durable_sql_probe.py','tools/p09/tests/test_signed_durable_sql_execution.py',ARCHIVE,
    'implementation/p09/source-archive/p09-150-pre-SQL-execution-test-closure-r29/source-preimages.v1.json',
    'implementation/p09/source-archive/p09-150-pre-SQL-light-fixture-fix-r29/source-preimages.v1.json',
    'implementation/p09/source-archive/p09-150-pre-SQL-policy-key-fixture-fix-r29/source-preimages.v1.json']


def require(ok,code):c.require(ok,'SQL_BUILD_DURABLE_'+code)


def inventory(rows):
    require(isinstance(rows,list) and 1<=len(rows)<=2048,'INPUT_SCOPE')
    out={p['path']:legacy.inputs.pin_shape(p) for p in rows}
    require(len(out)==len(rows),'INPUT_DUPLICATE');return out


def accepted(row):
    require(row['state']==build.PASS and row['current_build_binding_accepted'] is True
        and row['source_freeze_exact_after'] is True and row['protected_executables_exact_after'] is True
        and row['cleanup_confirmed'] is True and row['owned_tree_empty'] is True
        and row['exit_code']==0 and row['stop_reason'] is None,'CURRENT_BUILD_NOT_ACCEPTED')
    require(row['policy']==c.POLICY and row['worker_created'] and row['job_assigned'] and row['writer_authorized']
        and row['post_hash_stable_admission_revalidated'] and row['compile_admission_RAM_percent']==15,'GO_AND_POLICY')
    require(row['build_result']['catalog_profile']==dict(opt_level='1',debuginfo='line-tables-only',
        debug_assertions=True,overflow_checks=True,test=False),'NONTEST_PROFILE')
    require(row['current_dev_package_profile_config']==list(build.DEV_CONFIG)
        and row['original_test_package_profile_config']==list(build.original.base.CONFIG),'COMMAND_ONLY_PROFILE')
    require(row['actual_SQL_or_native_executed'] is False and row['current_SQL_admission_qualified'] is False
        and row['old_SQL_admission_modified'] is False and row['product_complete'] is False
        and row['P09_gate']=='OPEN','PHASE_SCOPE')
    limits=row['owned_limits_readback'];final=row['job_final']
    require(limits['verified'] and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384 and limits['kill_on_close'] and limits['breakaway_disabled']
        and limits['active_process_limit']==16 and final['active_processes']==0 and final['owned_processes']==[],'LIMITS_AND_CLEANUP')
    capture=row['capture_diagnostics'];proof=row['build_result']['validated_stream']
    require(capture['error_code'] is None and capture['per_stream_limit_bytes']==32768
        and not capture['raw_log_content_included'] and proof['all_records_validated'] is True
        and proof['raw_output_truncated'] is False and proof['raw_logs_included'] is False
        and proof['stdout_record_buffer_limit']==proof['stderr_total_limit']==32768
        and proof['stdout_total_JSON_IO_budget']==16*1024*1024,'WHOLE_STREAM_PROOF')
    source=inventory(row['source_freeze']);protected=inventory(row['protected_executables'])
    require(len(protected)==51 and row['whole_workspace_Rust_input_count']==784,'CURRENT_INPUT_COVERAGE')
    exe=legacy.inputs.pin_shape(row['executable_pin'])
    require(exe['path']==build.executable_name(5) and exe['path'] not in protected,'FRESH_RUNTIME_EXE')
    return source,protected,exe


def bind_probe_build(reader,build_file):
    require(legacy.direct_name(build_file)==BUILD_PIN['path'],'ONLY_FIXED_CURRENT_BUILD')
    require(reader.pin(BUILD_PIN['path'])==BUILD_PIN and reader.pin(CLOSING_PIN['path'])==CLOSING_PIN,'IMMUTABLE_RECEIPTS')
    row=reader.json(BUILD_PIN['path']);all_source,protected,exe=accepted(row)
    closing=reader.json(CLOSING_PIN['path'])
    require(closing['state']=='PASS_CURRENT_BUILD_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
        and closing['source_closing_exact'] and closing['current_build_receipt_pin']==BUILD_PIN
        and closing['executable_pin']==exe and closing['tests_passed']==22
        and closing['protected_executables_exact']==51,'CLOSING_AUDIT')
    for pin in [*all_source.values(),*protected.values(),exe]:
        require(reader.pin(legacy.direct_name(pin['path']))==pin,'CURRENT_INPUT_DRIFT')
    rust={n for n in all_source if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==784 and build.original.rust_inputs(c.ROOT,reader.resources.checkpoint_io)==rust,'WHOLE_RUST_INPUTS')
    require(reader.pin(legacy.CURRENT_BUILD_PIN['path'])==legacy.CURRENT_BUILD_PIN,'LEGACY_RECEIPT_PRESERVED')
    old=reader.json(legacy.CURRENT_BUILD_PIN['path']);original=inventory(old['source_freeze'])
    require(len(original)==842 and rust-set(original)==ADDED_RUST,'EXACT_ADDED_THREE')
    names=set(original)|ADDED_RUST;require(len(names)==SOURCE_COUNT and names<=set(all_source),'COMPILED_SOURCE_VIEW')
    archive=reader.json(ARCHIVE)
    for item in archive['files']:
        raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
        require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
            and reader.pin(pin['path'])==pin,'ORIGINAL_DRIVER_WHOLE_BYTES')
    helpers=sorted(set(all_source)-names)
    binding=dict(scheme='p150_current_runtime_r05',receipt_pin=BUILD_PIN,closing_audit_pin=CLOSING_PIN,
        helper_paths=helpers,actual_SQL_qualified=False,original_driver_archive=ARCHIVE,
        exact_added_Rust_paths=sorted(ADDED_RUST),compiled_source_count=SOURCE_COUNT)
    # Explicit consumption VIEW, not a modified/restamped historical/build receipt.
    view=dict(source_freeze=[all_source[n] for n in sorted(names)],protected_executables=list(protected.values()),
        whole_workspace_Rust_input_coverage_enforced=True,historical_parent_archive_verified=True,
        current_build_consumption_view=True,original_build_receipt_pin=BUILD_PIN)
    return view,exe,binding


def consumer_sources(binding):
    require(binding.get('scheme')=='p150_current_runtime_r05' and binding.get('actual_SQL_qualified') is False
        and binding.get('receipt_pin')==BUILD_PIN and binding.get('compiled_source_count')==845,'CONSUMER_PHASE')
    return list(dict.fromkeys([*SOURCES,BUILD_PIN['path'],CLOSING_PIN['path'],*binding['helper_paths']]))
