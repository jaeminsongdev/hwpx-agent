"""Pure585 gate/publication models, no shared lock or actual process query/SQL/Native."""
import ast,contextlib,copy,hashlib,io,json,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import common_late585_publication as pub
import verify_common_late585 as driver
import crossref_inline_receipt567 as layout
SELF='tools/p09/verify_common_late585_models.py'
OUTPUT='implementation/p09/evidence/p09-361-common-late585-models.v1.json'


def main():
    c=r.c;c.require(sys.argv[1:]==['--pure-admission-and-publication-only'],'P585_PURE_MODELS_SCOPE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P585_IMMUTABLE_PURE_MODELS')
    selection=r.tools.select_own_single_cpu();started=time.monotonic()
    names={SELF,driver.SELF,driver.HOST,driver.WORKER,driver.CASE,driver.EXAMPLE,
        'tools/p09/common_late585_publication.py','tools/p09/crossref_generation005_publication.py',
        'tools/p09/crossref_inline_receipt567.py','tools/p09/compact_receipt_json.py','tools/p09/successor_preparation_workspace_v1.py',driver.MODELS}
    pins=[];raws={}
    for name in sorted(names):
        path=c.ROOT/name;c.require(path.is_file()and not path.is_symlink()and not path.is_junction(),'P585_MODEL_REGULAR_INPUT')
        raw=path.read_bytes();c.require(len(raw)<=262144,'P585_MODEL_SMALL_SOURCE');raws[name]=raw
        pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    c.require(sum(map(len,raws.values()))<=1048576,'P585_MODEL_INPUT_TOTAL_BOUND')
    for name in names:
        if name.endswith('.py'):ast.parse(raws[name].decode())
    def packet():return dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',generation=5,cleanup=False,native_claim_created=True,
        fixed_eight_executed=False,native_startup_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    def row():return dict(state='FAILED_COMMON_LATE_SQL585',accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Hancom_COM_Native_or_249_started=False,model=list(range(16000)))
    class Models(unittest.TestCase):
        def setUp(self):
            self.temp=tempfile.TemporaryDirectory(prefix='p09-common585-pure-',dir=c.ROOT/'target');self.root=Path(self.temp.name).resolve()
            c.require(self.root.is_relative_to((c.ROOT/'target').resolve())and not self.root.is_symlink()and not self.root.is_junction(),'P585_OWNED_MODEL_TEMP_SCOPE')
            (self.root/'implementation/p09/evidence/private').mkdir(parents=True)
        def tearDown(self):
            c.require(self.root.is_relative_to((c.ROOT/'target').resolve())and not self.root.is_symlink()and not self.root.is_junction(),'P585_MODEL_CLEANUP_EXACT_SCOPE')
            self.temp.cleanup()
        def test_absent005_defers_before_any_guard_policy_selection_or_claim(self):
            out=io.StringIO()
            with (patch.object(driver,'external_terminal',return_value=None),
                patch.object(driver.r.tools,'select_own_single_cpu',side_effect=AssertionError('GUARD_SELECTION_FORBIDDEN')),
                patch.object(sys,'argv',['driver','--after-external005-terminal-only']),contextlib.redirect_stdout(out)):
                self.assertEqual(driver.main(),3)
            result=json.loads(out.getvalue());self.assertEqual(result['state'],'DEFERRED_EXTERNAL005_NOT_TERMINAL_NO_LOCK_BUILD_OR_DATABASE')
            self.assertFalse(result['shared_lock_acquired']);self.assertFalse(result['actual_Cargo_SQL_or_Native_started']);self.assertFalse(result['SQL_case_consumed'])
        def test_terminal_requires_exact_generation_types_and_non_gate_state(self):
            self.assertTrue(driver.terminal_value(packet()))
            for key,value in(('generation',True),('generation',4),('cleanup',None),('native_claim_created',1),('fixed_eight_executed',0),
                ('accepted_count_delta',True),('accepted_count_delta',1),('native_startup_qualified',True),('P09_gate','CLOSED'),('P10_started',True)):
                value_row=packet();value_row[key]=value
                with self.subTest(key=key,value_type=type(value).__name__):self.assertFalse(driver.terminal_value(value_row))
        def test_partial005_file_is_not_terminal_and_original_cleanup_false_is_not_upgraded(self):
            path=self.root/driver.EXTERNAL;path.write_bytes(b'{')
            self.assertIsNone(driver.external_terminal(self.root))
            raw=json.dumps(layout.pack(packet()),separators=(',',':')).encode();path.write_bytes(raw)
            value=driver.external_terminal(self.root);self.assertEqual(value['sha256'],hashlib.sha256(raw).hexdigest());self.assertFalse(value['original_cleanup'])
        def test_spool_and_self_contained_formal_packet_roundtrip(self):
            value=row();pub.publish_final(self.root,value);self.assertEqual(pub.retained_row(self.root),value)
            self.assertEqual(layout.unpack(json.loads((self.root/pub.OUTPUT).read_bytes())),value)
            self.assertGreater(len(list((self.root/pub.SPOOL).glob('part-*.json-bytes'))),1)
        def test_encoder_failure_preserves_exact_row_without_formal_result(self):
            value=row()
            with patch.object(pub.layout,'pack',side_effect=ValueError('PURE_MODEL_ENCODER_FAILURE')):
                with self.assertRaises(ValueError):pub.publish_final(self.root,value)
            self.assertEqual(pub.retained_row(self.root),value);self.assertFalse((self.root/pub.OUTPUT).exists())
        def test_existing_results_or_spool_never_overwrite_or_reuse(self):
            value=row();pub.publish_final(self.root,value);before=(self.root/pub.OUTPUT).read_bytes()
            with self.assertRaises(ValueError):pub.publish_final(self.root,value)
            self.assertEqual((self.root/pub.OUTPUT).read_bytes(),before);self.assertEqual(pub.retained_row(self.root),value)
        def test_corrupt_part_and_manifest_path_escape_are_rejected(self):
            value=row();pub.publish_final(self.root,value);folder=self.root/pub.SPOOL;part=folder/'part-000.json-bytes';original=part.read_bytes()
            part.write_bytes(b'X'+original[1:])
            with self.assertRaises(ValueError):pub.retained_row(self.root)
            part.write_bytes(original);path=folder/pub.MANIFEST;meta=json.loads(path.read_bytes());meta['parts'][0]['name']='../../private-original'
            path.write_text(json.dumps(meta),encoding='utf-8')
            with self.assertRaises(ValueError):pub.retained_row(self.root)
        def test_no_authority_promotion_before_spool_or_result_creation(self):
            for key,value in(('accepted_count_delta',1),('accepted_count_delta',True),('P09_gate','CLOSED'),('P10_started',True),('Hancom_COM_Native_or_249_started',True)):
                bad=row();bad[key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):pub.publish_final(self.root,bad)
                self.assertFalse((self.root/pub.SPOOL).exists());self.assertFalse((self.root/pub.OUTPUT).exists())
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Models);result=unittest.TestResult();suite.run(result)
    for pin in pins:
        raw=(c.ROOT/pin['path']).read_bytes();c.require(len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['sha256'],'P585_MODEL_INPUT_CHANGED')
    for path in(c.ROOT/pub.OUTPUT,c.ROOT/pub.SPOOL,driver.worker.OWNED,c.ROOT/driver.worker.OBSERVATION):
        c.require(not path.exists()and not path.is_symlink()and not path.is_junction(),'P585_NO_ACTUAL_SQL_NAMESPACE_CREATED')
    record=dict(state='PASS_COMMON_LATE585_PURE_ADMISSION_AND_PUBLICATION_NOT_COMPILED_SQL_NATIVE_OR_GATE'if result.wasSuccessful()else'FAILED_COMMON_LATE585_PURE_MODELS',
        models=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
        failed_model_names=[case.id()for case,_ in result.failures+result.errors],source_pins=pins,fresh_inputs=len(pins),final_fresh_hashes=len(pins),
        own_cpu_selection=selection,elapsed_seconds=round(time.monotonic()-started,3),shared_verification_lock_acquired=False,
        actual_Cargo_SQL_Hancom_COM_or_Native_started=False,current_host_query_executed=False,SQL_case_state='NOT_RUN',
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,cleanup=True)
    proof=r.shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(record),NS(require=c.require,exact=r.a.exact))
    print(json.dumps({**{k:record[k]for k in('state','models','failed_model_names','fresh_inputs','final_fresh_hashes','elapsed_seconds','cleanup')},'receipt':proof}),flush=True)
    return 0 if result.wasSuccessful()else 2


if __name__=='__main__':raise SystemExit(main())
