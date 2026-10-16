import hashlib
import unittest
from types import SimpleNamespace as NS

M=CODEC=None


class Tests(unittest.TestCase):
    def test_original_body_closure_and_default_dictionary_are_unchanged(self):
        fn=M.encoder(CODEC,1024*1024)
        self.assertIs(fn.__code__,CODEC.encode.__code__); self.assertIs(fn.__closure__,CODEC.encode.__closure__)
        self.assertEqual(CODEC.DICTIONARY_BYTES,8*1024*1024)
        self.assertEqual(fn.__globals__['DICTIONARY_BYTES'],1024*1024)
    def test_unsupported_dictionary_and_bool_are_rejected(self):
        for value in (True,0,2*1024*1024,8*1024*1024):
            with self.assertRaises(ValueError): M.encoder(CODEC,value)
    def test_actual_compressor_receives_one_mib_without_changing_decoder(self):
        fn=M.encoder(CODEC,1024*1024); old=fn.__globals__['lzma']; calls=[]
        def create(*args,**kwargs):
            calls.append(kwargs['filters'][0]['dict_size']); return old.LZMACompressor(*args,**kwargs)
        fn.__globals__['lzma']=NS(**{**vars(old),'LZMACompressor':create})
        raw=b'bounded opaque fixture'*200; encoded=fn(raw,lambda:None)
        self.assertEqual(CODEC.decode(encoded,lambda:None),raw); self.assertEqual(calls,[1024*1024])
        self.assertIs(CODEC.lzma,old)
    def test_two_fresh_decodes_preserve_every_byte_and_original_hash(self):
        raw=bytes(range(256))*17+b'\x00\xff \r\n'; encoded=M.encoder(CODEC,1024*1024)(raw,lambda:None)
        first=CODEC.decode(encoded,lambda:None); second=CODEC.decode(encoded,lambda:None)
        self.assertEqual(first,raw); self.assertEqual(second,raw); self.assertIsNot(first,second)
        self.assertEqual(hashlib.sha256(first).digest(),hashlib.sha256(raw).digest())
    def test_original_guard_failure_is_not_retried_or_suppressed(self):
        calls=[]; error=ValueError('SYNTHETIC_ORIGINAL_GUARD')
        def stopped(): calls.append(1); raise error
        with self.assertRaises(ValueError) as caught: M.encoder(CODEC,1024*1024)(b'safe',stopped)
        self.assertIs(caught.exception,error); self.assertEqual(calls,[1])
    def test_original_types_bounds_and_trailing_stream_guards_survive(self):
        fn=M.encoder(CODEC,1024*1024)
        for raw in (b'',bytearray(b'safe')):
            with self.assertRaises(ValueError): fn(raw,lambda:None)
        encoded=fn(b'safe',lambda:None)
        # A second complete stream is never accepted as one envelope.
        import base64,json
        row=json.loads(encoded); payload=base64.b64decode(row['payload']); row['payload']=base64.b64encode(payload+payload).decode('ascii')
        with self.assertRaises(ValueError): CODEC.decode(json.dumps(row).encode('ascii'),lambda:None)
    def test_selection_includes_each_fixed_group_not_only_small_inputs(self):
        rows=[dict(semantic_original_pin=dict(bytes=i+1),physical_envelope_pin=dict(path='old/'+str(i))) for i in range(162)]
        for i in range(7): rows[i]['physical_envelope_pin']['path']='x/legacy-zlib75/'+str(i)
        self.assertEqual([i for i,r in M.representatives(rows)],[74,160,161,6])
    def test_selection_rejects_incomplete_table_or_wrong_repack_count(self):
        with self.assertRaises(ValueError): M.representatives([])
        with self.assertRaises(ValueError): M.representatives([dict(semantic_original_pin=dict(bytes=1),physical_envelope_pin=dict(path='x'))]*162)


if __name__=='__main__': unittest.main()
