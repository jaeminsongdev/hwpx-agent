"""Register the existing P04 test blob as a newly in-scope input; preserve251 preflight failure."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_transaction_bytes_probe as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-transaction-bytes-probe-recovery252.v1.json'
DRIVER='tools/p09/run_transaction_bytes_probe_recovery.py'
TEST_BASELINE=dict(path=base.PARENT,bytes=26355,sha256='ad0a3d7955b3192fcaaf71216e5638ddc70c164a8f729421fdf8642bd4d3447e')


def inventory(check):return base.inventory(check)|{DRIVER}


def inverse(q,old):base.inverse(q,{**old,base.PARENT:TEST_BASELINE})


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'BYTE_PROBE_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TRANSACTION_BYTES_PROBE_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,bytes_source_API_accepted=False,expected_security_negative_case=True,real_filesystem_only_owned_test_scratch=True,
        original_test_baseline=TEST_BASELINE,baseline_origin='read-only Git HEAD blob checked against the complete live prefix after removing only the new test child')
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=base.prior.compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='9af1a2d0e63848a56746a2cc022e93bf8e5fb2cb715e1a0309b96d3e5711edf8'
            and failed['cleanup']and failed['error_type']=='KeyError'and not failed['steps'],'EXACT251_INPUT_SCOPE_FAILURE_NO_CARGO_OR_TESTS')
        packet=q.json(base.prior.OUTPUT);origin=base.prior.compact.unpack(packet);docs=q.json(base.DOC_BASE)
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='0e118e7c6d12be8bb8792793e9eb4c4ed08974542f96a940bbd1b1911245e324'
            and origin['cleanup'],'EXACT249_PRIOR_SOURCE')
        c.require(q.snapshots[base.DOC_BASE]['sha256']=='9383b9a082ba6eb65e7400e56f9d1228e8ea2611f890348e6c2326c4574ee5cb'and docs['cleanup'],'EXACT250_PRIOR_DOCS')
        old={p['path']:p for p in origin['source_pins']};documented={p['path']:p for p in docs['source_pins']};attempt={p['path']:p for p in failed['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in base.NEW|base.CHANGED|{DRIVER}:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_SERVICES_ROUTES_AND_NATIVE_GUARDS_UNCHANGED')
            elif name!=DRIVER:c.require(q.snapshots[name]==attempt[name],'ALL_BYTE_API_CODE_AND_NEGATIVE_TESTS_UNCHANGED_SINCE251')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);base.expected(q)
        print(json.dumps(dict(state='BYTE_PROBE_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),one_negative_case=True,old9_and_official249_not_run=True)),flush=True)
        snapshot=base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        try:
            harness.run_one('one_staged_output_tamper_case_before_repair',[harness.CARGO,'test','--offline','--locked','-j','1','-p','operation-engine',
                '--test','workspace_transaction','--message-format=short','--',base.CASE,'--exact','--test-threads=1'],{base.CASE},guard,audit.environment(),row,observe_capture=snapshot)
        except ValueError:
            c.require(len(row['steps'])==1 and row['steps'][0]['exit_code']==101 and row['steps'][0]['tests']==[(base.CASE,'FAILED')],
                'ONLY_EXPECTED_TAMPER_CASE_FAILURE_NOT_COMPILATION_OR_RESOURCE_ERROR')
        else:raise ValueError('EXPECTED_TAMPER_FAILURE_NOT_REPRODUCED')
        q.finish();guard.check(force=True)
        row.update(state='REPRODUCED_STAGED_OUTPUT_TAMPER_TEST_FAILURE_NOT_ACCEPTANCE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            security_negative_test_failed=True,total_accepted_cases=0,next_work='streaming_staged_and_published_result_identity_checks_then_12_new_and9_affected_file_regressions')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'BYTE_PROBE_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_BYTE_PROBE_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,base.prior.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},'tests':s.get('tests',[])}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('REPRODUCED_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
