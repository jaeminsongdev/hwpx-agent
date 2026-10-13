from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_failed_receipt_manifest_v1 as m


class Tests(unittest.TestCase):
    def test_new_schema_and_path_are_not_old_eleven_manifest(self):
        self.assertNotEqual(m.SCHEMA,m.original.SCHEMA)
        self.assertNotEqual(m.PATH,m.original.PATH)
    def test_original_guard_error_identity_before_any_delegated_read(self):
        error=ValueError("ORIGINAL_STOP")
        class A:
            @staticmethod
            def read_exact(q,p):raise error
        with self.assertRaises(ValueError) as caught:m.load(None,{},A)
        self.assertIs(caught.exception,error)
    def test_wrong_shape_stops_before_large_prior_manifest(self):
        class A:
            @staticmethod
            def read_exact(q,p):return {"schema_version":m.SCHEMA}
            @staticmethod
            def require(ok,msg):
                if not ok:raise ValueError(msg)
        with patch.object(m.original,"load") as old:
            with self.assertRaises(ValueError):m.load(None,{},A)
        old.assert_not_called()
    def test_success_role_cannot_replace_failed_admission(self):
        self.assertEqual(m.failed.ROLE,"preserved_same_case_pre_product_failure_not_prior_product")
        self.assertTrue(m.failed.PHYSICAL.endswith(".failed.envelope.v1.json"))


if __name__=="__main__":unittest.main()
