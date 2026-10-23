"""386: new external-root inspection contracts and actual current-caller denial; no child/Native."""
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS
import unittest

import named_style_verification_runtime as r
import inspect_current_crossref_prerequisites as prior
import crossref_external_host_inspection as subject
import inspect_external_crossref_host as external

OUTPUT=external.CODE
DRIVER='tools/p09/run_external_crossref_host_code.py'


def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists(),'EXTERNAL_HOST_CODE_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=runtime=None;started=time.monotonic()
    row=dict(state='FAILED_EXTERNAL_HOST_INSPECTION_CODE',own_cpu_selection=selection,
        user_external_terminal_preparation_authorized=True,actual_Cargo_Hangul_COM_or_child_started=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,
        prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='2cc887cfbc1991084ca944c28815dfeb9bfec09fcd8b7be49829d0ea4e4107ca'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==14,'EXACT380_ORIGINAL_NATIVE_PREREQUISITES')
        pins={p['path']:p for p in previous['source_pins']}
        for path in sorted(prior.NATIVE):c.require(q.pin(path)==pins[path],'ORIGINAL_NATIVE_GUARDS_FACTORY_AND_FIXED_EIGHT_UNCHANGED')
        for path in(DRIVER,external.SELF,external.MODULE,external.TEST):q.pin(path)
        spec=importlib.util.spec_from_file_location('p09_external_host_contracts',c.ROOT/external.TEST)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        originals=(subject.current_identity,subject.empty_resource_layout,subject.prerequisites.inspect,
            subject.prerequisites.startup.parent_without_prompt_kill,subject.native.NativeOwnerJob,subject.host.OwnedHostProcess)
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        suite=unittest.defaultTestLoader.loadTestsFromModule(module);result=GuardedResult();suite.run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=22,errors=0,failures=0,skipped=0),'EXACT22_NEW_EXTERNAL_HOST_CONTRACTS_NO_SKIPS')
        c.require(originals==(subject.current_identity,subject.empty_resource_layout,subject.prerequisites.inspect,
            subject.prerequisites.startup.parent_without_prompt_kill,subject.native.NativeOwnerJob,subject.host.OwnedHostProcess),'ORIGINAL_FUNCTIONS_RESTORED_BEFORE_ACTUAL_KERNEL_OBSERVATION')
        executable=Path(subject.native.EXECUTABLE);image=a.AcceptanceReader(executable.parent,guard.check)
        runtime=a.AcceptanceReader(subject.fixed.PYTHON.parent,guard.check)
        row['actual_observation']=subject.inspect(guard.windows,guard.check,
            lambda:image.pin(executable.name),lambda:runtime.pin(subject.fixed.PYTHON.name))
        observed=row['actual_observation'];original=observed['prerequisites']
        c.require(not observed['external_jobless_prerequisites_observed']and observed['empty_resource_layout']is None
            and original['failed_prerequisites']==['caller_lifecycle_native_safe']
            and not observed['process_created']and not observed['COM_activated'],'ACTUAL_CURRENT_CALLER_DENIAL_BEFORE_ANY_EMPTY_JOB_OR_NATIVE_PROCESS')
        imported=set()
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':
                    relative=path.relative_to(c.ROOT).as_posix();q.pin(relative);imported.add(relative)
        row['inspection_dependency_paths']=sorted(imported|prior.NATIVE|{external.SELF,external.MODULE,external.TEST})
        image.finish();runtime.finish();q.finish();guard.check(force=True)
        row.update(state=external.CODE_STATE,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_image_final_hashes=image.final_fresh_hashes,external_runtime_final_hashes=runtime.final_fresh_hashes,
            next_work='user_external_inspect_only_run001_then_live_preassigned_native_factory_and_owner_qualification_before_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        row.update(error_type=type(error).__name__,error_code=external.safe_code(error))
        if q is not None:
            try:
                if image is not None:image.finish();row['external_image_final_hashes']=image.final_fresh_hashes
                if runtime is not None:runtime.finish();row['external_runtime_final_hashes']=runtime.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            external_image_pins=[]if image is None else list(image.snapshots.values()),
            external_runtime_pins=[]if runtime is None else list(runtime.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes',
            'external_image_final_hashes','external_runtime_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state']==external.CODE_STATE and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
