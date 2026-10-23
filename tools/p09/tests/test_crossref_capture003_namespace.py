"""Fixed namespace contracts, no actual Native process or artifact writes."""
import unittest
from unittest.mock import Mock
import crossref_capture003_namespace as n
import crossref_external_batch_runtime as old

class Capture003Namespace(unittest.TestCase):
    def test_all40_artifacts_are_fixed_unique_and_disjoint_from_originals(self):
        paths={n.artifact(i,name)for i in range(1,9)for name in n.FILES}
        self.assertEqual(len(paths),40)
        for i in range(1,9):
            self.assertNotEqual(n.directory(i),old.artifact_directory(i))
            for name in n.FILES:self.assertTrue(n.artifact(i,name).startswith(n.directory(i)+'/'))

    def test_bool_float_strings_out_of_range_and_foreign_names_are_rejected(self):
        for index in (True,False,1.0,'1',0,9,-1,None):
            with self.assertRaises(ValueError):n.directory(index)
        for name in ('../opened.hwpx','Opened.hwpx','C:/outside.hwpx','saved.hwpx/extra',None):
            with self.assertRaises(ValueError):n.artifact(1,name)

    def test_existing_or_linked_attempt_fails_without_delete_or_move(self):
        for kind in ('exists','is_symlink','is_junction'):
            candidate=Mock();candidate.exists.return_value=False;candidate.is_symlink.return_value=False;candidate.is_junction.return_value=False
            getattr(candidate,kind).return_value=True
            root=Mock();root.__truediv__=Mock(return_value=candidate)
            with self.assertRaises(ValueError):n.require_absent(root)
            candidate.unlink.assert_not_called();candidate.rename.assert_not_called()

    def test_absence_inspects_all_eight_without_creating_directories(self):
        candidate=Mock();candidate.exists.return_value=False;candidate.is_symlink.return_value=False;candidate.is_junction.return_value=False
        root=Mock();root.__truediv__=Mock(return_value=candidate)
        n.require_absent(root)
        self.assertEqual(root.__truediv__.call_count,8);candidate.mkdir.assert_not_called()

    def test_names_are_inventory_not_execution_permit_or_run_selector(self):
        self.assertNotIn('execute',vars(n));self.assertNotIn('generation',vars(n))
        self.assertEqual(n.PROBE,'target/debug/examples/p09_crossref_capture003_probe.exe')
        self.assertEqual(n.FILES,('opened.hwpx','saved.hwpx','reopened.hwpx','target-trace.json','owner-identities.json'))
