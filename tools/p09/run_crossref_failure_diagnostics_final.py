"""429: retain 426 Python16/PS10; affected2 + new2, no double wait on Ctrl+C."""
import importlib.util,json,re,subprocess,time,unittest
from types import SimpleNamespace as NS
import run_crossref_failure_diagnostics as prior
r,layout,entry=prior.r,prior.layout,prior.entry
OUTPUT='implementation/p09/evidence/p09-361-crossref-failure-diagnostics-final429.v1.json'
DRIVER='tools/p09/run_crossref_failure_diagnostics_final.py'
TRANSPORT='tools/p09/crossref_native_worker_io.py'


def original_transport(text):
    changes=[("    code=result.get('error_code');phase=result.get('phase');kind=result.get('error_kind');hresult=result.get('error_hresult')",
        "    code=result.get('error_code');phase=result.get('phase')"),
        ("        worker_error_kind=kind if type(kind)is str and kind in('COMException','InvalidOperationException','OtherException')else None,\n",''),
        ("        worker_error_hresult=hresult if type(hresult)is str and re.fullmatch(r'0x[0-9A-F]{8}',hresult)else None,\n",''),
        (";result=None;interruption=None",";result=None"),
        ("        if isinstance(error,KeyboardInterrupt):interruption=error\n",''),
        ("        if interruption is not None:\n            # Ctrl+C during the retained-owner wait must not silently enter\n            # that same unbounded wait again in finally. No kill/close/replay.\n            record['cleanup_failure']=safe_failure(interruption)\n            raise interruption\n",'')]
    for added,original in changes:
        r.c.require(text.count(added)==1,'ONE_CLOSED_INTERRUPT_OR_SAFE_NUMERIC_DIAGNOSTIC_CHANGE');text=text.replace(added,original)
    return text


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'DIAGNOSTICS429_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_CROSSREF_FAILURE_DIAGNOSTICS_FINAL429',own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,qualification_or_fixed_worker_started=False,fixed_eight_executed=False,
        native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        original_claim_consumed=True,remaining_owned_native_force_terminated=False,current_entry_source_requires_requalification=True,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='e5bf2e49bdf41a8a79d1dd3d8931dab70cedc76f39cb1a86659c443d7c41aaef'
            and base['cleanup']is True and base['contracts']==dict(run=16,errors=0,failures=0,skipped=0)
            and base['fresh_inputs']==base['final_fresh_hashes']==227 and len(base['steps'][0]['tests'])==10,'EXACT426_PY16_PS10_RETAINED')
        old={p['path']:p for p in base['source_pins']}
        for path in sorted(set(old)|{DRIVER}):
            pin=q.pin(path)
            if path in old and path not in(TRANSPORT,prior.PYTEST):c.require(pin==old[path],'ALL_OTHER_EXECUTION_DIAGNOSTIC_PS_NATIVE_GUARD_INPUTS_UNCHANGED')
        r.audit.inverse(original_transport(q.text(TRANSPORT)),old[TRANSPORT],'ONLY_NO_DOUBLE_INTERRUPT_WAIT_AND_SAFE_NUMERIC_NOTICE_EXTENSION')
        text=q.text(prior.PYTEST);start=text.index('    def test_17_');end=text.index('if __name__',start)
        r.audit.inverse(text[:start]+'\n\n'+text[end:],old[prior.PYTEST],'ALL16_PREVIOUS_CONTRACTS_AND_MODEL_HELPERS_UNCHANGED_ONLY_TWO_NEW_TESTS')
        spec=importlib.util.spec_from_file_location('p09_failure_diagnostic_final_models',c.ROOT/prior.PYTEST)
        models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        selected=[n for n in unittest.defaultTestLoader.getTestCaseNames(models.FailureContracts)if int(n.split('_')[1])in(9,10,17,18)]
        c.require(len(selected)==4,'AFFECTED2_NEW2_ONLY_NO_UNAFFECTED_REPLAY')
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();unittest.TestSuite(models.FailureContracts(n)for n in selected).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=4,errors=0,failures=0,skipped=0),'EXACT_AFFECTED2_AND_NEW2_CONTRACTS_PASS')
        final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_CROSSREF_DIAGNOSTICS_PY18_PS10_RETAINED_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_distinct_contracts=28,retained_unaffected_contracts=24,last_executed_contracts=4,new_contracts=2)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'DIAGNOSTICS429_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            final_attempted=True
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
