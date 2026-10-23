"""Original OwnedPacer and fresh-reader invariants, not Native execution."""
import time
from types import SimpleNamespace as NS
import unittest
import owned_source_read_pressure as pressure
import native011_precise_boundary_pacer as precise


class PreciseBoundaryContracts(unittest.TestCase):
    def fixture(self):
        return NS(pacer=pressure.OwnedPacer(),read_passes=0,bytes_read=0,final_fresh_hashes=0,
            snapshots={},checkpoint=lambda:None,pressure=object(),maximum_parse_bytes=16777216)
    def test_only_fresh_clock_origin_changes_and_old_pacer_is_not_mutated(self):
        reader=self.fixture();before=dict(vars(reader));old=reader.pacer;saved=dict(vars(old))
        proof=precise.connect(reader,pressure)
        self.assertEqual(vars(old),saved);self.assertIs(type(reader.pacer),type(old))
        self.assertIs(reader.pacer.clock,time.perf_counter)
        self.assertTrue(all(vars(reader)[name] is value for name,value in before.items() if name!='pacer'))
        self.assertEqual(proof['maximum_burst_bytes'],65536)
        self.assertFalse(proof['read_hash_parse_counter_checkpoint_or_deadline_changed'])
    def test_second_adoption_cannot_reset_clock_or_credit(self):
        reader=self.fixture();precise.connect(reader,pressure);old=reader.pacer
        with self.assertRaises(ValueError):precise.connect(reader,pressure)
        self.assertIs(reader.pacer,old)
    def test_any_previous_read_or_final_hash_blocks_adoption(self):
        for name in ('read_passes','bytes_read','final_fresh_hashes'):
            reader=self.fixture();setattr(reader,name,1)
            with self.assertRaises(ValueError):precise.connect(reader,pressure)
        reader=self.fixture();reader.snapshots['known']={}
        with self.assertRaises(ValueError):precise.connect(reader,pressure)
    def test_prior_reservation_refund_or_sleep_blocks_adoption(self):
        for name,value in (('tokens',65535),('bytes_paced',1),('requested_sleep_seconds',.001)):
            reader=self.fixture();setattr(reader.pacer,name,value)
            with self.assertRaises(ValueError):precise.connect(reader,pressure)
        reader=self.fixture();reader.pacer.bytes_by_kind['other']=1
        with self.assertRaises(ValueError):precise.connect(reader,pressure)
    def test_selected_or_foreign_pacer_is_not_replaced(self):
        reader=self.fixture();reader.pacer.select('file.exe')
        with self.assertRaises(ValueError):precise.connect(reader,pressure)
        reader=self.fixture();reader.pacer=NS()
        with self.assertRaises(ValueError):precise.connect(reader,pressure)
    def test_original_rates_and_rate_selection_are_unchanged(self):
        reader=self.fixture();precise.connect(reader,pressure)
        for name,expected in (('file.exe',1048576),('source.py',2097152)):
            reader.pacer.select(name);self.assertEqual(reader.pacer.rate,expected)
    def test_original_no_accumulated_burst_and_actual_byte_accounting(self):
        reader=self.fixture();precise.connect(reader,pressure);pacer=reader.pacer;pacer.select('source.py')
        pacer.reserve(lambda:None);pacer.refund(100);self.assertEqual(pacer.bytes_paced,100)
        self.assertEqual(pacer.bytes_by_kind,{'binary':0,'other':100});self.assertLessEqual(pacer.tokens,65536)
    def test_source_clock_and_sleep_dependency_cannot_be_changed_before_adoption(self):
        reader=self.fixture();reader.pacer.clock=lambda:0
        with self.assertRaises(ValueError):precise.connect(reader,pressure)
        reader=self.fixture();reader.pacer.sleeper=lambda seconds:None
        with self.assertRaises(ValueError):precise.connect(reader,pressure)
