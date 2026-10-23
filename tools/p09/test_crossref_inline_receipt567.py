"""Pure serialization tests, no Native/COM, source/DB replay or common execution lock."""
import copy,json,unittest
from unittest.mock import patch
import compact_receipt_json as compact
import crossref_inline_receipt567 as subject

def pin(index=0):return dict(path=f'implementation/p09/evidence/source-{index}.json',bytes=100+index,sha256=f'{index:064x}')
def original():return dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',cleanup=False,
    source_pins=[pin()],boundary=dict(pins=[pin()],closed=False),
    partial_case=dict(phase='source_bind',error='P09_XREF_BIND_SOURCE_READ_LEASE_FAILED'),
    resource_samples=[dict(system_cpu_percent=18.57,available_ram_percent=42.317),dict(system_cpu_percent=15.47,available_ram_percent=42.869)])

class Codec(unittest.TestCase):
    def test_every_failure_value_order_and_occurrence_round_trips(self):
        row=original();before=compact.raw(row);encoded=subject.encode(row)
        self.assertEqual(len(encoded['pins']),1)
        self.assertEqual(compact.raw(subject.unpack(subject.pack(row))),before)
        self.assertEqual(compact.raw(row),before)
        restored=subject.decode(encoded);restored['boundary']['pins'][0]['bytes']=999
        self.assertEqual(restored['source_pins'][0]['bytes'],100)
        self.assertEqual(encoded['pins'][0]['bytes'],100)

    def test_publication_stays_below_original_cap_with_large_repeated_boundaries(self):
        pins=[pin(i)for i in range(230)]
        row=dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',cleanup=False,source_pins=pins,
            boundaries=[dict(label=f'boundary-{i}',pins=copy.deepcopy(pins),closed=False)for i in range(12)],
            resource_samples=[dict(system_cpu_percent=18.57,available_ram_percent=42.317)for _ in range(300)])
        with self.assertRaises(ValueError):compact.pack(row)
        packet=subject.pack(row)
        self.assertLessEqual(len((json.dumps(packet,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode()),compact.MAXIMUM)
        self.assertEqual(compact.raw(subject.unpack(packet)),compact.raw(row))

    def test_reference_corruption_and_state_mismatch_are_rejected(self):
        base=subject.encode(original())
        for value in(True,-1,1000,'0'):
            changed=copy.deepcopy(base);changed['document']['source_pins'][0]={subject.REF:value}
            with self.assertRaises(ValueError):subject.decode(changed)
        changed=copy.deepcopy(base);changed['state']='PASS_FAKE'
        with self.assertRaises(ValueError):subject.decode(changed)
        changed=copy.deepcopy(base);changed['pins'][0]['sha256']='invalid'
        with self.assertRaises(ValueError):subject.decode(changed)

    def test_original_marker_collision_and_depth_are_rejected_not_omitted(self):
        row=original();row['collision']={subject.REF:0}
        with self.assertRaises(ValueError):subject.pack(row)
        row=original();nested=[];row['nested']=nested
        for _ in range(subject.MAX_DEPTH+2):child=[];nested.append(child);nested=child
        with self.assertRaises(ValueError):subject.pack(row)

    def test_no_samples_notice_and_pin_mapping_key_orders_round_trip(self):
        row=dict(state='NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP',cleanup_confirmed=False,
            pins=[pin(),dict(reversed(list(pin().items())))])
        self.assertEqual(compact.raw(subject.unpack(subject.pack(row))),compact.raw(row))
        row=dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',resource_samples=[],tail=pin())
        self.assertEqual(compact.raw(subject.unpack(subject.pack(row))),compact.raw(row))

    def test_outer_integrity_limit_is_unchanged(self):
        row=dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',unknown_unique_text='x'*compact.MAXIMUM)
        with self.assertRaises(ValueError):subject.pack(row)
        packet=subject.pack(original());packet['payload_sha256']='0'*64
        with self.assertRaises(ValueError):subject.unpack(packet)

    def test_expansion_and_node_budgets_reject_before_unbounded_copying(self):
        large=pin();large['path']='p'*4096
        packet=subject.encode(dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',source_pins=[large]))
        packet['document']['source_pins']=[{subject.REF:0}for _ in range(40)]
        with patch.object(subject,'MAX_INPUT_BYTES',8192):
            with self.assertRaises(ValueError):subject.decode(packet)
        with patch.object(subject,'MAX_NODES',1):
            with self.assertRaises(ValueError):subject.decode(subject.encode(dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY')))

if __name__=='__main__':unittest.main()
