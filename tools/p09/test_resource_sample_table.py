"""The receipt layout must retain every sample and value, not thin or aggregate observations."""
import unittest
import resource_sample_table as t


class LayoutTests(unittest.TestCase):
    def test_empty_samples_and_unqualified_flags_are_preserved(self):
        value=dict(state='FAILED',resource_samples=[],native=False,accepted_count_delta=0)
        self.assertEqual(t.unpack(t.pack(value)),value)
    def test_every_sample_and_float_roundtrips_without_mutation(self):
        samples=[dict(time_utc='a',cpu=1.25,ram=50.125),dict(time_utc='b',cpu=90.0,ram=5.0)]
        value=dict(state='OBSERVED',resource_samples=samples,source_pins=[dict(path='a',bytes=7,sha256='x')])
        before=t.compact.raw(value);self.assertEqual(t.unpack(t.pack(value)),value);self.assertEqual(t.compact.raw(value),before)
    def test_a_changed_sample_column_is_rejected_not_dropped(self):
        with self.assertRaisesRegex(ValueError,'^RESOURCE_TABLE_COLUMNS$'):
            t.pack(dict(state='FAILED',resource_samples=[dict(cpu=1),dict(ram=2)]))
    def test_duplicate_column_and_short_row_are_rejected(self):
        for columns,rows in [(['cpu','cpu'],[[1,2]]),(['cpu','ram'],[[1]])]:
            with self.assertRaises(ValueError):t.decode(dict(state='FAILED',resource_sample_table=dict(profile=t.PROFILE,columns=columns,rows=rows)))
    def test_original_compact_payload_limit_is_not_relaxed(self):
        with self.assertRaisesRegex(ValueError,'^COMPACT_RECEIPT_PAYLOAD_LIMIT$'):
            t.pack(dict(state='FAILED',resource_samples=[],body='x'*(t.compact.MAXIMUM+1)))
    def test_no_existing_table_or_unknown_profile_is_accepted(self):
        with self.assertRaisesRegex(ValueError,'^RESOURCE_TABLE_INPUT$'):
            t.encode(dict(state='FAILED',resource_samples=[],resource_sample_table={}))
        with self.assertRaisesRegex(ValueError,'^RESOURCE_TABLE_PROFILE$'):
            t.decode(dict(state='FAILED',resource_sample_table=dict(profile='other',columns=[],rows=[])))


if __name__=='__main__':unittest.main()
