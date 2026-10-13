import unittest
import current_audit_reader_context as d

class CurrentReaderContextTests(unittest.TestCase):
    def fixture(self):
        old='prefix\n'+d.OLD_SIGNATURE+'body\n'+d.OLD_POLICY+'legacy guards\nsuffix\n'
        new=old.replace(d.OLD_SIGNATURE,d.NEW_SIGNATURE).replace(d.OLD_POLICY,d.NEW_POLICY)
        return old,new
    def test_only_declared_extension_restores_complete_legacy_body(self):
        old,new=self.fixture();self.assertEqual(d.restore(new,old),old)
        self.assertEqual(d.restore(new.replace('\n','\r\n'),old),old)
    def test_guard_deletion_duplicate_extension_or_changed_branch_rejected(self):
        old,new=self.fixture()
        for bad in (new.replace('legacy guards','SKIPPED'),new+d.NEW_SIGNATURE,
                    new.replace('validate_current_resources(run, build)','allow_everything()')):
            with self.assertRaises(ValueError):d.restore(bad,old)

if __name__=='__main__':unittest.main()
