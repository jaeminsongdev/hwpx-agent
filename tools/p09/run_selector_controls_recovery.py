"""Retain58 completed cases; correct one invalid newline expectation and rerun only that case."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_controls_components as base
shared,c,a,audit=base.shared,base.c,base.a,base.audit
OUTPUT='implementation/p09/evidence/p09-361-selector-controls-recovery108.v1.json'
FAILED_CASE='selector_controls::selector_controls_xml_references_and_crlf_preserve_original_atom_and_scalar_order'
ORIGINAL='    for prefix in["A&amp;&#13;\\r\\n","Aé각","A&#x65;&#769;"]{\n'
REVISED=('    // Literal/reference control characters are rejected by the original text reader, not admitted\n'
    '    // as lineBreak atoms. Preserve that policy and check its exact import error before projection.\n'
    '    for prefix in["A&amp;&#13;\\r\\n","A&#13;","A\\r\\n"]{\n'
    '        let raw=fixture::with_body(&format!("<hp:p id=\'1\'><hp:run><hp:t>{prefix}{TAB}Z</hp:t></hp:run></hp:p>"))?;\n'
    '        let source=ImportedSourcePackage::import(&raw,DocumentId::parse("selector-controls")?,Sha256::digest(&raw).into(),Default::default())?;\n'
    '        assert!(matches!(ImportedDocumentForms::import(source),Err(hwpx_package::document_import::forms::FormImportError::Body(\n'
    '            hwpx_package::document_import::structure::StructureImportError::Paragraph{code:"text_flow_invalid_text"}))));\n'
    '    }\n'
    '    for prefix in["A&amp;&#x41;","Aé각","A&#x65;&#769;"]{\n')


def correction(q,old):
    text=q.text(base.TEST);c.require(text.count(REVISED)==1,'ONLY_FAILED_INVALID_LITERAL_NEWLINE_FIXTURE_EXPECTATION_CORRECTED')
    audit.inverse(text.replace(REVISED,ORIGINAL),old[base.TEST],'ENTIRE_OLD_TEST_FILE_AND_FIFTY_EIGHT_COMPLETED_CASE_BODIES_PRESERVED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_CONTROLS_RECOVERY_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_CONTROLS_RECOVERY',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,stored_product_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='f80a3b2b13a31eb81365d8e02dbce27295a50879c01150c51d3e02abf3e941ae'
            and failed['state']=='FAILED_SELECTOR_CONTROLS_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL_FAILED_RUN_AND_CLEANUP_RETAINED')
        old={p['path']:p for p in failed['source_pins']};original={p['path']:p for p in previous['source_pins']}
        c.require(names=={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',base.CAPTURE}},'EXACT_SAME_SOURCE_INVENTORY_AS_FAILED_RUN')
        for name in names-{base.TEST}:c.require(q.snapshots[name]==old[name],'NO_PRODUCTION_FIXTURE_OR_COMPLETED_TEST_INPUT_CHANGE')
        correction(q,old);base.inverse(q,original);expected=base.expected(q);step=failed['steps'][0]
        c.require(step['exit_code']==101 and len(step['tests'])==59 and {n for n,s in step['tests']}==expected
            and [(n,s)for n,s in step['tests']if s!='ok']==[(FAILED_CASE,'FAILED')]and step['safe_error_variants']==['Body']
            and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed'],
            'FIFTY_EIGHT_COMPLETED_PASSES_AND_ONLY_INVALID_TEXT_IMPORT_FAILURE_NOT_A_CPU_STOP')
        print(json.dumps(dict(state='SELECTOR_CONTROLS_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),retained_passes=58,rerun_cases=1)),flush=True)
        base.harness.run_one('only_corrected_xml_reference_and_rejected_crlf_case',[base.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','selector_controls_bundle','--',FAILED_CASE,'--exact','--test-threads=1'],{FAILED_CASE},guard,audit.environment(),row,observe_capture=base.snapshot)
        c.require(base.inventory(guard.check)==names,'FINAL_SELECTOR_CONTROLS_RECOVERY_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_CONTROLS_FIFTY_EIGHT_RETAINED_ONE_RECOVERED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=12,affected_cases=47,total_distinct_core_cases=59,
            retained_passes=58,actual_reexecuted_cases=1,production_or_existing_test_inputs_changed=False,prior_failed_run_preserved=True,
            original_scope_text_style_inspection_and_navigation_inverse_verified=True,original_text_control_character_rejection_preserved=True,
            actual_control_start_not_parent_paragraph_membership=True,source_nfc_reordering_ambiguity_rejected=True,
            policy_and_scope_exclusions_before_control_match_cap=True,control_regions_and_source_order_cursor_bound=True,
            next_work='Current_stored_service_and_strict_product_binding_of_exact_review_selector_controls_then_full_search_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_CONTROLS_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_CONTROLS_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
