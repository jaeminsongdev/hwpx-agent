import json
import unittest
from unittest.mock import patch
import run_observed_r07_inventory as v

class ObservedR07InventoryTests(unittest.TestCase):
    def test_no_future_or_overwritten_receipt_in_helpers(self):
        names=v.helpers()
        self.assertIn(v.FAILED_PREP,names);self.assertIn(v.ORIGINAL_LIGHT,names)
        self.assertNotIn(v.PREP,names);self.assertNotIn(v.ACTUAL,names)
        self.assertNotEqual(v.PREP,v.FAILED_PREP)
    def test_closed_parent_sets_all68_and_rejects_stale(self):
        row=json.loads((v.c.ROOT/v.prior.CLOSING['path']).read_text(encoding='utf-8'))
        reader=object.__new__(v.Reader);reader.reader=type('FakeReader',(),{})()
        with patch.object(v.observation.ObservedReader,'json',return_value=row):reader.json(v.prior.CLOSING['path'])
        self.assertEqual(len(reader.reader.protected),68)
        row['current_build_accepted']=False
        with patch.object(v.observation.ObservedReader,'json',return_value=row):
            with self.assertRaises(ValueError):reader.json(v.prior.CLOSING['path'])
    def test_original_worker_delegation_no_recompile(self):
        with patch.object(v.prior,'worker',return_value=0) as checked:self.assertEqual(v.worker(v.prior.i.task_for(7)),0)
        checked.assert_called_once_with(v.prior.i.task_for(7))
        self.assertEqual(v.c.POLICY['emergency_cpu_consecutive_samples'],4)
    def test_redacted_failure_never_private_traceback(self):
        self.assertEqual(v.closed_error(ValueError('XML_PRODUCT_POSTCLOSED_LIST_PREPARATION_NOT_ACCEPTED')),
            'XML_PRODUCT_POSTCLOSED_LIST_PREPARATION_NOT_ACCEPTED')
        for error in (ValueError('private original.hwpx: secret'),OSError('private secret path')):
            self.assertEqual(v.closed_error(error),'OBSERVED_INVENTORY_REDACTED_FAILURE')
