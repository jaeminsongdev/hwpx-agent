"""Adversarial bounded codec tests; no files, workers, Native or execution."""
import base64,hashlib,unittest,zlib
import compact_receipt_json as compact
import crossref_lossless_receipt610 as subject

class Codec(unittest.TestCase):
    def row(self):return dict(state='FAILED_ORIGINAL_STATE',generation=10,cleanup=False,values=[None,True,False,0,-1,1,1.0,-0.0,'한글',{'$p':1,'nodes':[1,2]}])
    def packet_for(self,raw):
        data=zlib.compress(raw,1)
        return dict(state='x',profile=subject.PROFILE,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(data),payload_base64=base64.b64encode(data).decode())
    def test_01_types_order_unicode_reserved_values_round_trip_exact(self):
        row=self.row();self.assertEqual(compact.raw(subject.unpack(subject.pack(row))),compact.raw(row))
    def test_02_failed_unqualified_statuses_never_promoted(self):
        for state in('FAILED_EXTERNAL_QUALIFIED_ENTRY','CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED'):
            row=self.row();row['state']=state;self.assertEqual(subject.unpack(subject.pack(row)),row)
    def test_03_complete_repeated_data_under_original_writer_cap(self):
        row=self.row();row['data']=[dict(path='fixed',bytes=10,sha256='a'*64)]*2000
        packet=subject.pack(row);self.assertLess(len(compact.raw(packet)),len(compact.raw(row)));self.assertEqual(compact.raw(subject.unpack(packet)),compact.raw(row))
    def test_04_changed_hash_length_state_are_rejected(self):
        for field,value in(('raw_sha256','0'*64),('raw_bytes',2),('state','PASS_INVENTED'),('compressed_bytes',1)):
            packet=subject.encode(self.row());packet[field]=value
            with self.assertRaises(ValueError):subject.decode(packet)
    def test_05_expansion_bomb_stops_at_declared_limit(self):
        packet=self.packet_for(b' '*1000000);packet['raw_bytes']=1000
        with self.assertRaisesRegex(ValueError,'EXPANDED_BYTE_LIMIT'):subject.decode(packet)
    def test_06_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_KEY'):subject.decode(self.packet_for(b'{"state":"x","state":"x"}'))
    def test_07_external_payload_unknown_codec_extra_fields_denied(self):
        for field,value in(('external_path','never-read'),('profile','OTHER')):
            packet=subject.encode(self.row());packet[field]=value
            with self.assertRaises(ValueError):subject.decode(packet)
    def test_08_invalid_base64_and_nonASCII_denied(self):
        for text in('!!!!','한글','Zg==\n','===='):
            packet=subject.encode(self.row());packet['payload_base64']=text
            with self.assertRaises(ValueError):subject.decode(packet)
    def test_09_depth_and_nonfinite_denied(self):
        row=self.row();value=[];row['deep']=value
        for _ in range(65):child=[];value.append(child);value=child
        with self.assertRaises(ValueError):subject.pack(row)
        for value in(float('nan'),float('inf')):
            with self.assertRaises(ValueError):subject.pack(dict(state='x',value=value))
    def test_10_original_caps_preserved(self):
        self.assertEqual(subject.MAX_INPUT_BYTES,4*1024*1024);self.assertEqual(subject.MAX_NODES,100000);self.assertEqual(subject.MAX_DEPTH,64);self.assertEqual(compact.MAXIMUM,262144)
        with self.assertRaises(ValueError):subject.pack(dict(state='x',value='x'*subject.MAX_INPUT_BYTES))
    def test_11_truncated_concatenated_trailing_streams_denied(self):
        packet=subject.encode(self.row());data=base64.b64decode(packet['payload_base64'])
        for bad in(data[:-1],data+b'extra',data+data):
            value=dict(packet,compressed_bytes=len(bad),payload_base64=base64.b64encode(bad).decode())
            with self.assertRaises(ValueError):subject.decode(value)
    def test_12_live_checkpoints_propagate_pressure(self):
        calls=[];packet=subject.pack(dict(state='x',data=list(range(2000))),lambda:calls.append(1));self.assertGreater(len(calls),10)
        def stop():raise ValueError('STOP_MODEL_RESOURCE')
        with self.assertRaisesRegex(ValueError,'STOP_MODEL_RESOURCE'):subject.unpack(packet,stop)
    def test_13_bool_lengths_and_missing_state_denied(self):
        for field in('raw_bytes','compressed_bytes'):
            packet=subject.encode(self.row());packet[field]=True
            with self.assertRaises(ValueError):subject.decode(packet)
        with self.assertRaises(ValueError):subject.pack({})
    def test_14_logical_node_count_bounded(self):
        with self.assertRaisesRegex(ValueError,'TREE_LIMIT'):subject.pack(dict(state='x',nodes=[0]*100000))
    def test_15_noncanonical_and_nonASCII_raw_denied(self):
        for raw in(b'{ "state": "x" }',b'not ascii\xff'):
            with self.assertRaises(ValueError):subject.decode(self.packet_for(raw))
    def test_16_corrupt_deflate_never_returns_partial(self):
        packet=self.packet_for(b'{"state":"x"}');data=bytearray(base64.b64decode(packet['payload_base64']));data[-1]^=1;packet['payload_base64']=base64.b64encode(data).decode()
        with self.assertRaises(ValueError):subject.decode(packet)

if __name__=='__main__':unittest.main()
