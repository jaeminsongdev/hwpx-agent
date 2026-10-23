"""New publication contracts only. No Native, source editing or dispatch retry."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepared_bookmark632_receipt as subject


class Contracts(unittest.TestCase):
    def value(self):
        return dict(state='CAPTURED_MODEL_SEMANTICS_UNQUALIFIED', cleanup=True, source='MODEL',
                    references=[dict(index=i, sha256=hashlib.sha256(str(i).encode()).hexdigest()) for i in range(30)])

    def test_01_byte_exact_round_trip_and_state(self):
        v = self.value()
        self.assertEqual(subject.compact.raw(subject.unpack(subject.pack(v, lambda: None), lambda: None)), subject.compact.raw(v))

    def test_02_never_silently_use_old_codec(self):
        with self.assertRaises(ValueError):
            subject.legacy.unpack(subject.pack(self.value(), lambda: None))

    def test_03_old_codec_still_works_and_is_not_new_profile(self):
        v = self.value()
        old = subject.legacy.pack(v)
        self.assertEqual(subject.legacy.unpack(old), v)
        with self.assertRaises(ValueError):
            subject.unpack(old, lambda: None)

    def test_04_declared4MiB_and_bool_sizes_rejected_before_decompress(self):
        for size in (True, 0, subject.legacy.MAX_INPUT_BYTES+1):
            v = subject.compact.unpack(subject.pack(self.value(), lambda: None))
            v['xz']['original_bytes'] = size
            with patch.object(subject.xz, 'decode') as decode, self.assertRaises(ValueError):
                subject.unpack(subject.compact.pack(v), lambda: None)
            decode.assert_not_called()

    def test_05_wrong_original_hash_detected(self):
        v = subject.compact.unpack(subject.pack(self.value(), lambda: None))
        v['xz']['original_sha256'] = '0'*64
        with self.assertRaises(ValueError):
            subject.unpack(subject.compact.pack(v), lambda: None)

    def test_06_truncated_stream_is_not_partial_success(self):
        v = subject.compact.unpack(subject.pack(self.value(), lambda: None))
        v['xz']['payload'] = v['xz']['payload'][:-8]
        with self.assertRaises(ValueError):
            subject.unpack(subject.compact.pack(v), lambda: None)

    def test_07_profile_and_extra_keys_rejected(self):
        for changes in (dict(profile=subject.legacy.PROFILE), dict(permission=True), dict(state='PASS')):
            v = subject.compact.unpack(subject.pack(self.value(), lambda: None))
            v.update(changes)
            with self.assertRaises(ValueError):
                subject.unpack(subject.compact.pack(v), lambda: None)

    def test_08_original_tree_and_raw_limits_not_relaxed(self):
        self.assertEqual(subject.legacy.MAX_INPUT_BYTES, 4194304)
        self.assertEqual(subject.legacy.MAX_COMPRESSED_BYTES, 180000)
        self.assertEqual(subject.compact.MAXIMUM, 262144)
        v = dict(state='MODEL', text='x'*(subject.legacy.MAX_INPUT_BYTES+1))
        with patch.object(subject.xz, 'encode') as encode, self.assertRaises(ValueError):
            subject.pack(v, lambda: None)
        encode.assert_not_called()

    def test_09_original_compressed_cap_preserved(self):
        v = self.value()
        huge = dict(schema_version=subject.xz.SCHEMA, encoding=subject.xz.ENCODING,
                    original_bytes=1, original_sha256='0'*64,
                    payload=subject.base64.b64encode(b'x'*180001).decode())
        with patch.object(subject.xz, 'encode', return_value=subject.compact.raw(huge)), self.assertRaises(ValueError):
            subject.pack(v, lambda: None)

    def test_10_guard_failure_propagates_without_retry(self):
        count = []
        def stop():
            count.append(1)
            raise ValueError('STOP_CPU')
        with self.assertRaisesRegex(ValueError, 'STOP_CPU'):
            subject.pack(self.value(), stop)
        self.assertEqual(len(count), 1)

    def test_11_nonfinite_data_not_normalized(self):
        with self.assertRaises(ValueError):
            subject.pack(dict(state='MODEL', data=float('nan')), lambda: None)

    def test_12_forensic_path_injection_denied(self):
        from types import SimpleNamespace as NS
        manifest = dict(state='RAW_METADATA_RETAINED_NOT_ACCEPTANCE_OR_NATIVE_PERMIT',
                        profile='hwpx-agent.private.canonical-metadata-retention/v1',
                        bytes=subject.RAW_BYTES, sha256=subject.MANIFEST_SHA,
                        parts=[dict(path='../other', bytes=1, sha256='0'*64)]*14)
        reader = NS(root=Path('D:/MODELED'), json=lambda name: manifest)
        with patch.object(subject.files, 'directory'), self.assertRaisesRegex(ValueError, 'FIXED_PART_NO_PATH_INJECTION'):
            subject.retained(reader)


if __name__ == '__main__':
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Contracts).run(result)
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped),
                         failed_tests=[str(t) for t, _ in result.errors+result.failures], actual_native_started=False)))
    sys.exit(0 if result.wasSuccessful() else 2)
