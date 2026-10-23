import hashlib,json,unittest
import compact_receipt_json as module


class Contracts(unittest.TestCase):
    def test_all_json_values_order_absent_null_false_and_trace_are_preserved(self):
        value=dict(state='FAILED_OR_PARTIAL_NOT_PROMOTED',absent_distinct=dict(null=None,false=False,true=True),
            source_pins=[dict(path='a',bytes=1,sha256='0'*64)],trace=[0,1.25,-0.0,True,None],steps=[['case','ok']])
        packet=module.pack(value);self.assertEqual(module.unpack(packet),value);self.assertNotIn('absent',module.unpack(packet)['absent_distinct'])
        self.assertEqual(packet['state'],value['state']);self.assertEqual(module.raw(module.unpack(packet)),module.raw(value))
    def test_large_repeated_metadata_fits_without_removing_any_fields(self):
        value=dict(state='SCOPED_ONLY',source_pins=[dict(path=f'crates/component/{i:04}.rs',bytes=i,sha256='a'*64)for i in range(832)],
            resource_samples=dict(columns=['cpu','ram'],rows=[[i/10,50.0]for i in range(400)]))
        packet=module.pack(value);self.assertEqual(module.unpack(packet),value)
        self.assertLess(len(json.dumps(packet,indent=2)),module.MAXIMUM)
    def test_tampered_size_hash_state_and_unknown_field_are_rejected(self):
        packet=module.pack(dict(state='FAIL',cleanup=True))
        for key,value in[('payload_utf8_bytes',True),('payload_utf8_bytes',packet['payload_utf8_bytes']+1),('payload_sha256','0'*64),('state','PASS'),('unknown',1)]:
            bad=dict(packet);bad[key]=value
            with self.assertRaises((ValueError,UnicodeError)):module.unpack(bad)
    def test_nonfinite_oversize_duplicate_and_noncanonical_payloads_fail_closed(self):
        for value in[dict(state='FAIL',number=float('nan')),dict(state='FAIL',huge='x'*module.MAXIMUM)]:
            with self.assertRaises(ValueError):module.pack(value)
        packet=module.pack(dict(state='FAIL'))
        for data in[b'{"state":"FAIL","state":"FAIL"}',b'{ "state":"FAIL" }',b'{"state":"FAIL","n":Infinity}']:
            bad=dict(packet,payload_json=data.decode('ascii'),payload_utf8_bytes=len(data),payload_sha256=hashlib.sha256(data).hexdigest())
            with self.assertRaises(ValueError):module.unpack(bad)
