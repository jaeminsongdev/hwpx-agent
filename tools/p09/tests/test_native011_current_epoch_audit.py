"""Audit facade delegates to original epochs; no actual metadata/Native IO."""
from types import SimpleNamespace as NS
import unittest
import native011_current_epoch_audit as audit


class AuditFacadeContracts(unittest.TestCase):
    def test_only_explicit_readonly_generations_no_automatic_retry_loop(self):
        for value in (0,4,True,'2'):
            with self.assertRaisesRegex(ValueError,'CLOSED_READONLY_AUDIT_ID'):
                audit.PreparationAudit(None,None,run_id=value)

    def fixture(self):
        events=[]
        class Epochs:
            def __init__(self,factory):self.guard=None;self.records=[];self.broken=False
            def advance(self,stage):events.append(stage);self.guard=NS(samples=[dict(system_cpu_percent=1)])
            def check(self,*args,**kwargs):events.append(('check',args,kwargs));return 'checked'
            def close(self):events.append('close');self.records.append(dict(cleanup_confirmed=True));self.guard=None
        module=NS(Epochs=Epochs,STAGES=('construction','opening','metadata','closing'),
            MARKERS=('source_begin','connect_first_begin','consumer_begin','connect_second_begin'))
        return audit.PreparationAudit(module,lambda:None),events

    def test_original_epoch_acquire_check_and_close_delegation(self):
        driver,events=self.fixture();driver.acquire();samples=driver.samples
        self.assertEqual(driver.check(force=True),'checked');driver.close()
        self.assertEqual(events,['construction',('check',(),dict(force=True)),'close'])
        self.assertIs(driver.samples,samples);self.assertTrue(driver.cleanup)

    def test_failure_latched_on_the_original_driver_not_a_guard_restart(self):
        driver,_=self.fixture();driver.acquire();driver.fail()
        self.assertTrue(driver.epochs.broken)

    def test_audit_cannot_run_without_named_reader_preparation(self):
        driver,_=self.fixture()
        with self.assertRaisesRegex(ValueError,'ONE_PREPARED_ACTUAL_AUDIT'):
            driver.run(None,None,None,None)

    def test_partial_progress_retains_mismatch_and_never_claims_full_boundary(self):
        driver,_=self.fixture();driver.readers['opening']=NS(snapshots={'model':dict(bytes=2)},read_passes=1,bytes_read=2)
        result=driver.report(NS(data=NS(planned=NS(whole={'model':dict(bytes=1)}))))
        self.assertNotIn('whole_opening',result)
        self.assertEqual(result['opening_progress']['disagreements'][0]['path'],'model')


class AuditCheckpointContracts(unittest.TestCase):
    def fixture(self):
        opening=dict(actual_complete=True,fresh_inputs=1,bytes_read=1,full_pin_sha256='a'*64)
        metadata=dict(state='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE',fresh_inputs=1,
            final_fresh_hashes=1,metadata_body_executed=True,Frame_created=False,worker_created=False,GO_authorized=False)
        return dict(declared_whole_inputs=1,declared_whole_bytes=1,whole_pin_sha256='a'*64,
            whole_opening=opening,metadata=metadata,whole_closing=dict(opening)),[dict(path='model',bytes=1,sha256='a'*64)]

    def test_completed_metadata_snapshot_survives_later_result_mutation_without_authority(self):
        result,pins=self.fixture();payload=audit.checkpoint_payload('metadata',result,pins)
        result['metadata']['fresh_inputs']=999;pins[0]['bytes']=999
        self.assertEqual(payload['evidence']['metadata']['fresh_inputs'],1)
        self.assertEqual(payload['execution_code_source_pins'][0]['bytes'],1)
        self.assertFalse(payload['actual_whole_closing_complete'])
        self.assertFalse(payload['later_input_read_or_guard_may_be_skipped'])

    def test_partial_opening_or_unclosed_metadata_never_published_as_completed(self):
        for mode in ('opening','metadata'):
            result,pins=self.fixture()
            if mode=='opening':result['whole_opening']['actual_complete']=False
            else:result['metadata']['final_fresh_hashes']=0
            with self.assertRaises(ValueError):audit.checkpoint_payload(mode,result,pins)

    def test_second_boundary_must_match_entire_first_boundary(self):
        result,pins=self.fixture();result['whole_closing']['full_pin_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'EXACT_WHOLE_SECOND_BOUNDARY'):
            audit.checkpoint_payload('closing',result,pins)

    def test_named_phase_payload_does_not_grant_native_or_product_acceptance(self):
        result,pins=self.fixture()
        for phase in ('opening','metadata','closing'):
            payload=audit.checkpoint_payload(phase,result,pins)
            self.assertFalse(payload['actual_Native_Frame_or_READY15_or_product_qualified'])
            self.assertEqual(payload['accepted_count_delta'],0)
        with self.assertRaises(ValueError):audit.checkpoint_payload('native',result,pins)

    def test_publisher_receives_one_exclusive_snapshot_and_cannot_replay(self):
        driver=PreparationAuditFixture.make();result,pins=self.fixture();driver.result=result;calls=[]
        def publish(root,path,payload,api):
            calls.append((path,payload));return dict(path=path,bytes=1,sha256='a'*64)
        driver.publisher=NS(publish=publish);driver.publisher_api=NS();driver.check=lambda **kwargs:None
        driver.checkpoint(None,NS(snapshots={'model':pins[0]}),'metadata')
        with self.assertRaisesRegex(ValueError,'NO_CHECKPOINT_REPLAY_OR_OVERWRITE'):
            driver.checkpoint(None,NS(snapshots={'model':pins[0]}),'metadata')
        self.assertEqual(len(calls),1)


class PreparationAuditFixture:
    @staticmethod
    def make():
        return audit.PreparationAudit(NS(Epochs=lambda factory:NS()),lambda:None,run_id=3)
