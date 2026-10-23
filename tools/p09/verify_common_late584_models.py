"""Tiny pure models during pending external005: no shared lock, Cargo, SQL or Native.

Only the two actual pure worker validators are compiled from their unchanged
ASTs. This is not a resource/runtime/product/Gate qualification of the SQL case.
"""
import ast,copy,hashlib,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parent))
import named_style_verification_runtime as r
import crossref_inline_receipt567 as layout
ROOT=r.c.ROOT;SELF='tools/p09/verify_common_late584_models.py'
WORKER='tools/p09/native_postgres_common_late584.py'
STORAGE='crates/product-cli/examples/sql23_storage.rs'
LEAF='crates/product-cli/examples/sql23_storage/https_target_recovery.rs'
CASE='crates/product-cli/examples/sql23_storage/https_common_late584.rs'
EXAMPLE='crates/product-cli/examples/sql26_https_common_late584.rs'
ARCHIVE='implementation/p09/source-archive/p361-common-late584/'
READY='implementation/p09/evidence/p09-361-capture005-entry-ready580.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-common-late584-models.v1.json'


def require(ok,code):
    if not ok:raise ValueError(code)


def main():
    require(sys.argv[1:]==['--pure-preparation-only'],'P584_MODELS_ONLY')
    require(not(ROOT/OUTPUT).exists(),'P584_IMMUTABLE_PURE_MODELS')
    selection=r.tools.select_own_single_cpu();started=time.monotonic()
    names={SELF,WORKER,STORAGE,LEAF,CASE,EXAMPLE,ARCHIVE+'storage583.rs',ARCHIVE+'recovery583.rs',ARCHIVE+'late545.rs',
        'crates/product-cli/examples/sql23_storage/https_late_revoke.rs',READY}
    values={};pins=[]
    for name in sorted(names):
        path=ROOT/name;require(path.is_file()and not path.is_symlink()and not path.is_junction(),'P584_REGULAR_SOURCE')
        raw=path.read_bytes();require(len(raw)<=262144,'P584_SMALL_STATIC_INPUT_BOUND');values[name]=raw
        pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    require(sum(len(v)for v in values.values())<=1048576,'P584_ONE_MIB_PREPARATION_BOUND')
    parsed=ast.parse(values[WORKER].decode());nodes=[v for v in parsed.body if isinstance(v,ast.FunctionDef)and v.name in('registry_snapshot','validate_probes')]
    require(len(nodes)==2,'P584_ONLY_TWO_PURE_VALIDATORS');env=dict(original=NS(cluster=NS(require=require)))
    exec(compile(ast.Module(body=copy.deepcopy(nodes),type_ignores=[]),WORKER,'exec'),env)
    registry,validate=env['registry_snapshot'],env['validate_probes']
    def observation():return dict(state='PASS_COMMON_LATE584_REGISTERED_UNCOMMITTED_OBSERVATION_NO_REEXECUTION',
        common_existing_without_policy_or_compilation=True,registered_effect_not_observed_not_no_effect_proof=True,
        job_in_progress_not_success=True,head_generation=1,attempt=1,fencing_token=1,claim_lease_CAS_or_execution_retried=False)
    def probes():return [dict(migrations=26),dict(actual_policy_AEAD_artifact=True,
        actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives=False,actual_atomic_policy_lock_and_binding_checks=False),
        dict(state='PASS_COMMON_LATE584_ORIGINAL_SQL_CAS_DENIAL_AND_EVIDENCE_NOT_ADMISSION',common_policy_bound_dispatch=True,
        last_app_guard_reads_completed=True,original_SQL_CAS_denied=True,result_intent_precommit_AEAD_retained=True,
        source_and_head_preserved=True,current_route_callbacks=5,route_unqualified=True,read_only_observation=observation()),observation()]
    class Models(unittest.TestCase):
        def test_exact_registry_is_copied_not_aliased(self):
            row=dict(versions=1,revocations=1,latest=1);result=registry(row);self.assertEqual(result,row);self.assertIsNot(result,row)
        def test_registry_wrong_counts_bool_missing_and_extra_are_denied(self):
            for row in(dict(versions=2,revocations=1,latest=1),dict(versions=True,revocations=1,latest=1),dict(versions=1,revocations=0,latest=1),
                dict(versions=1,revocations=1),dict(versions=1,revocations=1,latest=1,extra=0),None):
                with self.subTest(row_type=type(row).__name__),self.assertRaises(ValueError):registry(row)
        def test_exact_probes_are_not_mutated(self):
            rows=probes();before=copy.deepcopy(rows);self.assertIsNone(validate(rows));self.assertEqual(rows,before)
        def test_common_cas_and_evidence_flags_are_mandatory(self):
            for key in('common_policy_bound_dispatch','last_app_guard_reads_completed','original_SQL_CAS_denied',
                'result_intent_precommit_AEAD_retained','source_and_head_preserved','route_unqualified'):
                rows=probes();rows[2][key]=False
                with self.subTest(key=key),self.assertRaises(ValueError):validate(rows)
            for value in(4,6,True):
                rows=probes();rows[2]['current_route_callbacks']=value
                with self.subTest(callbacks=value),self.assertRaises(ValueError):validate(rows)
        def test_no_old_matrix_duplicate_recovery_or_completed_substitution(self):
            for key in('actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives','actual_atomic_policy_lock_and_binding_checks'):
                rows=probes();rows[1][key]=True
                with self.subTest(key=key),self.assertRaises(ValueError):validate(rows)
            rows=probes();rows.append(observation())
            with self.assertRaises(ValueError):validate(rows)
            rows=probes();rows[2]['state']='PASS_HTTPS_COMMON_SQL26_ORIGINAL_ATOMIC_CAS_COMPLETION_NOT_ADMISSION'
            with self.assertRaises(ValueError):validate(rows)
        def test_before_and_after_observation_require_exact_attempt_and_no_retry(self):
            for index in(2,3):
                for key,value in(('attempt',2),('head_generation',2),('fencing_token',True),('claim_lease_CAS_or_execution_retried',True),
                    ('registered_effect_not_observed_not_no_effect_proof',False),('job_in_progress_not_success',False),('extra',0)):
                    rows=probes();target=rows[2]['read_only_observation']if index==2 else rows[3];target[key]=value
                    with self.subTest(index=index,key=key),self.assertRaises(ValueError):validate(rows)
        def test_existing_example_modes_and_old545_body_are_byte_exact(self):
            text=values[STORAGE].decode()
            for addition in('const HTTPS_COMMON_LATE584_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-common-late-584";\n',
                'static HTTPS_COMMON_LATE584_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n',
                'if HTTPS_COMMON_LATE584_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_COMMON_LATE584_ROOT}else ',
                'pub fn https_common_late584_main(){HTTPS_COMMON_LATE584_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_late_revoke_main()}\n'):
                self.assertEqual(text.count(addition),1);text=text.replace(addition,'',1)
            self.assertEqual(text.encode(),values[ARCHIVE+'storage583.rs'])
            text=values[LEAF].decode()
            for addition in('#[path="https_common_late584.rs"]mod common_late584;\n',
                '    if HTTPS_COMMON_LATE584_MODE.load(Ordering::Relaxed){return common_late584::execute();}\n',
                'if HTTPS_COMMON_LATE584_MODE.load(Ordering::Relaxed)&&matches!(mode,"--restart-registered"|"--cold-recover"){return common_late584::observe();}'):
                self.assertEqual(text.count(addition),1);text=text.replace(addition,'',1)
            self.assertEqual(text.encode(),values[ARCHIVE+'recovery583.rs'])
            self.assertEqual(values['crates/product-cli/examples/sql23_storage/https_late_revoke.rs'],values[ARCHIVE+'late545.rs'])
        def test_no_modified_sql_example_is_a_prepared005_input(self):
            ready=layout.unpack(json.loads(values[READY]));paths={v['path']for v in ready['source_pins']}
            self.assertFalse(paths&{SELF,WORKER,STORAGE,LEAF,CASE,EXAMPLE})
            self.assertEqual(ready['state'],'PASS_CAPTURE005_ENTRY_RUNTIME_PREPARATION_NOT_NATIVE_OR_GATE')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Models);result=unittest.TestResult();suite.run(result)
    for pin in pins:
        raw=(ROOT/pin['path']).read_bytes();require(len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['sha256'],'P584_STATIC_INPUT_CHANGED')
    row=dict(state='PASS_COMMON_LATE584_PURE_PREPARATION_MODELS_NOT_COMPILED_SQL_NATIVE_OR_GATE'if result.wasSuccessful()else'FAILED_COMMON_LATE584_PURE_MODELS',
        models=dict(run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)),
        failed_model_names=[case.id()for case,_ in result.failures+result.errors],source_pins=pins,fresh_inputs=len(pins),final_fresh_hashes=len(pins),
        own_cpu_selection=selection,elapsed_seconds=round(time.monotonic()-started,3),shared_verification_lock_acquired=False,
        actual_Cargo_SQL_Hancom_COM_or_Native_started=False,SQL_case_state='NOT_RUN',new_SQL_database_created=False,
        old545_failure_or_571_result_rewritten=False,old_modes_whole_body_inverse_checked=True,prepared005_inputs_modified=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,cleanup=True)
    packet=layout.pack(row);pin=r.shared.publisher.publish(ROOT,OUTPUT,packet,NS(require=require,exact=r.a.exact))
    print(json.dumps({**{k:row[k]for k in('state','models','failed_model_names','fresh_inputs','final_fresh_hashes','elapsed_seconds','cleanup')},'receipt':pin}),flush=True)
    return 0 if result.wasSuccessful()else 2


if __name__=='__main__':raise SystemExit(main())
