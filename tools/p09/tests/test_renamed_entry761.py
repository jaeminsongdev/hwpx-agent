"""Reader-path regressions for the exact XZ/legacy boundary; no Native starts."""
import contextlib,copy,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_prepared_bookmark_native761 as entry
import run_prepared_bookmark_native755 as consumed
import compact_receipt_json as compact

ROOT=entry.r.c.ROOT
PRIOR='implementation/p09/evidence/p09-361-renamed-bookmark760-code001.v1.json'
FAILURE='implementation/p09/evidence/p09-361-prepared-bookmark755-native001.v1.json'

class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet=json.loads((ROOT/PRIOR).read_text(encoding='utf-8'))
        cls.prior=entry.codec.unpack(cls.packet,lambda:None)
    def reader(self,proof=None,packet=None):
        source=self.prior if proof is None else proof
        proof=copy.deepcopy({key:source[key]for key in ('state','cleanup','fresh_inputs','final_fresh_hashes','all_new_tests_passed','actual_native_started','ready_denial','execution_dependency_paths','source_pins')})
        # Models need the entry contract, not hundreds of historical resource rows.
        proof['ready_denial']={key:proof['ready_denial'][key]for key in ('cleanup','requests','result')}
        proof['state']=entry.STATE
        proof['execution_dependency_paths']=sorted(set(proof['execution_dependency_paths'])|{entry.SELF,__file_path__})
        pins={p['path']:p for p in proof['source_pins']}
        for name in (entry.SELF,__file_path__):pins[name]=dict(path=name,bytes=1,sha256='a'*64)
        proof['source_pins']=list(pins.values())
        checkpoint=Mock();reader=NS(checkpoint=checkpoint,json=Mock(return_value=entry.codec.pack(proof,lambda:None)if packet is None else packet),pin=Mock(side_effect=lambda name:pins[name]))
        return reader,proof
    def test_exact_actual_old_packet_reproduces_wrong_decoder(self):
        with self.assertRaisesRegex(ValueError,'XREF_LOSSLESS610_ENVELOPE'):entry.publisher.codec.unpack(self.packet)
        self.assertEqual(entry.codec.unpack(self.packet,lambda:None)['state'],self.prior['state'])
    def test_real_entry_reader_decodes_xz_and_checks_every_pin(self):
        reader,proof=self.reader();pins,paths,value=entry.load_code(reader)
        self.assertEqual(value,proof);self.assertEqual(set(pins),set(p['path']for p in proof['source_pins']))
        self.assertEqual(reader.pin.call_count,len(pins));self.assertIn(entry.SELF,paths);self.assertTrue(reader.checkpoint.called)
    def test_legacy_product_remains_explicit_legacy_decoder(self):
        packet=json.loads((ROOT/entry.runtime.prepared.PROOF).read_text(encoding='utf-8'))
        self.assertTrue(entry.publisher.codec.unpack(packet)['cleanup'])
        with self.assertRaises(ValueError):entry.codec.unpack(packet,lambda:None)
    def test_legacy_envelope_is_not_a_fallback_for_new_code(self):
        reader,proof=self.reader();reader.json.return_value=entry.publisher.codec.pack(proof)
        with self.assertRaises(ValueError):entry.load_code(reader)
        reader.pin.assert_not_called()
    def test_bad_envelope_hash_rejected_before_pin_or_execution(self):
        packet=copy.deepcopy(self.packet);packet['payload_sha256']='0'*64
        reader,_=self.reader(packet=packet)
        with self.assertRaises(ValueError):entry.load_code(reader)
        reader.pin.assert_not_called()
    def test_wrong_xz_profile_rejected(self):
        packet=compact.unpack(self.packet);packet['profile']='caller-selected';reader,_=self.reader(packet=compact.pack(packet))
        with self.assertRaises(ValueError):entry.load_code(reader)
        reader.pin.assert_not_called()
    def test_validation_status_and_retained_ready_are_still_required(self):
        for field,value in(('cleanup',False),('all_new_tests_passed',False),('actual_native_started',True),('final_fresh_hashes',0)):
            with self.subTest(field=field):
                proof=copy.deepcopy(self.prior);proof[field]=value;reader,_=self.reader(proof)
                with self.assertRaisesRegex(ValueError,'CURRENT_CODE_PROOF'):entry.load_code(reader)
        proof=copy.deepcopy(self.prior);proof['ready_denial']['result']['completed_callback_cases']=1;reader,_=self.reader(proof)
        with self.assertRaisesRegex(ValueError,'CURRENT_CODE_PROOF'):entry.load_code(reader)
    def test_missing_execution_dependency_is_not_qualified(self):
        reader,proof=self.reader();proof['execution_dependency_paths'].remove(entry.runtime.TARGET);reader.json.return_value=entry.codec.pack(proof,lambda:None)
        with self.assertRaisesRegex(ValueError,'WHOLE_EXECUTION_CLOSURE'):entry.load_code(reader)
    def test_source_pin_drift_is_not_qualified(self):
        reader,_=self.reader();reader.pin.side_effect=lambda name:dict(path=name,bytes=0,sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'CHANGED_INPUT_REQUALIFY'):entry.load_code(reader)
    def test_decoder_receives_resource_checkpoint_and_propagates_stop(self):
        reader,_=self.reader();reader.checkpoint.side_effect=ValueError('MODEL_RESOURCE_STOP')
        with self.assertRaisesRegex(ValueError,'MODEL_RESOURCE_STOP'):entry.load_code(reader)
        reader.pin.assert_not_called()
    def test_whole_entry_changes_only_codec_and_new_output_namespace(self):
        old=(ROOT/consumed.SELF).read_text(encoding='utf-8')
        expected=old.replace('SELF=runtime.ENTRY',"SELF='tools/p09/run_prepared_bookmark_native761.py'").replace('renamed-bookmark760-code001','renamed-bookmark762-code001').replace(consumed.STATE,entry.STATE).replace('prepared-bookmark755-','prepared-bookmark761-').replace('FAILED755_','FAILED761_').replace('CAPTURED755_','CAPTURED761_').replace('OBSERVED755_','OBSERVED761_').replace('proof=publisher.codec.unpack(reader.json(CODE))','proof=codec.unpack(reader.json(CODE),reader.checkpoint)')
        self.assertEqual((ROOT/entry.SELF).read_text(encoding='utf-8'),expected)
        self.assertIs(entry.runtime,consumed.runtime);self.assertIs(entry.runtime.io,consumed.runtime.io)
    def test_failed755_is_preserved_and_no_new_native_claim_or_cases(self):
        failure=entry.codec.unpack(json.loads((ROOT/FAILURE).read_text(encoding='utf-8')),lambda:None)
        self.assertEqual(failure['fresh_inputs'],1);self.assertFalse(failure['native_claim_created']);self.assertTrue(failure['cleanup'])
        self.assertNotEqual(entry.OUTPUT,consumed.OUTPUT)
        for path in (entry.OUTPUT,entry.CLAIM,entry.SCRATCH):self.assertFalse((ROOT/path).exists())
        for i in range(1,9):self.assertFalse((ROOT/entry.runtime.directory(i)).exists())

__file_path__='tools/p09/tests/test_renamed_entry761.py'
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contracts);out=io.StringIO();result=unittest.TextTestRunner(stream=out,verbosity=0).run(suite)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),actual_native_started=False,failed_test_ids=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures])))
    raise SystemExit(0 if result.wasSuccessful()else 2)
