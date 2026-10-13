import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import recorded_legacy146_acceptance_v1 as migration
import flat_current_queue_native_diagnostic_runtime_v6 as v6


def fixture():
    def exact(a, b, code):
        if a != b:
            raise ValueError(code)
    def fields(row, expected, code):
        for key, value in expected.items():
            if type(row.get(key)) is not type(value) or row[key] != value:
                raise ValueError(code)
    info = dict(existing_observer_instances=1, additional_PDH_queries_explicit=True,
                second_sampler_thread_or_process=False)
    row = dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
        selected_test_index=146, stop_reason=None, closing_error_code=None,
        actual_product_child_executed=True, Native_source_frame_qualified=True,
        cleanup_confirmed=True, owned_tree_empty=True, serial_CPU_attribution=info)
    failure = dict(state="FAILED_NATIVE_V6_CONNECTION_AFTER_REAL_PRODUCT_PASS_NOT_ACCEPTED",
        command_exit_code=2, error_code="NATIVE_CONTROLLER_V6_REAL_NATIVE_LOCAL_CONNECTION",
        official_accepted_count=139, accepted_count_delta=0, successful_product_replay_authorized=False,
        PC_freeze_resolved=False, root_inspection=dict(root_pin=migration.ROOT_PIN))
    reads = []
    def read(q, pin):
        reads.append(pin)
        return failure if pin == migration.FAILURE_PIN else row
    m = NS(base=NS(CONFIG=NS(index=146, before=139)), a=NS(exact=exact, fields=fields, read_exact=read))
    return m, row, failure, reads


class Tests(unittest.TestCase):
    def test_only_exact_root_pin_allowed_before_read(self):
        for key, value in (("path","other.json"),("bytes",1),("sha256","0"*64)):
            m, row, failure, reads = fixture()
            pin = dict(migration.ROOT_PIN);pin[key] = value
            with self.assertRaises(ValueError):
                migration.checked_record(None, m, pin)
            self.assertFalse(reads)

    def test_other_index_and_wrong_before_rejected(self):
        for index, before in ((147,139),(145,139),(True,139),(146,140),(146,True)):
            m, row, failure, reads = fixture()
            m.base.CONFIG = NS(index=index, before=before)
            with self.assertRaises(ValueError):
                migration.checked_record(None, m, migration.ROOT_PIN)
            self.assertFalse(reads)

    def test_original_record_returned_without_modification_or_relabel(self):
        m, row, failure, reads = fixture();before = copy.deepcopy(row)
        self.assertIs(migration.checked_record(None,m,migration.ROOT_PIN),row)
        self.assertEqual(row,before)
        self.assertEqual(reads,[migration.FAILURE_PIN,migration.ROOT_PIN])

    def test_new_backend_or_second_sampler_cannot_be_grandfathered(self):
        for key, value in (("backend","NATIVE_TOOLHELP_PROCESS_TIMES_V2"),
                           ("native_backend_connection",{}),
                           ("existing_observer_instances",2),("additional_PDH_queries_explicit",False)):
            m, row, failure, reads = fixture()
            row["serial_CPU_attribution"][key] = value
            with self.assertRaises(ValueError):
                migration.checked_record(None,m,migration.ROOT_PIN)

    def test_failed_optimizer_not_promoted_or_root_swapped(self):
        for key,value in (("command_exit_code",0),("accepted_count_delta",1),("successful_product_replay_authorized",True)):
            m,row,failure,reads=fixture();failure[key]=value
            with self.assertRaises(ValueError):
                migration.checked_record(None,m,migration.ROOT_PIN)
        m,row,failure,reads=fixture();failure["root_inspection"]=dict(root_pin=dict(migration.ROOT_PIN,bytes=1))
        with self.assertRaises(ValueError):
            migration.checked_record(None,m,migration.ROOT_PIN)

    def test_original_full_prepare_bytecode_defaults_closure_and_other_globals_unchanged(self):
        old=v6.API.prepare
        new=migration.preparation(v6)
        self.assertIs(new.__code__,old.__code__)
        self.assertIs(new.__defaults__,old.__defaults__)
        self.assertIs(new.__closure__,old.__closure__)
        self.assertEqual(set(new.__globals__),set(old.__globals__))
        for key,value in old.__globals__.items():
            if key!="source":self.assertIs(new.__globals__[key],value)
        self.assertIs(new.__globals__["source"],v6.M.API.prepare.__globals__["source"])

    def test_full_oracle_failure_not_suppressed(self):
        def fail(q,pin):
            raise ValueError("ORIGINAL_FULL_SOURCE_FAILURE")
        with patch.object(migration,"preparation",return_value=fail), \
             patch.object(migration,"checked_record",return_value={}), \
             patch.object(migration,"qualify",return_value=migration.FAILURE_PIN):
            m=migration.runtime(v6)
            with self.assertRaisesRegex(ValueError,"ORIGINAL_FULL_SOURCE_FAILURE"):
                m.API.prepare(None,migration.ROOT_PIN)

    def test_full_oracle_result_must_equal_exact_record(self):
        def different(q,pin):
            return dict(changed=True),{}, {},{}
        with patch.object(migration,"preparation",return_value=different), \
             patch.object(migration,"checked_record",return_value={}), \
             patch.object(migration,"qualify",return_value=migration.FAILURE_PIN):
            m=migration.runtime(v6)
            with self.assertRaises(ValueError):
                m.API.prepare(None,migration.ROOT_PIN)


if __name__=="__main__":
    unittest.main()

