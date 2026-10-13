import unittest
from unittest.mock import patch
import run_writer_xml_product_inventory as d

class WriterInventoryTests(unittest.TestCase):
    def test_stale_or_failed_build_closing_not_accepted(self):
        for state in ('FAILED_NOT_ACCEPTED','PASS_SOURCE_XML_PRODUCT_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'):
            with self.assertRaises(ValueError):d.closing_scope(dict(state=state))

    def test_foreign_listing_worker_cannot_launch(self):
        with patch.object(d.i,'worker',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.worker(d.i.task_for(4))

    def test_worker_current_generation_target_and_restore(self):
        old=d.i.EXE_RUN;old_target=d.d.c.TARGET;calls=[]
        with patch.object(d.i,'worker',side_effect=lambda task:calls.append((task,d.i.EXE_RUN,d.d.c.TARGET)) or 0):
            self.assertEqual(d.worker(d.i.task_for(5)),0)
        self.assertEqual(calls,[(d.i.task_for(5),5,d.d.TARGET)])
        self.assertEqual(d.i.EXE_RUN,old);self.assertEqual(d.d.c.TARGET,old_target)

    def test_complete_original_parser_rejects_missing_and_extra_names(self):
        names=[f'case_{n}' for n in range(249)];text=''.join(n+': test\n' for n in names)
        d.i.validate_listing(text,names)
        for bad in (text.replace('case_0: test\n',''),text+'foreign: test\n',text+'case_0: test\n'):
            with self.assertRaises(ValueError):d.i.validate_listing(bad,names)

if __name__=='__main__':unittest.main()
