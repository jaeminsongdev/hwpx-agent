import hashlib
import lzma
import unittest
from types import FunctionType

MODULE=None


def fixture():
    def digest(raw): return hashlib.sha256(raw).hexdigest()
    env=dict(digest.__globals__,__name__='p09_exact_profile_fixture')
    return FunctionType(digest.__code__,env),env


class Tests(unittest.TestCase):
    def test_hash_is_computed_by_original_and_default_module_unchanged(self):
        fn,env=fixture(); original=hashlib.sha256; meter=MODULE.Meter(lambda:True)
        with meter.patched([fn]): self.assertEqual(fn(b'opaque'),original(b'opaque').hexdigest())
        self.assertIs(hashlib.sha256,original); self.assertIs(env['hashlib'],hashlib)
        self.assertEqual(meter.stats['sha256']['calls'],1); self.assertEqual(meter.stats['sha256']['input_bytes'],6)
    def test_exception_preserves_error_and_restores_dependency(self):
        fn,env=fixture(); meter=MODULE.Meter(lambda:True); failure=ValueError('SYNTHETIC_PROFILE_STOP')
        with self.assertRaises(ValueError) as caught:
            with meter.patched([fn]): raise failure
        self.assertIs(caught.exception,failure); self.assertIs(env['hashlib'],hashlib); self.assertEqual(meter.swaps,[])
    def test_default_namespace_cannot_be_patched(self):
        fn,env=fixture(); env['__name__']='not_private'; meter=MODULE.Meter(lambda:True)
        with self.assertRaises(ValueError):
            with meter.patched([fn]): pass
        self.assertIs(env['hashlib'],hashlib)
    def test_lzma_memory_limit_flags_and_result_delegate_to_original(self):
        meter=MODULE.Meter(lambda:True); raw=b'opaque bounded fixture'*20; encoded=lzma.compress(raw)
        decoder=meter.decoder_factory(lzma.LZMADecompressor)(format=lzma.FORMAT_XZ,memlimit=32*1024*1024)
        self.assertEqual(decoder.decompress(encoded,max_length=65536),raw); self.assertTrue(decoder.eof)
        self.assertEqual(meter.stats['lzma_decompress']['calls'],1)
    def test_inactive_measurement_does_not_change_operation_or_record_work(self):
        fn,env=fixture(); meter=MODULE.Meter(lambda:False)
        with meter.patched([fn]): self.assertEqual(fn(b'opaque'),hashlib.sha256(b'opaque').hexdigest())
        self.assertEqual(meter.stats,{})


if __name__=='__main__': unittest.main()
