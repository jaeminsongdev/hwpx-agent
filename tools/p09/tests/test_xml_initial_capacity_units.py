import unittest
from unittest.mock import patch
import run_xml_initial_capacity_units as d

class CapacityUnitsTests(unittest.TestCase):
    def sample(self):
        old='prefix\n'+d.b.OLD_ENTRY+'\n'+d.b.OLD_CAP+'\nsuffix\n'
        core=old.replace(d.b.OLD_ENTRY,d.b.NEW_ENTRY).replace(d.b.OLD_CAP,d.b.NEW_CAP)
        tests='#[test]\n#[test]\n#[test]\nassert_eq!(originals, 36)\nusize::MAX\nassert_eq!(new, old)\n100_000\n256\n512\n'
        return old,core+d.b.MARKER+tests
    def test_exact_inverse_and_original_tests_preserved(self):
        old,current=self.sample();self.assertTrue(d.b.inverse(current,old))
        self.assertTrue(d.b.inverse(current.replace('\n','\r\n'),old))
    def test_undeclared_product_changes_rejected(self):
        old,current=self.sample()
        with self.assertRaises(ValueError):d.b.inverse(current,old+'authority skipped')
    def test_missing_duplicate_delta_rejected(self):
        old,current=self.sample()
        for changed in (current.replace(d.b.NEW_CAP,'SKIPPED'),current.replace(d.b.MARKER,d.b.NEW_ENTRY+d.b.MARKER)):
            with self.assertRaises(ValueError):d.b.inverse(changed,old)
    def test_missing_sparse_dense_or_corpus_oracle_rejected(self):
        old,current=self.sample()
        for token in ('assert_eq!(originals, 36)','100_000','assert_eq!(new, old)','usize::MAX'):
            with self.assertRaises(ValueError):d.b.inverse(current.replace(token,''),old)
    def test_complete_original_profile_no_test_filter(self):
        self.assertEqual(len(d.CONFIG),81)
        self.assertEqual(d.ARGS,['test','-p','hwpx-package','--lib',*[v for entry in d.CONFIG for v in ('--config',entry)]])
        self.assertNotIn('--release',d.ARGS);self.assertTrue(d.TASK.endswith('tests'))
    def test_foreign_worker_denied_before_launch(self):
        with patch.object(d.c,'worker',side_effect=AssertionError('NO_CHILD')):
            with self.assertRaises(ValueError):d.worker('foreign')

if __name__=='__main__':unittest.main()
