"""No IO: terminal evidence and guard sequencing model contracts."""
import base64
import hashlib
from types import SimpleNamespace as NS
import unittest
import native011_readonly_frame_driver as driver


class ReadonlyDriverContracts(unittest.TestCase):
    def test_full_frame_parts_are_bounded_and_lossless_without_truncation(self):
        raw=b'x'*400001;parts=driver.frame_parts(raw)
        restored=b''.join(base64.b64decode(part['base64']) for part in parts)
        self.assertEqual(restored,raw);self.assertEqual(len(parts),3)
        for i,part in enumerate(parts):
            block=base64.b64decode(part['base64']);self.assertEqual(part['index'],i)
            self.assertEqual(part['bytes'],len(block));self.assertEqual(part['sha256'],hashlib.sha256(block).hexdigest())
            self.assertLess(len(part['base64']),250000)
    def test_empty_or_oversized_frame_evidence_not_accepted(self):
        for raw in (b'',b'x'*(driver.MAX_FRAME_BYTES+1),'frame'):
            with self.assertRaises(ValueError):driver.frame_parts(raw)
    def test_closed_attempts_and_distinct_construction_output(self):
        self.assertNotEqual(driver.Driver(1).output,driver.Driver(1,construct_only=True).output)
        self.assertTrue(driver.Driver(4).output.endswith('probe004.v1.json'))
        self.assertFalse(driver.Driver(4).exact_read);self.assertTrue(driver.Driver(5).exact_read)
        self.assertTrue(driver.Driver(6).exact_read);self.assertTrue(driver.Driver(6).observe_decoder)
        self.assertFalse(driver.Driver(5).observe_decoder);self.assertIsNone(driver.Driver(6).decoder_timing)
        self.assertTrue(driver.Driver(7).chunk_join);self.assertFalse(driver.Driver(6).chunk_join)
        self.assertTrue(driver.Driver(7).exact_read);self.assertTrue(driver.Driver(7).observe_decoder)
        self.assertTrue(driver.Driver(8).metadata_tail);self.assertFalse(driver.Driver(7).metadata_tail)
        self.assertTrue(driver.Driver(8).chunk_join);self.assertIsNone(driver.Driver(8).metadata_tail_link)
        for attempt in (0,9,True):
            with self.assertRaises(ValueError):driver.Driver(attempt)

    def test_actual_frame_codec_witness_requires_same_class_and_method_reference(self):
        class Projection:
            def decode_fresh(self,*args):pass
        obj=driver.Driver(7);obj.chunk_link=NS(projection_type=Projection,method=Projection.decode_fresh,
            metadata_projection=Projection())
        evidence=obj.codec_evidence(NS(explicit_projection=Projection()))
        self.assertTrue(evidence['candidate_codec_namespace_used_by_both'])
        self.assertFalse(evidence['actual_Native_or_product_qualified'])
        class Wrong(Projection):pass
        with self.assertRaises(ValueError):obj.codec_evidence(NS(explicit_projection=Wrong()))

    def test_metadata_tail_evidence_reads_only_existing_complete_original_counters(self):
        class Reader:pass
        reader=Reader();reader.snapshots={'semantic':{}};reader._exact_input_sizes={'physical':3}
        reader.final_fresh_hashes=1;reader.read_passes=2;reader.bytes_read=6
        reader.pacer=NS(bytes_paced=6,reserved_bytes=8,refunded_bytes=2,pending=None,request=None,
            failed=False,reservations=4);reader.open_pacer=NS(requests=2)
        owner=NS(whole={'physical':dict(bytes=3)},metadata_connection=NS(readers=[reader]))
        obj=driver.Driver(8);obj.metadata_tail_link=NS(selected_reader=Reader)
        row=obj.metadata_evidence(owner)
        self.assertEqual(row['physical_bytes_read'],6);self.assertEqual(row['query_requests'],2)
        self.assertEqual(row['fresh_inputs'],row['final_fresh_hashes']);self.assertFalse(row['hash_JSON_source_or_closing_cache'])
        self.assertFalse(row['actual_Native_or_product_qualified'])
        for kind in ('closing','scope','pending','bytes'):
            with self.subTest(kind=kind):
                reader.final_fresh_hashes=1;reader._exact_input_sizes={'physical':3}
                reader.pacer.pending=None;reader.pacer.bytes_paced=6
                if kind=='closing':reader.final_fresh_hashes=0
                if kind=='scope':reader._exact_input_sizes={'wrong':3}
                if kind=='pending':reader.pacer.pending=1
                if kind=='bytes':reader.pacer.bytes_paced=5
                with self.assertRaises(ValueError):obj.metadata_evidence(owner)

    def terminal_fixture(self,*,second_complete_bytes=False):
        def reader(passes,actual):
            return NS(read_passes=passes,bytes_read=actual,semantic_decode_counts={'physical':1},
                pacer=NS(bytes_paced=actual,requested_sleep_seconds=.1,reservations=4,
                    reserved_bytes=actual+1,refunded_bytes=1,pending=None,failed=False))
        return NS(state='CLOSED',held=NS(closed=True),registered=False,
            inputs={'a':dict(bytes=3),'b':dict(bytes=3)},boundaries=[dict(role='before')],
            readers=[reader(2,6),reader(2,6) if second_complete_bytes else reader(1,3)])

    def test_terminal_partial_reader_counters_remain_actual_and_closed_only(self):
        frame=self.terminal_fixture();row=driver.terminal_readers(frame)
        self.assertEqual(row['declared_input_bytes'],6);self.assertEqual(row['recorded_complete_boundaries'],1)
        self.assertEqual(row['readers'][1]['actual_bytes_read'],3)
        self.assertEqual(row['readers'][1]['paced_bytes'],3)
        self.assertFalse(row['readers'][1]['recorded_complete_boundary'])
        self.assertFalse(row['actual_whole_Native_or_product_qualified'])
        frame.held.closed=False
        with self.assertRaisesRegex(ValueError,'AFTER_ORIGINAL_CLOSE_ONLY'):driver.terminal_readers(frame)

    def test_full_byte_counts_never_create_missing_semantic_boundary(self):
        row=driver.terminal_readers(self.terminal_fixture(second_complete_bytes=True))
        self.assertEqual(row['readers'][1]['actual_bytes_read'],6)
        self.assertFalse(row['readers'][1]['recorded_complete_boundary'])
        self.assertEqual(row['recorded_complete_boundaries'],1)

    def test_timing_summary_preserves_counts_and_values_without_mutating_rows(self):
        row=dict(attempts=2,roles=dict(metadata=dict(attempts=2,completed=2,rows=[{},{}],observed_wall_total=.2)))
        result=driver.timing_summary(row)
        self.assertEqual(result['roles']['metadata']['recorded_row_count'],2)
        self.assertNotIn('rows',result['roles']['metadata']);self.assertEqual(len(row['roles']['metadata']['rows']),2)
        self.assertEqual(result['roles']['metadata']['observed_wall_total'],.2)

    def test_terminal_writer_splits_timing_after_close_without_skipping_rows(self):
        obj=driver.Driver(6);obj.closed=True;obj.records=[]
        frame=NS(state='CLOSED',held=NS(closed=True),registered=False,inputs={'a':dict(bytes=1)},
            readers=[],boundaries=[],summary=lambda:dict(frame_state='CLOSED'))
        obj.native=NS(frame=frame,proof={});obj.decoder_timing=NS(evidence=lambda:dict(attempts=1,
            roles=dict(metadata=dict(attempts=2,completed=2,rows=[{},{}],observed_wall_total=.2))))
        captured={};markers=[];obj._marker=markers.append
        def publish(root,name,body,a):
            captured[name]=body
            return dict(path=name,bytes=1,sha256='a'*64)
        row=dict(state='FAILED_TEST_NOT_QUALIFIED');obj._finish(None,row,NS(publish=publish),NS(exact=lambda *args:None))
        pin=row['shared_decoder_timing_observation_artifact']
        self.assertEqual(len(captured[pin['path']]['roles']['metadata']['rows']),2)
        self.assertEqual(row['shared_decoder_timing_observation']['roles']['metadata']['recorded_row_count'],2)
        self.assertEqual(markers,[3]);self.assertEqual(row['state'],'FAILED_TEST_NOT_QUALIFIED')
    def test_native_phase_blocks_any_new_guard_rotation(self):
        obj=driver.Driver(1);obj.native=object()
        with self.assertRaisesRegex(ValueError,'NO_ROTATION_AFTER_NATIVE_FRAME'):obj.advance('opening')
    def test_original_failure_survives_terminal_publication_failure(self):
        obj=driver.Driver(1);obj.closed=False;row=dict(state='FAILED_NATIVE_CHECK',error_code='ORIGINAL_NATIVE_FAILURE')
        obj.finish(None,row,None,None)
        self.assertEqual(row['error_code'],'ORIGINAL_NATIVE_FAILURE')
        self.assertIn('terminal_evidence_publication_error',row)
    def test_success_is_not_preserved_when_full_evidence_cannot_be_written(self):
        obj=driver.Driver(1);row=dict(state='PASS_UNQUALIFIED_CONSTRUCTION')
        obj.finish(None,row,None,None)
        self.assertEqual(row['state'],'FAILED_READONLY_FRAME_EVIDENCE_NOT_ACCEPTED')
    def test_guard_close_is_idempotent_and_does_not_restart_a_scope(self):
        obj=driver.Driver(1);obj.close();obj.close();self.assertTrue(obj.closed);self.assertEqual(obj.records,[])
    def test_construct_only_finish_does_not_run_or_publish_any_frame(self):
        obj=driver.Driver(1,construct_only=True);obj.closed=True;row={}
        obj.finish(None,row,None,None)
        self.assertFalse(row['Native_clock_reset_or_extended']);self.assertNotIn('actual_Native_Frame_created',row)
    def test_new_preparation_opening_retains_original_open_pacer_and_rejects_used_reader(self):
        import accept_case112_current_epoch as a
        import native011_precise_boundary_pacer as precise
        reader=a.AcceptanceReader('.',lambda:None);before=dict(vars(reader));pacer=reader.open_pacer
        proof=driver.precise_opening(reader,a.pressure,precise)
        self.assertIs(reader.open_pacer,pacer)
        self.assertTrue(all(vars(reader)[name] is value for name,value in before.items() if name!='pacer'))
        self.assertTrue(proof['original_open_pacer_and_stage_deadline_retained'])
        self.assertEqual(proof['rates'],dict(binary=1048576,other=2097152))
        with self.assertRaises(ValueError):driver.precise_opening(reader,a.pressure,precise)
        reader=a.AcceptanceReader('.',lambda:None);reader.read_passes=1
        with self.assertRaises(ValueError):driver.precise_opening(reader,a.pressure,precise)
    def exact_fixture(self):
        obj=driver.Driver(5);obj.exact_factory=NS(state=NS(attempts=2,completed=2,failed=False,proofs=[{},{}]))
        def reader():
            return NS(_exact_input_sizes={'one':3,'two':4},read_passes=2,bytes_read=7,
                pacer=NS(bytes_paced=7,pending=None,request=None,failed=False,reserved_bytes=9,
                    refunded_bytes=2,reservations=4,tokens=65529,requested_sleep_seconds=0.))
        frame=NS(inputs={'one':dict(bytes=3),'two':dict(bytes=4)},readers=[reader(),reader()])
        return obj,frame
    def test_exact_full_scope_evidence_requires_both_fresh_readers_and_byte_escrow(self):
        obj,frame=self.exact_fixture();proof=obj.exact_evidence(frame)
        self.assertEqual(proof['completed'],2);self.assertEqual(len(proof['readers']),2)
        self.assertFalse(proof['product_or_worker_executed'])
    def test_incomplete_exact_factory_or_unreturned_byte_reservation_is_not_accepted(self):
        for kind in ('attempts','failed','bytes','scope','pending','refund'):
            obj,frame=self.exact_fixture()
            if kind=='attempts':obj.exact_factory.state.completed=1
            if kind=='failed':obj.exact_factory.state.failed=True
            if kind=='bytes':frame.readers[1].bytes_read=6
            if kind=='scope':frame.readers[1]._exact_input_sizes={'one':7}
            if kind=='pending':frame.readers[1].pacer.pending=1
            if kind=='refund':frame.readers[1].pacer.refunded_bytes=1
            with self.assertRaises(ValueError):obj.exact_evidence(frame)
