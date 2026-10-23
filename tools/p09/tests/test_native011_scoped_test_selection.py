"""Negative selector contracts: paths alone cannot qualify the wrong module."""
from types import SimpleNamespace as NS
import unittest
import native011_scoped_test_runner as runner


class SelectionContracts(unittest.TestCase):
    def fixture(self):
        class Example(unittest.TestCase):
            def test_example(self):pass
        Example.__module__='requested_test_module'
        module=NS(__name__='requested_test_module',Example=Example)
        return {'requested_test_module':module},{'requested_test_module':1}

    def test_exact_ids_and_count_are_returned_from_actual_loaded_cases(self):
        modules,expected=self.fixture();suite,ids=runner.checked_suite(modules,expected)
        self.assertEqual(suite.countTestCases(),1)
        self.assertEqual(len(ids['requested_test_module']),1)
        self.assertTrue(ids['requested_test_module'][0].startswith('requested_test_module.'))

    def test_wrong_module_name_cannot_pass_with_correct_file_or_count(self):
        modules,expected=self.fixture();modules['requested_test_module'].__name__='old_test_module'
        with self.assertRaisesRegex(ValueError,'MODULE_NAME_MATCHES_REQUEST'):
            runner.checked_suite(modules,expected)

    def test_omitted_extra_and_wrong_count_rejected_before_execution(self):
        modules,expected=self.fixture()
        with self.assertRaisesRegex(ValueError,'EXACT_MODULE_SELECTION'):runner.checked_suite({},expected)
        with self.assertRaisesRegex(ValueError,'EXACT_MODULE_SELECTION'):
            runner.checked_suite(dict(modules,other=modules['requested_test_module']),expected)
        with self.assertRaisesRegex(ValueError,'EXACT_EXECUTED_TEST_IDS_AND_COUNT'):
            runner.checked_suite(modules,{'requested_test_module':2})


if __name__=='__main__':unittest.main()
