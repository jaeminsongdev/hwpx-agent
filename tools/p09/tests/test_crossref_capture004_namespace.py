"""Pure fixed path contracts. No directory/file writes or app execution."""
import unittest
from unittest.mock import Mock
import crossref_capture004_namespace as subject
import crossref_capture003_namespace as consumed
class Tests(unittest.TestCase):
    def test_all40_paths_are_unique_closed_and_disjoint_from_consumed003(self):
        paths={subject.artifact(i,n)for i in range(1,9)for n in subject.FILES}
        self.assertEqual(len(paths),40)
        self.assertTrue(paths.isdisjoint({consumed.artifact(i,n)for i in range(1,9)for n in consumed.FILES}))
        self.assertEqual(subject.FILES,consumed.FILES)
    def test_invalid_indices_names_and_foreign_paths_are_rejected(self):
        for index in(True,False,1.0,'1',0,9,-1,None):
            with self.assertRaises(ValueError):subject.directory(index)
        for name in('../opened.hwpx','Opened.hwpx','D:/private/document.hwpx','saved.hwpx/extra',None):
            with self.assertRaises(ValueError):subject.artifact(1,name)
    def test_existing_or_linked_directory_never_deleted_or_reused(self):
        for kind in('exists','is_symlink','is_junction'):
            value=Mock();value.exists.return_value=False;value.is_symlink.return_value=False;value.is_junction.return_value=False
            getattr(value,kind).return_value=True;root=Mock();root.__truediv__=Mock(return_value=value)
            with self.assertRaises(ValueError):subject.require_absent(root)
            value.unlink.assert_not_called();value.rename.assert_not_called();value.mkdir.assert_not_called()
    def test_absence_checks_exact_eight_without_creating_anything(self):
        value=Mock();value.exists.return_value=False;value.is_symlink.return_value=False;value.is_junction.return_value=False
        root=Mock();root.__truediv__=Mock(return_value=value);subject.require_absent(root)
        self.assertEqual(root.__truediv__.call_count,8);value.mkdir.assert_not_called()
    def test_namespace_cannot_issue_native_or_claim_or_execution_permission(self):
        self.assertEqual(subject.PROBE,'target/debug/examples/p09_crossref_capture004_probe.exe')
        for name in('execute','claim','generation','approve','main'):self.assertNotIn(name,vars(subject))
