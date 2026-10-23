"""New005 publication/storage integration models only; no active entry, claim, Native or SQL."""
import ast,hashlib,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_inline_receipt567 as layout
SELF='tools/p09/verify_generation005_publication573.py'
OUTPUT='implementation/p09/evidence/p09-361-generation005-publication573.v1.json'
MODULE='tools/p09/crossref_generation005_publication.py'
TEST='tools/p09/tests/test_crossref_generation005_publication.py'
CODEC='tools/p09/crossref_inline_receipt567.py'
CODE='implementation/p09/evidence/p09-361-capture004-entry-code559.v1.json'
OLD='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run003.v1.json'
ENTRY='tools/p09/run_external_crossref_fixed_batch.py'

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--publication-models-only'],'PUB573_CLOSED_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'PUB573_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None
    row=dict(state='FAILED_GENERATION005_PUBLICATION_MODELS',own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Hancom_COM_SQL_Native_or_product_started=False,old_Native_execution_replayed=False,actual_generation005_claim_or_result_created=False,
        generation005_runtime_entry_connected=False,generation005_authorized=False,old004_lost_result_reconstructed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names={SELF,MODULE,TEST,CODEC,CODE,OLD,ENTRY,'tools/p09/compact_receipt_json.py','tools/p09/resource_sample_table.py',
            'tools/p09/test_crossref_inline_receipt567.py','tools/p09/successor_preparation_workspace_v1.py'}
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(names):q.pin(name)
        old_code=r.compact.unpack(q.json(CODE));old_pins={p['path']:p for p in old_code['source_pins']}
        c.require(q.snapshots[ENTRY]==old_pins[ENTRY],'PUB573_CONSUMED_GENERATIONS001_TO004_ENTRY_BYTE_EXACT_UNCHANGED')
        c.require(q.snapshots[OLD]['sha256']=='901374892ce5c40986b3de473a139bf4d3579b68738419bd284f95e63a8c047a','PUB573_ORIGINAL003_REMAINS_FAILED_WITH_MISSING_CLEANUP')
        before={p:bool((c.ROOT/p).exists())for p in('implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim005.v1.json',
            'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run005.v1.json','implementation/p09/evidence/private/p09-361-generation005-final-result-spool')}
        c.require(not any(before.values()),'PUB573_NO_ACTUAL005_STATE_BEFORE_MODEL_RUN')
        for name in(SELF,MODULE,TEST):ast.parse(q.text(name))
        spec=importlib.util.spec_from_file_location('p573_publication_models',c.ROOT/TEST);models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(models.Publication);c.require(suite.countTestCases()==10,'PUB573_EXACT_TEN_NEW_INTEGRATION_MODELS')
        class ObservedResult(unittest.TestResult):
            def startTest(self,test):guard.check();super().startTest(test)
            def stopTest(self,test):super().stopTest(test);guard.check()
        outcome=ObservedResult();suite.run(outcome)
        row.update(contracts=dict(run=outcome.testsRun,errors=len(outcome.errors),failures=len(outcome.failures),skipped=len(outcome.skipped)),
            failed_contract_names=[test.id()for test,_ in outcome.errors+outcome.failures])
        c.require(row['contracts']==dict(run=10,errors=0,failures=0,skipped=0),'PUB573_ALL_TEN_CURRENT_INTEGRATION_MODELS_PASS')
        c.require(all(not(c.ROOT/p).exists()for p in before),'PUB573_ACTUAL005_NAMESPACE_STILL_UNUSED')
        c.require(not list((c.ROOT/'target').glob('p09-pub573-model-*')),'PUB573_ALL_EXACT_OWNED_TEST_DIRECTORIES_REMOVED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NEW005_PUBLICATION_TEN_LOSSLESS_AND_FORENSIC_RETENTION_MODELS_NOT_NATIVE_OR_ENTRY',
            original256KiB_final_limit_preserved=True,final_packet_self_contained=True,forensic_spool_not_acceptance=True,
            no_private_raw_exception_or_original_document_values_printed=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,RecursionError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'PUB573_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        proof=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':proof}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
