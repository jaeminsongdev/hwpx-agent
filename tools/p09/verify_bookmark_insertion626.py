"""New field insertion: preserve six exact PASS bodies; corrected/new two only, no Native."""
import hashlib,json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention
import crossref_native_startup as startup
import metadata_cpu_observer620 as attribution
SELF='tools/p09/verify_bookmark_insertion626.py'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-insertion626-audit003.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-bookmark-insertion626-audit003-forensic'
PRIOR='implementation/p09/evidence/p09-361-bookmark-request624-audit002.v1.json'
PARENT='crates/hwpx-package/src/document_import/fields.rs'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-insertion626/fields.rs'
TEST='crates/hwpx-package/tests/bookmark_source_insertion626.rs'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
FAILED='implementation/p09/evidence/p09-361-bookmark-insertion626-audit002.v1.json'
TEST_ARCHIVE='implementation/p09/source-archive/p361-bookmark-insertion626/test-audit002.rs'

def main():
    c,a,s=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--bounded-new-insertion'],'P626_BOUNDED_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P626_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    begin=time.monotonic();q=artifact=observer=None;observer_clean=True
    row=dict(state='FAILED626_SOURCE_NEW_BOOKMARK_INSERTION',steps=[],own_cpu_selection=selection,
        actual_Hancom_COM_Native_or_SQL_started=False,official249_replayed=False,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,PC_freeze_resolved=False,
        full_F11_or_product_route_or_native_display_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='369bfe6beaa25fff01bc0826796717c7ed8d08432a81a1922cdf4aa6679a6705'
            and prior['state']=='PASS624_STRICT_OWNED_BOOKMARK_REQUEST10_AND_AFFECTED20_NOT_NATIVE_CAS_OR_ROUTE'and prior['cleanup']is True,'P626_PRIOR624_UNCHANGED')
        failed=receipt.unpack(q.json(FAILED));c.require(q.snapshots[FAILED]['sha256']=='ac9d6b7ee2f64eaa459e8406caca491dc0aba1d654571e6b41bf466e683a989a'
            and failed['state']=='FAILED626_SOURCE_NEW_BOOKMARK_INSERTION'and failed['cleanup']is True,'P626_FAILED002_PRESERVED')
        retained={name for step in failed['steps']for name,status in step.get('tests',[])if status=='ok'}
        corrected={name for step in failed['steps']for name,status in step.get('tests',[])if status!='ok'}
        c.require(len(retained)==6 and corrected=={'locks_and_tracked_change_streams_reject_without_mutation'},'P626_EXACT_SIX_PASS_ONE_FAILED')
        failedpins={v['path']:v for v in failed['source_pins']}
        previous={v['path']:v for v in prior['source_pins']}
        # Reuse the previously-qualified observer, before the initial source IO.
        # It adds no WMI, thread, system sampling or warning-load process query.
        for name in ('metadata_cpu_observer620','native_process_cpu_attribution_v1','native_process_cpu_attribution_v2','native_process_cpu_attribution_v3','native_process_cpu_attribution_v4',
            'bounded_cpu_attribution_probe_v1','bounded_cpu_attribution_probe_v2','serial_observer_attribution','serial_cpu_attribution'):
            path='tools/p09/'+name+'.py';c.require(q.pin(path)==previous[path],'P626_QUALIFIED_OBSERVER_IDENTICAL')
        guard.check(force=True)
        if guard.samples[-1]['system_cpu_percent']<75:observer=attribution.Attached(guard)
        else:row['observer_unavailable_reason']='INITIAL_CPU_WARNING_NO_OPTIONAL_QUERY'
        names=inventory.inventory(guard)|includes.test_inputs((TEST,),guard)|{SELF,PARENT,ARCHIVE,TEST,CORPUS,PRIOR,'target/debug/examples/p09_crossref_capture010_probe.exe',
            'implementation/p09/evidence/p09-361-bookmark-insertion626-audit001.v1.json',
            'implementation/p09/source-archive/p361-bookmark-insertion626/verifier-audit001.py',
            'implementation/p09/source-archive/p361-bookmark-insertion626/bookmark_insertion-audit001.rs',
            'implementation/p09/source-archive/p361-bookmark-insertion626/test-audit001.rs'}
        names|={FAILED,TEST_ARCHIVE,'implementation/p09/source-archive/p361-bookmark-insertion626/verifier-audit002.py',
            'implementation/p09/source-archive/p361-bookmark-insertion626/audit002-bookmark_source_insertion626-05abb79fcef75981.exe',
            'implementation/p09/source-archive/p361-bookmark-insertion626/audit002-bookmark_source_insertion626-05abb79fcef75981.d'}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P626_ACTUAL_EIGHT_CORPUS')
        pins=[v['artifacts']['saved']for v in corpus['cases']];c.require(len(pins)==8,'P626_EIGHT')
        names|={v['path']for v in pins}
        for path in sorted(names):
            if path not in q.snapshots:q.pin(path)
        for pin in pins:c.require(q.snapshots[pin['path']]==pin,'P626_EXACT_ACTUAL_SAVED_SOURCE')
        text=q.text(PARENT);addition='pub mod bookmark_insertion;\n'
        c.require(text.count(addition)==1 and text.replace(addition,'',1)==q.text(ARCHIVE)
            and q.snapshots[ARCHIVE]['sha256']=='08f8a47b29328ce02568edf449d5ab096882543d20e9574156bd545c9196839e','P626_ORIGINAL_FIELD_IMPORT_BODIES_IDENTICAL')
        for path,pin in previous.items():
            if path.startswith('crates/')and '/src/'in path and path!=PARENT:c.require(q.snapshots[path]==pin,'P626_OTHER_EXISTING_COMPILED_RUST_UNCHANGED')
        c.require(q.snapshots['target/debug/examples/p09_crossref_capture010_probe.exe']==previous['target/debug/examples/p09_crossref_capture010_probe.exe'],'P626_CONSUMED010_UNCHANGED_NOT_EXECUTED')
        tests=q.text(TEST);c.require('#[ignore]'not in tests,'P626_NO_IGNORED')
        old=q.text(TEST_ARCHIVE);c.require(q.snapshots[TEST_ARCHIVE]['sha256']==failedpins[TEST]['sha256'],'P626_ORIGINAL_TEST_INPUT_ARCHIVE')
        def bodies(text):
            chunks=re.split(r'(?m)^#\[test\]\n',text)
            return chunks[0],{re.search(r'^fn\s+([A-Za-z0-9_]+)',v)[1]:v.strip()for v in chunks[1:]}
        oldhead,oldcases=bodies(old);head,allcases=bodies(tests)
        c.require(head==oldhead and all(allcases[v]==oldcases[v]for v in retained),'P626_EXACT_RETAINED_SIX_BODIES_AND_HELPERS')
        lowerer='crates/hwpx-package/src/document_import/fields/bookmark_insertion.rs'
        c.require(q.snapshots[lowerer]==failedpins[lowerer],'P626_TESTED_INSERTION_CODE_UNCHANGED')
        for path,pin in failedpins.items():
            if path.startswith('crates/')and '/src/'in path:c.require(q.snapshots[path]==pin,'P626_ALL_TESTED_PRODUCT_BODIES_UNCHANGED')
        cases=set(allcases)-retained;c.require(cases==corrected|{'numeric_identity_exhaustion_is_not_wrapped_or_reused'}and len(allcases)==8,'P626_CORRECTED_ONE_NEW_ONE_ONLY')
        row.update(retained_pass_tests=sorted(retained),retained_pass_source_receipt=FAILED,prior_actual_eight_test_retained_not_replayed=True,
            previous_actual_eight_test_unclosed_final_inputs_reconciled_by_current_fresh_whole_source=True,
            archived_previous_binary=q.snapshots['implementation/p09/source-archive/p361-bookmark-insertion626/audit002-bookmark_source_insertion626-05abb79fcef75981.exe'])
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P626_NO_HWP_BEFORE')
        scratch=c.ROOT/'target/p09-bookmark-insertion626-audit003-scratch';c.require(not scratch.exists(),'P626_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1');artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='P626_PREFLIGHT',retained_tests=6,corrected_and_new_tests=2,actual_eight_retained_not_replayed=True,previous624_tests_replayed=False,guards_unchanged=True)),flush=True)
        target='bookmark_source_insertion626';build_begin=time.time_ns()
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--features','p09-installed-format-fixture',
            '--message-format=short','--test',target,'--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one(target,args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P626_NO_WARNINGS')
        row['compiled_inputs']=[]
        for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
            if path.stat().st_mtime_ns<build_begin:continue
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P626_ALL_COMPILER_INPUTS_PREPINNED')
            row['compiled_inputs'].append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
        c.require(bool(row['compiled_inputs']),'P626_DEP_INFO_REQUIRED')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P626_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P626_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS626_NEW_FIELD_INSERTION_SOURCE_ENVELOPE8_ACTUAL8_NOT_FULL_F11_OR_NATIVE',new_executed_tests=2,retained_tests=6,total_unique_conditions=8,actual_saved_source_count=8,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes,original_field_import_and_other_existing_code_preserved=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P626_FAILURE_NO_RAW_VALUES')
    finally:
        if observer is not None:observer_clean=observer.close();row['resource_attribution']=observer.summary()
        guard.close();row.update(cleanup=guard.cleanup and observer_clean and all(v['cleanup']for v in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row)
        pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),diagnostics=v.get('diagnostics'),panic_locations=v.get('panic_locations'),
                compile=v.get('bounded_output_observation',{}).get('short_error_locations'),rust_codes=v.get('bounded_output_observation',{}).get('rust_error_codes'),
                failed_cases=[name for name,status in v.get('tests',[])if status!='ok'])for v in row['steps']], 'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS626_')else 2
if __name__=='__main__':raise SystemExit(main())
