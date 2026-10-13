import unittest
from unittest.mock import patch
import build_xml_capacity_product_r3 as d

class XmlProductR3InventoryTests(unittest.TestCase):
    def test_current_unwritten_receipts_are_not_required_inputs(self):
        with patch.object(d.prior.prior,'PREPARATION','fixture/not-written-preparation.json'), \
                patch.object(d.prior.prior,'ACTUAL','fixture/not-written-actual.json'):
            names=d.helpers()
        self.assertNotIn('fixture/not-written-preparation.json',names);self.assertNotIn('fixture/not-written-actual.json',names)
        self.assertIn('implementation/p09/evidence/p09-177-xml-capacity-product-build.actual-run01.v1.json',names)
        self.assertIn('implementation/p09/evidence/p09-177-xml-capacity-product-build.preparation-run01.v1.json',names)
        self.assertIn(d.SELF,names);self.assertEqual(len(names),len(set(names)))
    def test_helper_delta_keeps_rate_worker_and_original_recipe(self):
        before=d.prior.prior.recipe()
        with patch.object(d.prior,'worker',return_value=2) as worker:self.assertEqual(d.worker('p152-current-stored-build-r07'),2)
        worker.assert_called_once_with('p152-current-stored-build-r07')
        self.assertEqual(before,d.prior.prior.recipe());self.assertEqual(d.prior.pressure.BINARY_RATE,1048576)

if __name__=='__main__':unittest.main()
