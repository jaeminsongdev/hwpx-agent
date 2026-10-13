import unittest
from unittest.mock import patch
import run_writer_xml_reuse_units as d

class WriterUnitsTests(unittest.TestCase):
    def sample(self):
        old='struct ValidationCounts\n'+d.b.OLD_PRESERVATION+'\n'+d.b.OLD_INDEX+'\n'
        core=old.replace('struct ValidationCounts','#[cfg_attr(test, derive(Debug, Eq, PartialEq))]\nstruct ValidationCounts')
        core=core.replace(d.b.OLD_PRESERVATION,d.b.NEW_PRESERVATION).replace(d.b.OLD_INDEX,d.b.NEW_INDEX)
        tests='#[test]\n#[test]\n#[test]\nassert_eq!(count, 36)\nassert_eq!(*plain_reads.borrow(), *shared_reads.borrow())\nvalidate_archive_original\ncallback_called.get()\n'
        return old,core+d.b.MARKER+tests

    def test_exact_inverse_accepts_only_declared_core_and_three_oracles(self):
        old,current=self.sample();self.assertTrue(d.b.inverse(current,old))
        self.assertTrue(d.b.inverse(current.replace('\n','\r\n'),old))

    def test_unrelated_original_code_change_rejected(self):
        old,current=self.sample()
        with self.assertRaises(ValueError):d.b.inverse(current+'ignored',old+'changed')

    def test_missing_or_duplicate_delta_rejected(self):
        old,current=self.sample()
        for changed in (current.replace(d.b.NEW_INDEX,'SKIPPED'),current.replace(d.b.MARKER,d.b.NEW_PRESERVATION+d.b.MARKER)):
            with self.assertRaises(ValueError):d.b.inverse(changed,old)

    def test_missing_read_or_callback_oracle_rejected(self):
        old,current=self.sample()
        for token in ('callback_called.get()','assert_eq!(*plain_reads.borrow(), *shared_reads.borrow())'):
            with self.assertRaises(ValueError):d.b.inverse(current.replace(token,''),old)

    def test_complete_original_profile_and_scope_not_filtered(self):
        self.assertEqual(d.ARGS,['test','-p','hwpx-package','--lib',*[v for entry in d.b.p.b.CONFIG for v in ('--config',entry)]])
        self.assertEqual(len(d.b.p.b.CONFIG),81)
        self.assertTrue(d.TASK.endswith('tests'));self.assertNotIn('--release',d.ARGS)

    def test_foreign_worker_rejected_before_any_launch(self):
        with patch.object(d.c,'worker',side_effect=AssertionError('NO_CHILD')):
            with self.assertRaises(ValueError):d.worker('foreign')

if __name__=='__main__':unittest.main()
