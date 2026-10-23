"""Bounded non-Native transport regression proof, never consumed-run replay or new execution permit."""
import ast,hashlib,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_native_worker_io as old
import crossref_native_worker_io603 as candidate
import crossref_inline_receipt567 as layout
SELF='tools/p09/verify_crossref_transport603.py'
MODULE='tools/p09/crossref_native_worker_io603.py'
TEST='tools/p09/tests/test_crossref_native_worker_io603.py'
OLD='tools/p09/crossref_native_worker_io.py'
RUN009='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run009.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-native-worker-transport603-models.v1.json'

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--models-only'],'P603_MODELS_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P603_IMMUTABLE_OUTPUT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_TRANSPORT603_MODELS',own_cpu_selection=selection,actual_Native_COM_Hancom_started=False,
        consumed009_replayed=False,external010_prepared_or_authorized=False,candidate_wired_into_production=False,
        original600_deadline_relaxed_or_renewed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=layout.unpack(q.json(RUN009))
        c.require(q.snapshots[RUN009]['sha256']=='2eb9a9cb848d888ad39cfe433601e5494b3f4072eab856ef57d67f65fd7d6cef'
            and prior['cleanup']is False and prior['fixed_eight_executed']is False
            and prior['error_code']=='EXTERNAL_ENTRY_INTERRUPTED_WITH_UNCONFIRMED_CLEANUP','P603_ORIGINAL009_FAILURE_PRESERVED')
        pins={p['path']:p for p in prior['source_pins']}
        for name in(OLD,'tools/p09/crossref_external009_runtime.py','tools/p09/run_external_crossref_fixed_batch009.py',
                'tools/p09/accept_case112_current_epoch.py'):
            c.require(q.pin(name)==pins[name],'P603_CONSUMED009_AND_GUARD_SOURCES_BYTE_EXACT')
        paths={SELF,MODULE,TEST}
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':paths.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(paths):q.pin(name)
        def nested(text,name):
            return ast.get_source_segment(text,next(n for n in ast.walk(ast.parse(text))if isinstance(n,ast.FunctionDef)and n.name==name))
        for name in('read','emit'):
            c.require(nested(q.text(MODULE),name)==nested(q.text(OLD),name),'P603_ORIGINAL_BOUNDED_STREAM_READER_UNCHANGED')
        c.require(candidate.wait_native_exit is old.wait_native_exit and candidate.result_notice is old.result_notice,
            'P603_ORIGINAL_UNCERTAIN_OWNER_POLICY_NOT_RELAXED')
        spec=importlib.util.spec_from_file_location('transport603_models',c.ROOT/TEST)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);result=unittest.TestResult()
        with patch.object(candidate.closed.startup,'PreassignedNativeStartup',side_effect=AssertionError('P603_NATIVE_TRAP'))as native:
            unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
            row['native_constructor_trap_calls']=native.call_count
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['native_constructor_trap_calls']==0 and row['contracts']==dict(run=18,errors=0,failures=0,skipped=0),
            'P603_ALL18_NON_NATIVE_TRANSPORT_MODELS')
        q.finish();guard.check(force=True)
        row.update(state='PASS_TRANSPORT603_MODELS_NOT_NATIVE_OR_PRODUCTION_OR_GATE',
            native_timeout_guard_source_unchanged=True,unknown_messages_not_logged=True,
            failed_request_eof_precedes_native_wait=True,first_failure_and_snapshot_survive_cleanup_interrupt=True,
            returned_uncertain_owner_still_requires_exact_exit=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,AssertionError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'P603_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs',
            'final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2

if __name__=='__main__':raise SystemExit(main())
