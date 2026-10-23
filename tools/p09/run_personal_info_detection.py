"""373: one review index, explicit format bundle and source-bound read-only selection; new23 + affected3."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-detection373.v1.json';DRIVER='tools/p09/run_personal_info_detection.py'
BASE='implementation/p09/evidence/p09-361-compiled-personal-info-mask-receipt-hash371.v1.json'
DOCS='implementation/p09/evidence/p09-361-compiled-personal-info-mask-sync372.v1.json'
PARENT='crates/hwpx-package/src/document_import/search.rs';CORE=PARENT[:-3]+'/personal_info.rs'
ROOT_TEST='crates/hwpx-package/tests/personal_info_mask.rs';TEST='crates/hwpx-package/tests/support/personal_info_detection.rs'
LINK='#[path="support/personal_info_detection.rs"]mod detection;\n'
NEW={DRIVER,CORE,TEST};CHANGED={PARENT,ROOT_TEST}
AFFECTED={'reordered_partial_nfc_selection_is_rejected_instead_of_widened','public_metadata_has_no_original_text_pieces_or_per_value_source_hashes',
    'nonselected_text_beyond_bookmark_control_keeps_exact_original_xml'}

def inverse(q,old):
    text=q.text(PARENT);c.require(text.count('pub mod personal_info;\n')==1,'ONE_EXPLICIT_PERSONAL_INFO_DETECTION_MODULE')
    audit.inverse(text.replace('pub mod personal_info;\n',''),old[PARENT],'ALL_ORIGINAL_MATCHING_NORMALIZATION_MAPPING_AND_BUDGETS_UNCHANGED')
    text=q.text(ROOT_TEST);c.require(text.count(LINK)==1,'ONE_PERSONAL_INFO_DETECTION_CHILD_TEST_LINK')
    audit.inverse(text.replace(LINK,''),old[ROOT_TEST],'ALL25_PREVIOUS_MASK_TEST_BODIES_UNCHANGED')

def main(scratch_relative='target/p09-personal-info-detection-scratch-373'):
    c.require(not(c.ROOT/OUTPUT).exists(),'PERSONAL_INFO_DETECTION_IMMUTABLE')
    # Bounded name checks happen before importing/building test binaries or scanning the full closure.
    text=(c.ROOT/TEST).read_text(encoding='utf-8');c.require(len(text.encode())<=128*1024,'FINITE_DETECTION_TEST_SOURCE')
    cases={'detection::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
    root_names=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',(c.ROOT/ROOT_TEST).read_text(encoding='utf-8')))
    c.require(len(cases)==23 and AFFECTED<=root_names,'EXACT_NEW23_AND_AFFECTED3_TEST_NAMES')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_DETECTION',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        synthetic_markers_not_actual_personal_data=True,source_document_mutation=False,output_ingest_commit_or_publication=False,
        whole_package_personal_data_removed=False,native_format_policy_or_execution_qualified=False)
    try:
        guard.acquire();scratch=c.ROOT/scratch_relative;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'DETECTION_EARLY_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=compact.unpack(q.json(BASE));docs=q.json(DOCS)
        c.require(q.snapshots[BASE]['sha256']=='2e95bcaa81070948634a550e4b6260178768e8eff8a2aef3a823ebaeafbbc873'and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==868,'EXACT371_FULL_SOURCE_CURRENT_COMMON_MASK_BASELINE')
        c.require(q.snapshots[DOCS]['sha256']=='bf4afac8be084aecb7837434a017d8d4bedcc28f891dc64c218d92d5818656a4'and docs['cleanup'],'EXACT372_DOC_AUDIT_NO_RUNTIME_REPLAY')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW|CHANGED):
            q.pin(path)
            if path in old and path not in CHANGED:c.require(q.snapshots[path]==old[path],'ALL_OTHER_WRITERS_PROTECTION_STORED_PRODUCT_COMPILER_TESTS_AND_RESOURCE_GUARDS_UNCHANGED')
            elif path not in old:c.require(path in NEW,'ONLY_DETECTION_SOURCE_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        c.require(cases=={'detection::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))},'FRESH_NEW23_IDENTITIES_UNCHANGED')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='PERSONAL_INFO_DETECTION_PREFLIGHT',inputs=len(q.snapshots),new_cases=23,affected_cases=3)),flush=True)
        selected=cases|AFFECTED
        harness.run_one('personal_info_detection23_affected_mask3',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','personal_info_mask','--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
        tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'DETECTION23_AND_ORIGINAL_BOUNDARY3_NO_WARNINGS')
        c.require(not any(scratch.iterdir()),'DETECTION_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_PERSONAL_INFO_FORMAT_DETECTION23_AFFECTED_MASK3_NOT_NATIVE_DEFAULTS_STORED_PRODUCT_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=23,affected_cases=3,one_review_index_and_combined_match_scan=True,actual_identity_validated=False,
            next_work='current_stored_access_strict_read_only_product_then_qualified_native_format_policy_and_actual_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'PERSONAL_INFO_DETECTION_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'DETECTION_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),
            'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
