"""Eight-case code models and real worker READY denial; never releases Native."""
import json,re,subprocess,sys,time
from pathlib import Path
import run_prepared_bookmark_native684 as entry
import run_prepared_bookmark_native631 as prior
from verify_prepared_bookmark631 import command,ReadyDenial
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_prepared_bookmark687.py'
TEST='tools/p09/tests/test_prepared_bookmark684.py'
PS_TEST='implementation/p09/tools/test-prepared-bookmark684-ports.ps1'
OLD_CODE='implementation/p09/evidence/p09-361-prepared-bookmark631-code003.v1.json'

def require(ok,code):
    if not ok:raise ValueError('XREF_PREPARED687_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_NEW_PROOF')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=shell=None;begin=time.monotonic()
    row=dict(state='FAILED687_NEW_BLOCK_EIGHT_CODE',steps=[],actual_native_started=False,all_new_tests_passed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)


        second_path='implementation/p09/evidence/p09-361-prepared-bookmark686-code001.v1.json'
        second=prior.codec.unpack(q.json(second_path))
        require(q.snapshots[second_path]['sha256']=='174338a7295f5d0fe578b94114ea4a4f51d11cd536396c217b33e6359624b037'
            and second['cleanup']is True and second['steps'][0]['result']['run']==2
            and second['steps'][0]['result']['failures']==1,'RETAINED19_CODE_MODELS_ONE_SOURCE_PIN_FAILURE')
        archive686='implementation/p09/source-archive/p361-prepared-bookmark686-failed/'
        for pin in second['source_pins']:
            name=archive686+pin['path']if pin['path']in(entry.SELF,m.PORTS)else pin['path']
            actual=q.pin(name);require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'SECOND_FAILED_INPUTS_PRESERVED')
        failed_path='implementation/p09/evidence/p09-361-prepared-bookmark685-code001.v1.json'
        failed=prior.codec.unpack(q.json(failed_path))
        require(q.snapshots[failed_path]['sha256']=='34e7adbc1e768a4cc8c5a2771390520d4baa22f8b00eb5c9cd7a15f1d1f1365d'
            and failed['cleanup']is True and len(failed['steps'])==1
            and failed['steps'][0]['result']['run']==20 and failed['steps'][0]['result']['errors']==0
            and failed['steps'][0]['result']['failures']==2,'EXACT20_INITIAL18_PASSED')
        changed={entry.SELF,m.TARGET,m.PORTS,m.CHANNEL}
        archive='implementation/p09/source-archive/p361-prepared-bookmark685-failed/'
        for pin in failed['source_pins']:
            path=archive+pin['path']if pin['path']in changed else pin['path']
            observed=q.pin(path);require((observed['bytes'],observed['sha256'])==(pin['bytes'],pin['sha256']),'PRESERVED_FAILED_INPUTS_AND_RETAINED18')
        for path in(m.TARGET,m.PORTS,m.CHANNEL):
            expected=q.text(archive+path)+'\n'
            if path==m.PORTS:expected=expected.replace('64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184',m.prepared.SOURCE_PIN['sha256'])
            require(q.text(path)==expected,'ONE_TRAILING_LF_AND_CURRENT_DERIVED_SOURCE_PIN_ONLY')
        require(q.text(entry.SELF)==q.text(archive+entry.SELF).replace('685','687'),'ONLY_NEW_CODE_PROOF_NAMESPACE')
        q.pin('tools/p09/tests/test_prepared_bookmark687_recovery.py')
        row.update(retained19_not_replayed=True,previous20_proof=q.snapshots[failed_path])
        old=prior.codec.unpack(q.json(OLD_CODE));require(old['state']==prior.STATE and old['cleanup']is True,'RETAINED631_CODE_PROOF')
        pins={pin['path']:pin for pin in old['source_pins']}
        # Bind exactly the previous Native controller/ports/guard implementations,
        # not every Rust fixture ever listed by their historical receipts.
        retained={'tools/p09/prepared_bookmark_native631.py','tools/p09/prepared_bookmark631_sections.py',
            'tools/p09/prepared_bookmark631_drain.py','tools/p09/prepared_bookmark631_evidence.py',
            'tools/p09/crossref_native_worker_io603.py','implementation/p09/tools/run-prepared-bookmark631-worker.ps1',
            'implementation/p09/tools/prepared-bookmark631-ports.ps1','implementation/p09/tools/prepared-bookmark631-channel.ps1'}
        for path in retained:require(q.pin(path)==pins[path],'CONSUMED631_LIFECYCLE_AND_GUARDS_UNCHANGED')
        row['prepared_files']=m.prepared.validate_prepared(q,prior.codec.unpack)
        proof=prior.codec.unpack(q.json(m.prepared.PROOF))
        require(q.snapshots[m.prepared.PROOF]['sha256']=='658c83946a18c0bd3518ff75716eb4c35abaf59b26fcdd211c00bcf3662b79d2','EXACT683_SUCCESS')
        for pin in proof['source_pins']:require(q.pin(pin['path'])==pin,'GENERATED_CURRENT_PRODUCT_SOURCE_UNCHANGED')
        paths=m.SOURCES|m.prepared.loaded_dependencies(r.c.ROOT)|{entry.SELF,'tools/p09/prepared_bookmark684_receipt.py',m.prepared.PREPARED}
        paths|={m.prepared.SOURCE_PIN['path']}|{case['output']['path']for case in row['prepared_files']['cases']}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths|{SELF,TEST,PS_TEST}):q.pin(path)
        # Runtime per-case closure is restricted to current code/images and9 files.
        require(not any(path.startswith('crates/')or'/source-archive/'in path for path in paths),'NO_REPEATED_RUST_OR_HISTORY_AUDIT_PER_CASE')
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE')
        image=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(image.parent,guard.check)
        row['shell_pin']=shell.pin(image.name);require(row['shell_pin']==old['shell_pin'],'SAME_X86_WORKER_SHELL')
        for args,count,label in(([sys.executable,'-B',str(r.c.ROOT/'tools/p09/tests/test_prepared_bookmark687_recovery.py')],1,'only_corrected_source_pin_projection_retained19'),
            ([str(image),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/PS_TEST),'-ModelsOnly'],14,'new_profile_ports_BMP_and_syntax14')):
            result=command(guard,args,r.audit.environment(),row,label)
            require({k:result[k]for k in('run','errors','failures','skipped')}==dict(run=count,errors=0,failures=0,skipped=0)
                and result['actual_native_started']is False,'ALL_NEW_CODE_MODELS')
        worker=m.Worker(guard);handler=ReadyDenial(worker,lambda:shell.fresh_pin(image.name));attempt={};row['ready_denial']=attempt
        result=m.io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',r.audit.environment(),lambda value:None,attempt)
        require(attempt['exit_code']==2 and attempt['cleanup']is True and attempt['requests']==1 and handler.calls==1
            and result['completed_callback_cases']==0 and result['planned_cases']==8 and result['retained_live_or_uncertain_owners']==0,'REAL_READY_DENIED_ZERO_CASES')
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_PROCESS_CHANGE');m.absent()
        shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,current_code_models=34,actual_READY_frames=1,actual_case_frames=0,
            Native_process_set_unchanged=True,previous_product26_and_Native_not_replayed=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**m.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps'])and('ready_denial'not in row or row['ready_denial'].get('cleanup')is True),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        normalized,_=prior.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-prepared-bookmark687-code001-forensic',row)
        pin=prior.publish(entry.CODE,normalized)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','result')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
