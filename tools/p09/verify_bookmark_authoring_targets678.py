"""Shared point/block source target selection, not writer or Native qualification."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_bookmark_authoring_targets678.py'
TEST='crates/hwpx-package/tests/bookmark_authoring_targets676.rs'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark-import675-product004.v1.json'
READBACK='implementation/p09/evidence/p09-361-block-bookmark-source673-readback001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-authoring-targets678-product002.v1.json'
FAILED='implementation/p09/evidence/p09-361-bookmark-authoring-targets678-product001.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-authoring-targets678-product001/'

def require(ok,code):
    if not ok:raise ValueError('TARGET678_'+code)

def main():
    require(sys.argv[1:]==['--changed-target-selection-only']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=None;start=time.monotonic();row=dict(state='FAILED678_BOOKMARK_AUTHORING_TARGET_SELECTION',steps=[],Native_started=False,
        previous_Native_or_product_tests_replayed=False,writer_or_Content_Native_positive_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR));readback=p.codec.unpack(q.json(READBACK))
        require(q.snapshots[PRIOR]['sha256']=='a3b75173726202a493b6d78051e679ed4e1b9d0b779b69ad06b6a59eda78ea6b'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==907
            and prior['total_unique_product_conditions']==11,'PRESERVED_CORE_IMPORT675')
        require(q.snapshots[READBACK]['sha256']=='cc9022ab8a90d50152ca5926c7494b6e2de8faf7af3f18ec6f197ade6b23b8ad'
            and readback['cleanup']is True and readback['documents']==2,'EXACT_NATIVE_SOURCE_READBACK')
        for pin in prior['source_pins']:
            path=pin['path']
            if path=='crates/hwpx-package/src/document_import/fields.rs':
                q.pin(path);text=q.text(path)
                inverse=text.replace('pub mod bookmark_authoring_targets;\n','')
                require(text.count('pub mod bookmark_authoring_targets;')==1 and hashlib.sha256(inverse.encode()).hexdigest()==pin['sha256'],
                    'ONLY_NEW_SOURCE_TARGET_MODULE_DECLARATION')
            elif path.startswith('crates/')and Path(path).suffix in('.rs','.toml'):
                require(q.pin(path)==pin,'PRIOR_PRODUCT_AND_TEST_RUST_UNCHANGED')
        failed=p.codec.unpack(q.json(FAILED))
        require(q.snapshots[FAILED]['sha256']=='334eaab1c9bd50fa21f8907e96347f45e455112ddad3938b8449f474be03798f'
            and failed['cleanup']is True and failed['steps'][0]['exit_code']==101
            and failed['steps'][0]['tests']==[]
            and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0433'],
            'PRESERVED_FIRST_COMPILE_FAILURE_NO_TEST_EXECUTION')
        module='crates/hwpx-package/src/document_import/fields/bookmark_authoring_targets.rs'
        for pin in failed['source_pins']:
            if pin['path']in(SELF,module):
                saved=q.pin(ARCHIVE+Path(pin['path']).name)
                require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_FIRST_FAILURE_CODE_ARCHIVED')
            else:require(q.pin(pin['path'])==pin,'OTHER_TARGET_CODE_AND_TESTS_UNCHANGED')
        require(q.text(module)==q.text(ARCHIVE+Path(module).name).replace('hex::encode(Sha256::digest(&state))',
            'super::super::hex_digest(Sha256::digest(&state).into())',1),'ONLY_USE_EXISTING_PRODUCT_HEX_HELPER')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,),guard)|{SELF,TEST,PRIOR,READBACK,FAILED}
        for stage in readback['stages'].values():require(q.pin(stage['source']['path'])==stage['source'],'ACTUAL_NATIVE_BYTES')
        for name in sorted(names):q.pin(name)
        tests=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        require(len(tests)==12 and '#[ignore]'not in q.text(TEST),'TWELVE_NEW_TARGET_CONDITIONS')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','bookmark_authoring_targets676',
            '--message-format=short','--',*sorted(tests),'--exact','--test-threads=1']
        begin=time.time_ns();r.harness.run_one('source_point_block_target_selection12_no_Native',args,tests,guard,r.audit.environment(),row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'CHANGED_TARGET_TESTS_CLEAN')
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check);compiled=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('bookmark_authoring_targets676-*.d'):
            if path.stat().st_mtime_ns<begin:continue
            actual=dep.dependencies(path)
            require({TEST,'crates/hwpx-package/tests/support/document_import_field_fixture.rs'}<=actual
                and actual<=set(q.snapshots),'COMPILED_INPUTS_PREBOUND')
            compiled.append(dict(dep_info=binary.pin(path.relative_to(q.root).as_posix()),
                binary=binary.pin(path.with_suffix('.exe').relative_to(q.root).as_posix()),dependency_count=len(actual)))
        require(len(compiled)==1,'ONE_CURRENT_TARGET_TEST_EXECUTABLE')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED678_SHARED_POINT_BLOCK_SOURCE_TARGET_SELECTION_NOT_WRITER_OR_NATIVE',compiled_inputs=compiled,
            new_target_conditions=12,retained_core_import_conditions_not_replayed=11,actual_source_documents=2,
            actual_block_targets_per_document=8,displays_per_block=4,hyperlink_options=2,actual_source_bound_command_candidates=128,
            point_six_commands_and_state_match_original_context=True,cross_family_name_collisions_denied=True,
            point_Content_denied=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'TARGET678_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-bookmark-authoring-targets678-product002-forensic',row)
        pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','new_target_conditions','fresh_inputs','final_fresh_hashes',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','tests')}for s in row['steps']],
            'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED678_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
