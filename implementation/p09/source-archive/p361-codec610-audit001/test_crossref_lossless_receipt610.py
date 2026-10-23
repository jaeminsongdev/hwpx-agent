"""Adversarial/non-Native codec contracts; no files, workers, claims or execution."""
import copy,json,unittest
import compact_receipt_json as compact
import crossref_lossless_receipt610 as subject

class Codec(unittest.TestCase):
    def row(self):return dict(state='FAILED_ORIGINAL_STATE',generation=10,cleanup=False,values=[None,True,False,0,-1,1,1.0,-0.0,'한글',{'$p':1,'nodes':[1,2]}])
    def test_01_types_keys_order_unicode_and_reserved_looking_values_round_trip_exact(self):
        row=self.row();self.assertEqual(compact.raw(subject.unpack(subject.pack(row))),compact.raw(row))
    def test_02_failed_partial_and_unqualified_statuses_are_never_promoted(self):
        for state in('FAILED_EXTERNAL_QUALIFIED_ENTRY','CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED'):
            row=self.row();row['state']=state;self.assertEqual(subject.unpack(subject.pack(row)),row)
    def test_03_repeated_whole_containers_reduce_without_omitting_any_occurrence(self):
        row=self.row();row['repeated']=[{'source_pins':[dict(path='fixed',bytes=10,sha256='a'*64)]*30}]*200
        packet=subject.pack(row);self.assertLess(len(compact.raw(packet)),len(compact.raw(row)));self.assertEqual(compact.raw(subject.unpack(packet)),compact.raw(row))
    def test_04_changed_hash_length_or_state_is_rejected(self):
        for field,value in(('raw_sha256','0'*64),('raw_bytes',2),('state','PASS_INVENTED')):
            packet=subject.encode(self.row());packet[field]=value
            with self.assertRaises(ValueError):subject.decode(packet)
    def test_05_self_forward_bool_and_negative_references_are_denied(self):
        for ref in(0,True,-1,99999):
            packet=dict(state='X',profile=subject.PROFILE,raw_bytes=10,raw_sha256='a'*64,nodes=[[1,[ref]]],root=0)
            with self.assertRaises(ValueError):subject.decode(packet)
    def test_06_duplicate_dictionary_keys_are_rejected_before_expansion(self):
        packet=subject.encode(dict(state='x',a=1));packet['nodes'][-1][1][-2]=packet['nodes'][-1][1][0]
        with self.assertRaisesRegex(ValueError,'DUPLICATE_KEY'):subject.decode(packet)
    def test_07_unknown_node_tags_and_extra_envelope_fields_are_denied(self):
        for mode in('tag','field'):
            packet=subject.encode(self.row())
            if mode=='tag':packet['nodes'][0][0]=9
            else:packet['external_payload_path']='never-read'
            with self.assertRaises(ValueError):subject.decode(packet)
    def test_08_unreachable_and_duplicate_nodes_are_denied(self):
        packet=subject.encode(self.row());packet['nodes'].append([0,'unreachable']);packet['root']=len(packet['nodes'])-1
        with self.assertRaises(ValueError):subject.decode(packet)
        packet=subject.encode(self.row());packet['nodes'].append(packet['nodes'][0]);packet['root']=len(packet['nodes'])-1
        with self.assertRaises(ValueError):subject.decode(packet)
    def test_09_deep_and_nonfinite_inputs_fail_closed(self):
        row=self.row();value=[];row['deep']=value
        for _ in range(65):n=[];value.append(n);value=n
        with self.assertRaises(ValueError):subject.encode(row)
        for value in(float('nan'),float('inf')):
            with self.assertRaises(ValueError):subject.encode(dict(state='x',value=value))
    def test_10_original_fourMiB_and_256KiB_caps_are_kept(self):
        self.assertEqual(subject.MAX_INPUT_BYTES,4*1024*1024);self.assertEqual(compact.MAXIMUM,262144)
        with self.assertRaises(ValueError):subject.pack(dict(state='x',value='x'*subject.MAX_INPUT_BYTES))
    def test_11_expansion_bomb_is_stopped_by_byte_budget_before_large_allocation(self):
        nodes=[[0,'x'*256]]
        for i in range(1,18):nodes.append([1,[i-1,i-1]])
        packet=dict(state='x',profile=subject.PROFILE,raw_bytes=1000,raw_sha256='a'*64,nodes=nodes,root=len(nodes)-1)
        with self.assertRaisesRegex(ValueError,'EXPANDED_BYTE_LIMIT'):subject.decode(packet)
    def test_12_checkpoint_remains_live_during_both_encode_and_expand(self):
        calls=[];row=dict(state='x',data=list(range(2000)))
        packet=subject.pack(row,lambda:calls.append(1));self.assertGreater(len(calls),10)
        def stop():raise ValueError('STOP_MODEL_RESOURCE')
        with self.assertRaisesRegex(ValueError,'STOP_MODEL_RESOURCE'):subject.unpack(packet,stop)

if __name__=='__main__':unittest.main()
