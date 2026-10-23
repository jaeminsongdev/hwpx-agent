import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock
import native011_logical_cpu_observation as m


class Tests(unittest.TestCase):
    def test_original_constructor_array_and_close_and_default_paths_unchanged(self):
        before=m.original.PATHS;cls=m.observer_type()
        self.assertIs(cls.__init__.__code__,m.original.Observer.__init__.__code__)
        self.assertIs(cls.array,m.original.Observer.array);self.assertIs(cls.close,m.original.Observer.close)
        self.assertIs(m.original.PATHS,before);self.assertEqual(cls.__init__.__globals__['PATHS'],m.PATHS)
        self.assertEqual(len(m.PATHS),1)

    def test_only_complete_numeric_processor_instances_returned(self):
        rows=m.numeric_rows({'0':80.,'1':10.,'_total':45.},2)
        self.assertEqual(rows,dict(total_busy_percent=45.,logical_cpus=[
            dict(logical_cpu=0,busy_percent=80.),dict(logical_cpu=1,busy_percent=10.)]))
        for invalid in ({'0':10.,'_total':10.},{'0':10.,'1':5.,'private_name':1.,'_total':10.}):
            with self.assertRaisesRegex(ValueError,'EXACT_NUMERIC'):m.numeric_rows(invalid,2)

    def test_invalid_or_missing_counter_is_not_healthy_cpu(self):
        for value in (None,True,float('nan'),-1.,101.):
            with self.assertRaisesRegex(ValueError,'VALID_COMPLETE'):
                m.numeric_rows({'0':value,'_total':20.},1)

    def test_prime_and_collect_use_one_original_query_without_process_counter(self):
        cls=m.observer_type();obj=cls.__new__(cls)
        obj.closed=False;obj.query=NS(value=1);obj.handles=[1];obj.processors=1
        obj.api=NS(PdhCollectQueryData=Mock(return_value=0))
        obj.array=Mock(return_value={'0':10.,'_total':10.})
        with self.assertRaisesRegex(ValueError,'PRIMED'):obj.collect_core()
        obj.prime_core();self.assertEqual(obj.collect_core()['total_busy_percent'],10.)
        self.assertEqual(obj.api.PdhCollectQueryData.call_count,2);obj.array.assert_called_once_with(1)
        with self.assertRaisesRegex(ValueError,'ONE_LIVE'):obj.prime_core()


if __name__=='__main__':unittest.main()
