import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import current_stored_runtime_scope as scope


class CurrentScopeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[3]
        raw=(root/scope.LIST_PIN["path"]).read_bytes()
        assert len(raw)==scope.LIST_PIN["bytes"] and hashlib.sha256(raw).hexdigest()==scope.LIST_PIN["sha256"]
        cls.listing=json.loads(raw)
        cls.current=scope.listing_inputs(cls.listing)
        raw=(root/"implementation/p09/evidence/locked-r07/cases/p340-failure-111-run083.json").read_bytes()
        assert len(raw)==565807 and hashlib.sha256(raw).hexdigest()=="b8495d04c9444875cd500d2941c5b055fab1bab630325cbefb327f9f79ec1e72"
        cls.original=json.loads(raw)["source_freeze"]
        cls.required=scope.compose(cls.original,list(cls.current.values()))
    def test_full_lossless_projection_and_current_epoch_not_rebase(self):
        self.assertEqual(len(self.required),1686)
        self.assertEqual(self.required[scope.EXE_PIN["path"]],scope.EXE_PIN)
        for old,new in zip(scope.FROZEN,scope.ARCHIVES):
            self.assertEqual(self.required[new["path"]],new)
        self.assertNotEqual(self.required[scope.FROZEN[0]["path"]],scope.FROZEN[0])
        for name in scope.FIXTURES:self.assertIn(name,self.required)
    def test_unknown_overlap_conflict_fails_instead_of_silent_overlay(self):
        rows=copy.deepcopy(list(self.current.values()))
        old={p["path"]:p for p in self.original}
        changed=next(p for p in rows if p["path"] in old and p["path"]!=scope.FROZEN[0]["path"])
        changed["sha256"]="a"*64
        with self.assertRaisesRegex(ValueError,"CONFLICT_NOT_SILENT_REBASE"):
            scope.compose(self.original,rows)
    def test_original_preimage_missing_duplicate_or_fixture_omission_fails(self):
        for mutated in (self.original[:-1],self.original[:-1]+[self.original[0]]):
            with self.subTest(),self.assertRaises(ValueError):scope.compose(mutated,list(self.current.values()))
        mutated=copy.deepcopy(self.original)
        next(p for p in mutated if p["path"]==scope.FROZEN[0]["path"])["bytes"]+=1
        with self.assertRaises(ValueError):scope.compose(mutated,list(self.current.values()))
        mutated=[dict(p,path="fixtures/not-the-required-fixture.hwpx") if p["path"]==scope.FIXTURES[0] else p for p in self.original]
        with self.assertRaisesRegex(ValueError,"FIXTURES_RETAINED"):scope.compose(mutated,list(self.current.values()))
    def test_no_partial_listing_or_test_runtime_promotion(self):
        for change in (dict(runtime_tests_executed=True),dict(Native_source_frame_qualified=True),
            dict(actual_EXE_list_executed=None),dict(cleanup_confirmed=False),dict(next_case=True),
            dict(accepted_count_delta=1),dict(state="FAILED_NOT_ACCEPTED")):
            row=copy.deepcopy(self.listing);row.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):scope.listing_inputs(row)
        row=copy.deepcopy(self.listing);row["input_phase_observations"][1]["completed_input_pins"].pop()
        with self.assertRaises(ValueError):scope.listing_inputs(row)
    def test_exact_case112_name_not_arbitrary_filter(self):
        row=copy.deepcopy(self.listing);row["source_test_names"][111]+="_different"
        with self.assertRaises(ValueError):scope.listing_inputs(row)
    def test_serial_borrower_cost_prevents_old9_rate_timeout_attempt(self):
        old=scope.cost(self.required,9);new=scope.select_cost(self.required)
        self.assertFalse(old["nominal_fits_unchanged_deadline"])
        self.assertAlmostEqual(old["predicted_combined_seconds"],614.7903638839722)
        self.assertEqual(new["selected_acquisition_rate_per_second"],10)
        self.assertAlmostEqual(new["predicted_combined_seconds"],592.4903638839722)
        self.assertEqual(new["two_actual_byte_pass_native_reservations"],3372)
        self.assertEqual(new["unchanged_lock_deadline_seconds"],600)
        self.assertFalse(new["GO_authorized"]);self.assertFalse(new["queue_advance_authorized"])
    def test_no_hidden_stacked_reader_open_cost(self):
        with self.assertRaisesRegex(ValueError,"NO_SAFE_ORIGINAL_BUDGET"):
            scope.select_cost(self.required,extra_byte_open_reservations=2*len(self.required))
    def test_added_controller_receipts_require_rebudget_and_pin_conflict_check(self):
        expanded=scope.extend(self.required,{scope.LIST_PIN["path"]:scope.LIST_PIN})
        self.assertEqual(len(expanded),1687)
        self.assertGreater(scope.select_cost(expanded)["predicted_combined_seconds"],
                           scope.select_cost(self.required)["predicted_combined_seconds"])
        row=dict(scope.EXE_PIN,sha256="a"*64)
        with self.assertRaises(ValueError):scope.extend(self.required,{row["path"]:row})
        with self.assertRaisesRegex(ValueError,"MAPPING_KEY_PIN_BINDING"):
            scope.extend(self.required,{"unrelated-key":scope.LIST_PIN})
    def test_scope_path_bool_size_and_duplicate_rejection(self):
        for row in (dict(scope.EXE_PIN,path="../outside.exe"),dict(scope.EXE_PIN,bytes=True),
            dict(scope.EXE_PIN,path="D:/outside.exe"),dict(scope.EXE_PIN,sha256="bad")):
            with self.subTest(row=row),self.assertRaises(ValueError):scope.pins([row])
        with self.assertRaises(ValueError):scope.pins([scope.EXE_PIN,scope.EXE_PIN])
    def test_original_limits_not_overridden(self):
        for rate in (True,0,15,"10"):
            with self.subTest(rate=rate),self.assertRaises(ValueError):scope.cost(self.required,rate)
        for extra in (True,-1,"0"):
            with self.subTest(extra=extra),self.assertRaises(ValueError):scope.cost(self.required,10,extra_byte_open_reservations=extra)


if __name__=="__main__":unittest.main()
