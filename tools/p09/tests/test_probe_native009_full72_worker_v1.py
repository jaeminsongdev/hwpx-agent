import json
import unittest

MODULE=None


class Tests(unittest.TestCase):
    def test_known_code_and_basename_only(self):
        trace='Traceback:\n  File "D:/private/directory/probe.py", line 12, in run\nValueError: NATIVE009_PUBLIC_FAILURE'
        row=MODULE.closed_child_error(trace)
        self.assertEqual(row['exception_type'],'ValueError');self.assertEqual(row['error_code'],'NATIVE009_PUBLIC_FAILURE')
        self.assertEqual(row['frames'],[dict(file='probe.py',line=12,function='run')])
        self.assertNotIn('private',json.dumps(row));self.assertFalse(row['raw_log_preserved_or_printed'])

    def test_arbitrary_message_is_not_echoed(self):
        row=MODULE.closed_child_error('ValueError: private message value=EXAMPLE_SENSITIVE_VALUE')
        self.assertEqual(row['exception_type'],'ValueError');self.assertIsNone(row['error_code'])
        self.assertNotIn('EXAMPLE_SENSITIVE_VALUE',json.dumps(row))

    def test_identifier_looking_plaintext_not_exception_type(self):
        row=MODULE.closed_child_error('EXAMPLE_SENSITIVE_IDENTIFIER42')
        self.assertIsNone(row['exception_type']);self.assertIsNone(row['error_code'])
        self.assertNotIn('EXAMPLE_SENSITIVE_IDENTIFIER42',json.dumps(row))

    def test_uppercase_nonproject_value_not_error_code(self):
        row=MODULE.closed_child_error('ValueError: EXAMPLE_SENSITIVE_IDENTIFIER42')
        self.assertIsNone(row['error_code']);self.assertNotIn('EXAMPLE_SENSITIVE_IDENTIFIER42',json.dumps(row))

    def test_empty_and_large_logs_are_bounded_metadata_only(self):
        self.assertEqual(MODULE.closed_child_error('')['stderr_characters'],0)
        trace='EXAMPLE_PRIVATE_CONTENT'*2000+'\n'+''.join('  File "D:/private/file.py", line 1, in fn\n' for _ in range(20))+'TypeError: ordinary text'
        row=MODULE.closed_child_error(trace)
        self.assertEqual(row['stderr_characters'],len(trace));self.assertEqual(len(row['frames']),6)
        self.assertEqual(row['exception_type'],'TypeError');self.assertIsNone(row['error_code'])
        self.assertNotIn('EXAMPLE_PRIVATE_CONTENT',json.dumps(row))
