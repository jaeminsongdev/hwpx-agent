"""392: independent external001 source closure and new20 modeled session contracts; no Native/worker/COM."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS
import unittest
import named_style_verification_runtime as r
import crossref_preassigned_session_scope as subject
import inspect_external_crossref_host as external

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-scope392.v1.json'
DRIVER='tools/p09/run_crossref_preassigned_scope.py'
MODULE='tools/p09/crossref_preassigned_session_scope.py'
TEST='tools/p09/tests/test_crossref_preassigned_session_scope.py'
EXTERNAL='implementation/p09/evidence/p09-361-external-crossref-host-inspection-run001.v1.json'
DOCS='implementation/p09/evidence/p09-361-external-crossref-host-sync391.v1.json'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_SCOPE_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_SESSION_SCOPE',own_cpu_selection=selection,
        actual_Hangul_COM_or_child_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);observed=r.compact.unpack(q.json(EXTERNAL));docs=r.compact.unpack(q.json(DOCS))
        c.require(q.snapshots[EXTERNAL]['sha256']=='a9598c11a234b96a602ac9d075c8af151a518e7ab2ba40d53fcab6ea93c068c7'
            and observed['state']=='OBSERVED_EXTERNAL_JOBLESS_PREREQUISITES_EMPTY_LIMITS_NOT_NATIVE_OR_SESSION'
            and observed['cleanup']is True and observed['fresh_inputs']==observed['final_fresh_hashes']==200
            and observed['external_image_final_hashes']==observed['external_runtime_final_hashes']==1,
            'EXACT_USER_EXTERNAL001_COMPLETE_FRESH_SOURCE_AND_EXECUTABLE_BOUNDARIES')
        observation=observed['observation'];checks=observation['prerequisites']['checks']
        c.require(set(checks)=={'original_resource_policy_shape','fixed_registered_server','fixed_current_executable',
            'no_preexisting_hwp_process','caller_lifecycle_native_safe'}and all(v is True for v in checks.values())
            and observation['same_kernel_identity_before_after']is True and observation['external_jobless_prerequisites_observed']is True
            and observation['future_invocation_must_revalidate_all_live_conditions']is True
            and observation['empty_resource_layout']['empty_jobs_closed']is True
            and not observation['process_created']and not observation['native_startup_qualified']
            and not observation['fixed_eight_executed'],'EXTERNAL_JOBLESS_OBSERVATION_NOT_FUTURE_NATIVE_AUTHORITY')
        c.require(q.snapshots[DOCS]['sha256']=='b7457499c24ec54b847ce42377769a9e994c7783ab7135dd44ce2d3032c8a4e5'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==38,'EXACT391_PRIOR_SOURCE_DOCUMENT_CLOSURE')
        pins={p['path']:p for p in observed['source_pins']}
        for path,pin in sorted(pins.items()):c.require(q.pin(path)==pin,'ALL_EXTERNAL001_OBSERVED_DEPENDENCIES_AND_ORIGINAL_NATIVE_CODE_UNCHANGED')
        for path in(DRIVER,MODULE,TEST):q.pin(path)
        spec=importlib.util.spec_from_file_location('p09_preassigned_scope_contracts',c.ROOT/TEST)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        original=subject.startup.PreassignedNativeStartup
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=20,errors=0,failures=0,skipped=0),'EXACT20_NEW_MODELED_PREASSIGNED_SCOPE_CONTRACTS_NO_SKIPS')
        c.require(subject.startup.PreassignedNativeStartup is original,'ORIGINAL_NATIVE_BACKEND_RESTORED_AFTER_MODELS')
        # Actual current preparation guard is rejected before any original native
        # backend constructor. This tests the guard type boundary, not a native run.
        denied=False
        try:subject.PreassignedSessionScope(guard,lambda:None)
        except ValueError as error:denied=error.args==('XREF_PREASSIGNED_SCOPE_ORIGINAL_NATIVE_GUARD_REQUIRED',)
        c.require(denied,'ACTUAL_PREPARATION_GUARD_REJECTED_BEFORE_NATIVE_BACKEND_CONSTRUCTION')
        row['actual_preparation_guard_denied_before_native_constructor']=denied
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True);row.update(state='PASS_EXTERNAL001_INDEPENDENT_CLOSURE_AND_PREASSIGNED_SCOPE20_MODELS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external001_observation_independently_bound=True,live_external_process_or_future_native_session_qualified=False,
            next_work='exact_existing_ROT_owner_attachment_worker_and_live_factory_qualification_before_conditional_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        row.update(error_type=type(error).__name__,error_code=external.safe_code(error))
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
