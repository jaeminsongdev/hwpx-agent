"""P151 runtime admission only. Old receipts and SQL driver files stay immutable."""
import base64
import hashlib
import build_durable_negative_probe as build
import signed_durable_sql_contract as prior

c=build.c
BUILD_PIN=dict(path='implementation/p09/evidence/p09-151-runtime-build.actual-run01.v1.json',
    bytes=894137,sha256='a34b54014db8df958b2a39590b2374941df708ff591c26f49c938e44fc9f8ecc')
CLOSING_PIN={"path":"implementation/p09/evidence/p09-151-runtime-build.terminal-audit-run01.v1.json","bytes":308783,"sha256":"422703400cb68e322643557157f9cdc09d4c557df32b031c59d8540e5f735f8d"}
ARCHIVE=prior.ARCHIVE
DRIVER=prior.DRIVER
ADDED_RUST=prior.ADDED_RUST|{build.parent.SOURCE}
SOURCE_COUNT=846
SCHEME='p151_current_DS06_runtime_r01'
SOURCES=['tools/p09/durable_negative_sql_contract.py','tools/p09/durable_negative_sql_driver.py',
    'tools/p09/verify_durable_negative_sql_admission.py','tools/p09/tests/test_durable_negative_sql_admission.py',
    'tools/p09/signed_durable_sql_root.py',ARCHIVE]


def require(ok,code):c.require(ok,'SQL_P151_'+code)


def accepted(row):
    require(row['state']==build.PASS and row['current_build_binding_accepted'] is True
        and row['runtime_only_build_accepted'] is True and row['source_freeze_exact_after'] is True
        and row['protected_executables_exact_after'] is True and row['cleanup_confirmed'] is True
        and row['owned_tree_empty'] is True and row['exit_code']==0 and row['stop_reason'] is None,'CURRENT_BUILD')
    require(row['provided_driver_generation']=='P151_R31_CURRENT_DS06_NON_TEST'
        and row['whole_workspace_Rust_input_count']==785 and row['protected_executables_expected']==53
        and row['parent_example_audit_pin']==build.AUDIT_PIN,'GENERATION')
    require(row['policy']==c.POLICY and row['worker_created'] and row['job_assigned'] and row['writer_authorized']
        and row['post_hash_stable_admission_revalidated'] and row['compile_admission_RAM_percent']==15,'GO_POLICY')
    require(row['build_result']['catalog_profile']==dict(opt_level='1',debuginfo='line-tables-only',
        debug_assertions=True,overflow_checks=True,test=False)
        and row['current_dev_package_profile_config']==list(build.DEV_CONFIG)
        and row['original_test_package_profile_config']==list(build.parent.original.base.CONFIG),'PROFILE')
    require(row['actual_SQL_or_native_executed'] is False and row['current_SQL_admission_qualified'] is False
        and row['actual_SQL_metadata_or_signed_consumer_qualified'] is False and row['old_SQL_admission_modified'] is False
        and row['product_complete'] is False and row['P09_gate']=='OPEN','NO_PROMOTION')
    limits=row['owned_limits_readback'];final=row['job_final']
    require(limits['verified'] and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384 and limits['kill_on_close'] and limits['breakaway_disabled']
        and limits['active_process_limit']==16 and final['active_processes']==0 and final['owned_processes']==[],'LIMITS')
    capture=row['capture_diagnostics'];proof=row['build_result']['validated_stream']
    require(capture['error_code'] is None and capture['per_stream_limit_bytes']==32768
        and not capture['raw_log_content_included'] and proof['all_records_validated'] is True
        and proof['raw_output_truncated'] is False and proof['raw_logs_included'] is False
        and proof['stdout_record_buffer_limit']==proof['stderr_total_limit']==32768
        and proof['stdout_total_JSON_IO_budget']==16*1024*1024,'STREAM')
    source=prior.inventory(row['source_freeze']);protected=prior.inventory(row['protected_executables'])
    require(len(protected)==53,'PROTECTED53')
    exe=prior.legacy.inputs.pin_shape(row['executable_pin'])
    require(exe['path']==build.executable_name(1) and exe['path'] not in protected,'EXACT_RUNTIME')
    return source,protected,exe


def bind_probe_build(reader,build_file):
    require(prior.legacy.direct_name(build_file)==BUILD_PIN['path'],'ONLY_FIXED_CURRENT_BUILD')
    require(isinstance(CLOSING_PIN,dict),'CLOSING_NOT_INSTALLED')
    require(reader.pin(BUILD_PIN['path'])==BUILD_PIN and reader.pin(CLOSING_PIN['path'])==CLOSING_PIN,'IMMUTABLE_RECEIPTS')
    row=reader.json(BUILD_PIN['path']);all_source,protected,exe=accepted(row)
    closing=reader.json(CLOSING_PIN['path'])
    require(closing['state']=='PASS_CURRENT_DS06_RUNTIME_BUILD_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
        and closing['source_closing_exact'] and closing['actual_receipt_pin']==BUILD_PIN
        and closing['executable_pin']==exe and closing['contract_tests_passed']==22
        and closing['protected_executables_exact']==53 and closing['current_Rust_input_count']==785,'CLOSING')
    for pin in [*all_source.values(),*protected.values(),exe]:
        require(reader.pin(prior.legacy.direct_name(pin['path']))==pin,'CURRENT_INPUT_DRIFT')
    for pin in closing['bound_input_pins']:require(reader.pin(pin['path'])==pin,'CLOSING_INPUT_DRIFT')
    rust={n for n in all_source if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==785 and build.parent.original.rust_inputs(c.ROOT,reader.resources.checkpoint_io)==rust,'WHOLE_RUST785')
    old_pin=prior.legacy.CURRENT_BUILD_PIN
    require(reader.pin(old_pin['path'])==old_pin,'LEGACY_IMMUTABLE')
    old=reader.json(old_pin['path']);original=prior.inventory(old['source_freeze'])
    require(len(original)==842 and rust-set(original)==ADDED_RUST,'EXACT_FOUR_ADDED_RUST')
    names=set(original)|ADDED_RUST
    require(len(names)==SOURCE_COUNT and names<=set(all_source),'SOURCE_VIEW846')
    for item in reader.json(ARCHIVE)['files']:
        raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
        require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
            and reader.pin(pin['path'])==pin,'ORIGINAL_SQL_HELPERS_WHOLE_BYTES')
    binding=dict(scheme=SCHEME,receipt_pin=BUILD_PIN,closing_audit_pin=CLOSING_PIN,
        helper_paths=sorted(set(all_source)-names),actual_SQL_qualified=False,original_driver_archive=ARCHIVE,
        exact_added_Rust_paths=sorted(ADDED_RUST),compiled_source_count=846,current_Rust_input_count=785,
        required_check_count=39,old_admission_restamped=False)
    view=dict(source_freeze=[all_source[n] for n in sorted(names)],protected_executables=list(protected.values()),
        whole_workspace_Rust_input_coverage_enforced=True,historical_parent_archive_verified=True,
        current_build_consumption_view=True,original_build_receipt_pin=BUILD_PIN)
    return view,exe,binding


def consumer_sources(binding):
    require(binding.get('scheme')==SCHEME and binding.get('actual_SQL_qualified') is False
        and binding.get('receipt_pin')==BUILD_PIN and binding.get('closing_audit_pin')==CLOSING_PIN
        and binding.get('compiled_source_count')==846 and binding.get('current_Rust_input_count')==785
        and binding.get('required_check_count')==39,'CONSUMER_GENERATION')
    return list(dict.fromkeys([*SOURCES,BUILD_PIN['path'],CLOSING_PIN['path'],*binding['helper_paths']]))
