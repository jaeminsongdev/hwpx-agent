"""389: strict packed-only proof contract1; keep actual388 failure and other23 passes, no Native."""
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS
import unittest
import named_style_verification_runtime as r
import inspect_external_crossref_host as external

OUTPUT=external.CODE
DRIVER='tools/p09/run_external_crossref_host_packed.py'
BASE='implementation/p09/evidence/p09-361-external-crossref-host-entry388.v1.json'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'EXTERNAL_PACKED_CODE_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_EXTERNAL_HOST_PACKED_CODE',own_cpu_selection=selection,
        actual_Cargo_Hangul_COM_or_child_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='dd5b312dcdcdae993d79fc4c00e3c0d3fc9c357fb997795c3389517bda626515'
            and failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==198
            and failed['contracts']==dict(run=2,errors=1,failures=0,skipped=0)
            and len(failed['failed_contract_names'])==1 and '.test_24_'in failed['failed_contract_names'][0],
            'EXACT388_FAILED_PLAIN_FIXTURE_AND_PASSED_AST_CONTRACT_RETAINED')
        pins={p['path']:p for p in failed['source_pins']}
        for path,pin in sorted(pins.items()):
            q.pin(path)
            if path not in(external.SELF,external.TEST):c.require(q.snapshots[path]==pin,'ALL_OTHER_INSPECTION_NATIVE_FACTORY_GUARDS_AND_TEST_SOURCE_UNCHANGED')
        text=q.text(external.SELF).replace(OUTPUT,BASE).replace("proof['contracts']==dict(run=1,", "proof['contracts']==dict(run=2,").replace("proof['retained_contracts']==23,","proof['retained_contracts']==22,")
        r.audit.inverse(text,pins[external.SELF],'SAME_STRICT_PACKED_PRODUCTION_BODY_ONLY_SUCCESSOR_PROOF_COUNTS')
        text=q.text(external.TEST).replace('test_24_entry_requires_packed_proof_and_rejects_incomplete_or_failed_code',
            'test_24_entry_reads_packed_or_plain_proof_but_rejects_incomplete_or_failed_code').replace(
            'contracts=dict(run=1,errors=0,failures=0,skipped=0),current_distinct_contracts=24,retained_contracts=23)',
            'contracts=dict(run=2,errors=0,failures=0,skipped=0),current_distinct_contracts=24,retained_contracts=22)').replace(
            "        self.assertEqual(entry.load_code_proof(NS(json=lambda path:entry.r.compact.pack(proof))),proof)\n        with self.assertRaisesRegex(ValueError,'COMPACT_RECEIPT_ENVELOPE'):\n            entry.load_code_proof(NS(json=lambda path:proof))",
            '        for value in(proof,entry.r.compact.pack(proof)):\n            self.assertEqual(entry.load_code_proof(NS(json=lambda path:value)),proof)').replace(
            "('current_distinct_contracts',23),('retained_contracts',22)):","('current_distinct_contracts',23),('retained_contracts',23)):")
        r.audit.inverse(text,pins[external.TEST],'ONLY_FAILED24_EXPECTATION_FIXED_PLAIN_PROOF_STAYS_REJECTED_NO_WEAKENING')
        q.pin(DRIVER);spec=importlib.util.spec_from_file_location('p09_external_host_packed_contract',c.ROOT/external.TEST)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=unittest.TestResult();module.ExternalHostContracts('test_24_entry_requires_packed_proof_and_rejects_incomplete_or_failed_code').run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=1,errors=0,failures=0,skipped=0),'ONLY_FAILED_PACKED_PROOF_CONTRACT1_PASS_RETAIN23')
        imported=set(pins)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':
                    relative=path.relative_to(c.ROOT).as_posix();q.pin(relative);imported.add(relative)
        row['inspection_dependency_paths']=sorted(imported)
        q.finish();guard.check(force=True);row.update(state=external.CODE_STATE,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_distinct_contracts=24,retained_contracts=23,next_work='actual_entry_inspection_run007_without_native_then_external_user_run001')
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
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state']==external.CODE_STATE and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
