"""XML lang/space source/export fix: 52 core/reader/mapper cases + two exact product joins."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_api_components as harness
shared,c,a=harness.shared,harness.c,harness.a
OUTPUT='implementation/p09/evidence/p09-361-note-export-context-components035.v1.json'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/source_note_file_request.rs'
CORE=('document_import_note_export','document_import_note_export_context','text_flow','document_import_notes','document_import_structure')
EXCLUDE={'ten_locked_actual_packages_import_source_backed_body_and_verify_full_fresh_graph','all_sixteen_historical_generated_and_saved_tables_match_locked_grid_oracles'}
PRODUCT={'actual_import::source_note_file_request::note_file_product_inherited_xml_context_reaches_guarded_output_and_acl_revocation_still_blocks','actual_import::source_note_file_request::note_file_product_inherited_intermediate_base_remains_explicitly_unqualified'}


def inventory(check):return shared.source_inventory(check)|{TEST}|{'crates/hwpx-package/tests/'+name+'.rs' for name in CORE}


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'NOTE_EXPORT_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_NOTE_EXPORT_CONTEXT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.pin('fixtures/target-build/p09-24-note-target-20261002-03/output/fixture-manifest.json')
        q.pin('implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json')
        for i,file in enumerate(('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'),1):
            q.pin('fixtures/target-build/p09-24-note-target-20261002-03/output/'+file)
            for lane in ('saved','reopened'):
                q.pin(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{lane}.hwpx')
        regenerated='fixtures/target-build/p09-note-id-allocation-20261019-r01/output/'
        q.pin(regenerated+'fixture-manifest.json')
        for file in ('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'):q.pin(regenerated+file)
        q.pin('implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')
        official=q.json('implementation/p09/evidence/p09-15-note-hwpx-source-qualification.v1.json')['official_source']
        for file in ('ParaListType.h','ParaListType.cpp'):
            rel='OWPML/Class/Para/'+file
            path='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/'+rel
            q.pin(path);c.require(q.snapshots[path]['sha256']==official['reviewed_sha256'][rel],'LOCKED_OFFICIAL_CONTAINER_MODEL')
        expected=set();counts={}
        for name in CORE:
            found=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+name+'.rs')))-EXCLUDE
            c.require(not expected.intersection(found),'DISTINCT_CONTEXT_COMPONENT_TEST_NAMES')
            expected|=found;counts[name]=len(found)
        c.require(counts==dict(zip(CORE,(11,6,12,11,12))),'EXACT_FIFTY_TWO_CONTEXT_AND_AFFECTED_TESTS')
        declared={'actual_import::source_note_file_request::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))}
        c.require(len(declared)==10 and PRODUCT<=declared,'EXACT_TWO_NEW_CONTEXT_PRODUCT_JOINS')
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='NOTE_FILE_EXPORT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots))),flush=True)
        args=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        for name in CORE:args+=['--test',name]
        args+=['--','--test-threads=1']
        for name in sorted(EXCLUDE):args+=['--skip',name]
        harness.run_one('xml_context_six_new_and_forty_six_affected_reader_mapper_export_cases',args,expected,guard,env,row)
        harness.run_one('two_exact_product_xml_context_joins',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(PRODUCT),'--exact','--test-threads=1'],PRODUCT,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_NOTE_EXPORT_INPUT_INVENTORY_DRIFT')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NOTE_EXPORT_XML_LANG_SPACE_SIX_NEW_FORTY_SIX_AFFECTED_TWO_PRODUCT_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,component_tests=54,new_core_context_tests=6,affected_core_tests=46,new_product_context_tests=2,
            inherited_xml_language_and_space_closed=True,original_typed_reader_and_lowerer_unchanged=True,
            removed_intermediate_xml_base_qualified=False,native_container_layout_transfer_qualified=False,
            idempotency_key_claimed=False,command_line_or_server_route_added=False,unrelated_stored_suites_reexecuted=False,
            actual_new_hwpx_file_write_and_reopen=True,original_source_preserved=True,legacy_native_failures_preserved=True,
            native_export_layout_numbering_or_format_equivalence_qualified=False,full_product_or_native_or_gate_complete=False,
            source_api_and_unaffected_stored_suites_reexecuted=False,compiled_queue_reexecuted=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_EXPORT_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_NOTE_EXPORT_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())






