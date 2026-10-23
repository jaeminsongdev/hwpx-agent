"""Pure new008 path contracts; no actual Native capture directories or files."""
import unittest
from unittest.mock import Mock
import crossref_capture008_namespace as subject
import crossref_capture003_namespace as old3
import crossref_capture004_namespace as old4

class Tests(unittest.TestCase):
    def test_all40_fixed_paths_are_unique_and_disjoint_from_consumed003_and004(self):
        paths={subject.artifact(i,n)for i in range(1,9)for n in subject.FILES}
        self.assertEqual(len(paths),40)
        for old in(old3,old4):
            self.assertTrue(paths.isdisjoint({old.artifact(i,n)for i in range(1,9)for n in old.FILES}))
            self.assertEqual(subject.FILES,old.FILES)
        self.assertTrue(all('20261017-r01-c'not in name for name in paths))
    def test_no_case_subset_foreign_path_index_or_unknown_file_is_accepted(self):
        for index in(True,False,1.0,'1',0,9,-1,None):
            with self.assertRaises(ValueError):subject.directory(index)
        for name in('../opened.hwpx','Opened.hwpx','D:/private/document.hwpx','saved.hwpx/extra',None):
            with self.assertRaises(ValueError):subject.artifact(1,name)
    def test_existing_or_linked_directories_are_never_reused_moved_or_deleted(self):
        for kind in('exists','is_symlink','is_junction'):
            value=Mock();value.exists.return_value=False;value.is_symlink.return_value=False;value.is_junction.return_value=False
            getattr(value,kind).return_value=True;root=Mock();root.__truediv__=Mock(return_value=value)
            with self.assertRaises(ValueError):subject.require_absent(root)
            value.unlink.assert_not_called();value.rename.assert_not_called();value.mkdir.assert_not_called()
    def test_absence_checks_all_eight_without_creating_anything(self):
        value=Mock();value.exists.return_value=False;value.is_symlink.return_value=False;value.is_junction.return_value=False
        root=Mock();root.__truediv__=Mock(return_value=value);subject.require_absent(root)
        self.assertEqual(root.__truediv__.call_count,8);value.mkdir.assert_not_called()
    def test_namespace_has_no_native_claim_execution_or_approval_entry(self):
        self.assertEqual(subject.PROBE,'target/debug/examples/p09_crossref_capture008_probe.exe')
        for name in('execute','claim','generation','approve','main'):self.assertNotIn(name,vars(subject))

if __name__=='__main__':unittest.main()
