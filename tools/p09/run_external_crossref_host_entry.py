"""388: fix packed proof boundary, new1/affected AST1, retain22; preserve failed external008."""
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS
import unittest

import named_style_verification_runtime as r
import crossref_external_host_inspection as subject
import inspect_external_crossref_host as external

OUTPUT=external.CODE
DRIVER='tools/p09/run_external_crossref_host_entry.py'
BASE='implementation/p09/evidence/p09-361-external-crossref-host-recovery387.v1.json'
FAILED='implementation/p09/evidence/p09-361-external-crossref-host-inspection-run008.v1.json'


def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists(),'EXTERNAL_HOST_ENTRY_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_EXTERNAL_HOST_INSPECTION_ENTRY',own_cpu_selection=selection,
        user_external_terminal_preparation_authorized=True,actual_Cargo_Hangul_COM_or_child_started=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,
        prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=r.compact.unpack(q.json(BASE));failed=r.compact.unpack(q.json(FAILED))
        c.require(q.snapshots[BASE]['sha256']=='98865ee2fdd87343f12e6fefd9357854aff44c92538c68061c3db0464e0c5adf'
            and previous['state']==external.CODE_STATE and previous['cleanup']
            and previous['fresh_inputs']==previous['final_fresh_hashes']==195
            and previous['current_distinct_contracts']==23 and previous['retained_contracts']==10,'EXACT387_CURRENT23_CONTRACTS_AND_KERNEL_DENIAL')
        c.require(q.snapshots[FAILED]['sha256']=='e060d11a7712006b2bf5f3b760d6b7a61ac58819151cb1ad21ad82b09a9b1974'
            and failed['state']=='FAILED_EXTERNAL_HOST_INSPECTION_NOT_NATIVE'and failed['error_type']=='KeyError'
            and failed['cleanup']and not failed['actual_Hangul_or_COM_or_child_started'],'FAILED008_PACKED_PROOF_KEYERROR_RETAINED_BEFORE_ANY_NATIVE')
        pins={p['path']:p for p in previous['source_pins']}
        for path,pin in sorted(pins.items()):
            q.pin(path)
            if path not in(external.SELF,external.TEST):c.require(q.snapshots[path]==pin,'ALL_OTHER_SOURCE_NATIVE_FACTORY_GUARDS_AND_ORIGINAL_FAILURES_UNCHANGED')
        text=q.text(external.SELF).replace(OUTPUT,BASE)
        start=text.index('def load_code_proof(reader):');end=text.index('def main(argv=None):',start)
        text=text[:start]+text[end:]
        text=text.replace('guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=load_code_proof(q)',
            "guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=q.json(CODE)\n        c.require(proof['state']==CODE_STATE and proof['cleanup']is True\n            and proof['fresh_inputs']==proof['final_fresh_hashes']>0\n            and proof['contracts']==dict(run=13,errors=0,failures=0,skipped=0)\n            and proof['current_distinct_contracts']==23 and proof['retained_contracts']==10,'EXTERNAL_HOST_VERIFIED_INSPECTION_CODE_REQUIRED')")
        r.audit.inverse(text,pins[external.SELF],'ONLY_PACKED_PROOF_READER_CURRENT_CONTRACT_IDENTITY_CHANGED')
        test=q.text(external.TEST);start=test.index('    def test_24_entry_reads_packed_or_plain_proof');end=test.index('EMPTY_LAYOUT=subject.empty_resource_layout',start)
        r.audit.inverse(test[:start]+test[end:],pins[external.TEST],'ALL_PREVIOUS23_TEST_BODIES_EXACT_NEW_PACKED_PROOF_CONTRACT_ONLY')
        q.pin(DRIVER)
        spec=importlib.util.spec_from_file_location('p09_external_host_entry_contracts',c.ROOT/external.TEST)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        suite=unittest.TestSuite(module.ExternalHostContracts(name)for name in unittest.defaultTestLoader.getTestCaseNames(module.ExternalHostContracts)
            if name.startswith(('test_22_','test_24_')))
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();suite.run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=2,errors=0,failures=0,skipped=0),'NEW_PACKED_PROOF1_AFFECTED_ENTRY_AST1_PRESERVE22_NO_REPLAY')
        imported=set(previous['inspection_dependency_paths'])
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':
                    relative=path.relative_to(c.ROOT).as_posix();q.pin(relative);imported.add(relative)
        row['inspection_dependency_paths']=sorted(imported)
        q.finish();guard.check(force=True)
        row.update(state=external.CODE_STATE,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_distinct_contracts=24,retained_contracts=22,
            next_work='actual_entry_inspection_run007_without_native_then_external_user_run001')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        row.update(error_type=type(error).__name__,error_code=external.safe_code(error))
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes',
            'cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state']==external.CODE_STATE and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
