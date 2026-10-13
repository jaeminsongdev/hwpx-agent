"""Current P151 contracts; no children, SQL or native app starts."""
import base64
import json
import re
import unittest
from unittest.mock import patch
import run_durable_negative_example_tests as s


class DurableNegativeExampleTests(unittest.TestCase):
    def test_whole_three_prior_bodies_inverse_exact(self):
        archive=json.loads((s.c.ROOT/s.ARCHIVE).read_text(encoding='utf-8'))
        for item in archive['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            current=(s.c.ROOT/item['path']).read_text(encoding='utf-8')
            self.assertEqual(s.recovered(raw,s.restore_previous(item['path'],current)),raw)

    def test_whole_preP150_root_and_provider_inverse_exact(self):
        archive=json.loads((s.c.ROOT/s.original.ARCHIVE).read_text(encoding='utf-8'))
        for item in archive['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            current=(s.c.ROOT/item['path']).read_text(encoding='utf-8')
            restored=s.original.restore_original(item['path'],s.restore_previous(item['path'],current))
            self.assertEqual(s.recovered(raw,restored),raw)

    def test_absent_or_duplicate_declared_delta_denied(self):
        name=s.original.ROOT_SOURCE;text=(s.c.ROOT/name).read_text(encoding='utf-8')
        for wrong in (text.replace('// End P151 negative-controls module.','removed'),text+text):
            with self.assertRaises(ValueError):s.restore_previous(name,wrong)

    def test_all27_required_no_filter_or_ignored_acceptance(self):
        import contextlib
        with contextlib.ExitStack() as stack:
            for p in s.variant():stack.enter_context(p)
            good='running 27 tests\ntest result: ok. 27 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;'
            s.original.validate_output(good)
            for wrong in (good+good,good.replace('27 passed','19 passed'),good.replace('0 ignored','1 ignored'),
                          good.replace('0 filtered','1 filtered')):
                with self.assertRaises(ValueError):s.original.validate_output(wrong)

    def test_new_target_cannot_overwrite_old_test_or_runtime_EXE(self):
        self.assertNotEqual(s.TARGET,s.original.TARGET)
        self.assertFalse((s.c.ROOT/s.original.BINARY).is_relative_to(s.TARGET))
        self.assertEqual(s.TOTAL,11+8+len(s.NEGATIVE_TESTS))

    def test_declared_controls_and_tests_unique_complete(self):
        self.assertEqual(len(s.CONTROL_CHECKS),len(set(s.CONTROL_CHECKS)))
        text=(s.c.ROOT/s.SOURCE).read_text(encoding='utf-8')
        self.assertEqual(tuple(re.findall(r'#\[test\]\s+fn ([a-z_]+)\(',text)),s.NEGATIVE_TESTS)
        checks=re.search(r'pub\(super\) const CHECKS: \[&str; 8\] = \[(.*?)\];',text,re.DOTALL)
        self.assertEqual(tuple(re.findall(r'"([a-zA-Z0-9_]+)"',checks.group(1))),s.CONTROL_CHECKS)

    def test_private_synthetic_target_guard_before_disk_write(self):
        text=(s.c.ROOT/s.original.BACKEND_SOURCE).read_text(encoding='utf-8')
        self.assertLess(text.index('record.content_sha256() != ContentDigest::of(super::durable_negative::PAYLOAD)'),
                        text.index('options.open(&path)'))
        self.assertIn('direct(&path, false)?',text)
        self.assertIn('share_mode(0).custom_flags(0x0020_0000)',text)
        self.assertIn('ciphertext.len() != size',text)
        self.assertLess(text.index('ContentDigest::of(&ciphertext) != record.encryption().ciphertext_sha256'),
                        text.index('file.write_all'))

    def test_original_live_negatives_precede_new_controls(self):
        text=(s.c.ROOT/s.original.PROVIDER_SOURCE).read_text(encoding='utf-8')
        begin=text.index('// P151 negative-controls extension:')
        end=text.index('// End P151 negative-controls extension.',begin)
        block=text[begin:end]
        self.assertLess(block.index('verify_live_approval('),block.index('super::durable_negative::exercise'))
        self.assertIn('if p.blobs.is_durable()',block);self.assertIn('revisions.head(&ctx, p.project, branch()?)? == head',block)

    def test_worker_rejects_other_generation_before_child(self):
        with patch.object(s.original,'worker') as worker:
            with self.assertRaises(ValueError):s.worker(s.original.TASK)
        worker.assert_not_called()

    def test_global_limits_unchanged_and_no_key_or_plaintext_log(self):
        self.assertEqual(s.c.POLICY['job_memory_limit_percent'],8)
        self.assertEqual(s.c.POLICY['job_memory_stop_percent'],7)
        self.assertEqual(s.c.POLICY['output_limit_bytes_per_stream'],32768)
        text=(s.c.ROOT/s.SOURCE).read_text(encoding='utf-8')
        self.assertNotIn('println!',text);self.assertNotIn('eprintln!',text)
        self.assertIn('key.fill(0); wrong.fill(0)',text);self.assertIn('hmac.fill(0)',text)


if __name__=='__main__':unittest.main()
