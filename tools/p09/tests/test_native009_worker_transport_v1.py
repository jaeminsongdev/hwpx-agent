import copy
import hashlib
import unittest

MODULE=None
API=None
HINT=None
WIRE=None
GRAPH=None
CHECKPOINT=None


def forged(row):
    text=GRAPH.worker.encode.__globals__['json'].dumps(row,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)
    wire=text.encode('ascii');hint=copy.deepcopy(HINT)
    hint['capsule_pin'].update(bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
    return hint,wire


class Tests(unittest.TestCase):
    def test_only_three_exact_run_bound_slots_with_complete_inverses(self):
        self.assertEqual(len(API.run_limit_proofs),3)
        self.assertTrue(all(v['entire_code_inverse'] and v['old']==8 and v['new']==9 for v in API.run_limit_proofs))
        with self.assertRaises(ValueError):MODULE.run9(lambda:None)

    def test_new_context_not_native008_relabelled_or_other_case(self):
        self.assertEqual(API.validate(HINT)['run'],9)
        for key,value in (('run',8),('run',10),('index',164)):
            hint=copy.deepcopy(HINT);hint[key]=value
            with self.assertRaises(ValueError):API.validate(hint)

    def test_whole_original_reconstruction_retains_all69_rows(self):
        graph,proof=API.reconstruct(HINT,WIRE,CHECKPOINT)
        self.assertEqual(graph.binding.descriptors(),GRAPH.binding.descriptors())
        self.assertEqual(len(graph.binding.descriptors()),69)
        self.assertEqual(graph.worker.TASK,'case165-current-r009-tests')
        self.assertTrue(proof['whole_original_reconstruction_code_retained'])
        self.assertFalse(proof['Native009_or_GO_qualified'])

    def test_unchanged16KiB_limit_and_transport_hash(self):
        self.assertLessEqual(len(WIRE),16384);self.assertEqual(GRAPH.worker.MAX_BYTES,16384)
        with self.assertRaises(ValueError):API.reconstruct(HINT,WIRE+b' ',CHECKPOINT)
        with self.assertRaises(ValueError):API.reconstruct(HINT,b'x'*16385,CHECKPOINT)

    def test_unknown_failure_execution_cannot_be_changed_to_false(self):
        hint=copy.deepcopy(HINT);hint[MODULE.FIELD]['actual_failed_product_child_executed']=False
        with self.assertRaises(ValueError):API.validate(hint)
        self.assertIsNone(HINT[MODULE.FIELD]['actual_failed_product_child_executed'])

    def test_failure_and_prebody_declarations_remain_distinct(self):
        hint=copy.deepcopy(HINT);hint.pop(MODULE.FIELD)
        with self.assertRaises(ValueError):API.validate(hint)
        hint=copy.deepcopy(HINT);hint['closed_prebody_source_declaration']=hint[MODULE.FIELD]
        with self.assertRaises(ValueError):API.validate(hint)

    def test_changed_first_descriptor_not_a_scope_substitute(self):
        hint=copy.deepcopy(HINT);hint['first_descriptor']=copy.deepcopy(GRAPH.binding.descriptors()[1])
        with self.assertRaises(ValueError):API.reconstruct(hint,WIRE,CHECKPOINT)

    def test_changed_prior_pin_rejects_even_with_new_transport_hash(self):
        row=GRAPH.worker.decode.__globals__['json'].loads(WIRE.decode('ascii'),object_pairs_hook=GRAPH.worker.unique)
        row['descriptors'][0]['physical_envelope_pin']['sha256']='0'*64
        hint,wire=forged(row)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECKPOINT)

    def test_missing_failure_pair_cannot_decode_as_complete69(self):
        row=GRAPH.worker.decode.__globals__['json'].loads(WIRE.decode('ascii'),object_pairs_hook=GRAPH.worker.unique)
        row['descriptors'].pop()
        hint,wire=forged(row)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECKPOINT)

    def test_altered_failure_pin_is_not_authorized_by_recomputed_wire_hash(self):
        row=GRAPH.worker.decode.__globals__['json'].loads(WIRE.decode('ascii'),object_pairs_hook=GRAPH.worker.unique)
        row['descriptors'][-1]['semantic_original_pin']['path']=row['descriptors'][-1]['semantic_original_pin']['path'].replace('run008','run009')
        hint,wire=forged(row)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECKPOINT)

    def test_original_guard_stop_propagates_before_any_reconstruction(self):
        calls=[]
        def stop():calls.append(1);raise ValueError('ORIGINAL_STOP')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_STOP'):API.reconstruct(HINT,WIRE,stop)
        self.assertEqual(calls,[1])

    def test_worker_declaration_does_not_claim_parent_frame_or_acceptance(self):
        graph,proof=API.reconstruct(HINT,WIRE,CHECKPOINT)
        self.assertTrue(proof['parent_fresh_source_Frame_and_independent_oracle_still_required'])
        self.assertIsNone(graph.binding_module.native008_failure_alias['actual_failed_product_child_executed'])
        self.assertFalse(graph.binding_module.native008_failure_alias['current_product_or_GO_qualified'])
