import ast
import copy
import json
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_pressure_full_connection_v1 as m
import native_pressure_failfast_v1 as policy
import flat_current_queue_native_diagnostic_runtime_v16 as v

ROOT=Path(__file__).resolve().parents[3]
def node():
    tree=ast.parse((ROOT/"tools/p09/accept_case112_current_epoch.py").read_text(encoding="utf-8"))
    return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="validate")
def values(n,label):
    for x in ast.walk(n):
        if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=="fields" and len(x.args)==3 and isinstance(x.args[2],ast.Constant) and x.args[2].value==label:
            return {kw.arg:kw.value for kw in x.args[1].keywords}
    raise AssertionError(label)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(156)
    def direct(self):
        native=m.native_namespace(v.NATIVE,policy,v.raw,v.M.base.scope)
        return m.direct_oracle(v.M.V3.ORACLE,native)
    def test_exact_four_ast_pressure_changes_and_original_direct_changes_retained(self):
        direct=self.direct();n=direct.mechanics_projection(node())
        self.assertEqual(values(n,"BYTE_PRESSURE")["cool_distinct_sample_windows"].value,0)
        self.assertEqual(values(n,"BYTE_PRESSURE")["maximum_pause_windows_per_entry"].value,0)
        self.assertIs(values(n,"PHASE")["clock_and_sleeper_and_checkpoint_retained"].value,False)
        self.assertIs(values(n,"FAIL_FAST")["byte_boundary_cooling_policy_changed"].value,True)
        self.assertEqual(values(n,"BORROWED_STREAMS")["duplicate_handles_opened"].value,0)
        self.assertEqual(values(n,"READS")["read_rates_by_kind"].func.id,"dict")
        self.assertEqual(values(n,"HANDLE_CLEANUP")["maximum_lock_seconds"].value,600)
    def test_missing_changed_field_rejected_not_weakened(self):
        n=node();call=next(x for x in ast.walk(n) if isinstance(x,ast.Call) and len(x.args)==3 and isinstance(x.args[2],ast.Constant) and x.args[2].value=="BYTE_PRESSURE")
        call.args[1].keywords=[x for x in call.args[1].keywords if x.arg!="maximum_pause_windows_per_entry"]
        with self.assertRaises(ValueError):self.direct().mechanics_projection(n)
    def test_historical_projector_returns_exact_original_pointer(self):
        def fn():return 1
        for index in (115,147,154,155):self.assertIs(m.projector(fn,self.direct(),index),fn)
        for index in (True,114,250):
            with self.assertRaises(ValueError):m.projector(fn,self.direct(),index)
    def test_full_projector_only_two_explicit_dependencies_changed(self):
        pin=v.M.source.prior.accepted.original.candidate.ACCEPTOR_PIN
        fn,_=v.validator((ROOT/pin["path"]).read_bytes(),v.context(v.M.base.CONFIG))
        direct=self.direct();new=m.projector(fn,direct,156)
        self.assertIs(new.__code__,fn.__code__);self.assertIs(new.__defaults__,fn.__defaults__);self.assertIs(new.__closure__,fn.__closure__)
        for key,value in fn.__globals__.items():
            if key not in ("mechanics_projection","ORACLE_SCOPE"):self.assertIs(new.__globals__[key],value)
        self.assertIs(new.__globals__["ORACLE_SCOPE"].cost,direct.cost)
        self.assertIsNot(fn.__globals__["ORACLE_SCOPE"].cost,direct.cost)
    def test_direct_cost_retained_and_budget_original_code_defaults_closure(self):
        direct=self.direct();old=v.M.V3.ORACLE
        for name in ("runtime_budget","cost","retained_evidence"):
            before=getattr(old,name);after=getattr(direct,name)
            self.assertIs(after.__code__,before.__code__);self.assertIs(after.__defaults__,before.__defaults__);self.assertIs(after.__closure__,before.__closure__)
        required={"a.exe":dict(path="a.exe",bytes=1048576,sha256="0"*64),"a.rs":dict(path="a.rs",bytes=1024,sha256="1"*64)}
        before=old.runtime_budget(required,167);after=direct.runtime_budget(required,167)
        self.assertEqual(before["predicted_runtime_combined_seconds"]-after["predicted_runtime_combined_seconds"],4)
        self.assertEqual(after["unallocated_margin_seconds"],60);self.assertEqual(after["additional_early_source_wait_allowance_seconds"],11)
        with self.assertRaises(ValueError):direct.runtime_budget(required,166)
    def test_additional_checker_only_original_outside_cooling_expectation_changes(self):
        original=v.M.source.prior.accepted.original.candidate.original.additional_observer_evidence
        pin=v.M.source.prior.accepted.original.candidate.ACCEPTOR_PIN;raw=(ROOT/pin["path"]).read_bytes()
        calls=[]
        def fields(value,expected,code):calls.append((code,expected))
        fake=FunctionType(original.__code__,dict(original.__globals__,original=NS(fields=fields)),argdefs=original.__defaults__,closure=original.__closure__)
        new=m.additional_checker(fake,raw)
        row=dict(complete_runtime_budget={},serial_CPU_attribution=dict(probes=[{}]),source_frame=dict(handles=dict(all_acquisition_checkpoint_warning_fail_fast={})))
        fake(row);before=copy.deepcopy(calls);calls.clear();new(row)
        self.assertEqual([x[0] for x in before],[x[0] for x in calls])
        self.assertEqual(before[:-1],calls[:-1]);self.assertIs(before[-1][1]["original_outside_acquisition_cooling_retained"],True)
        self.assertIs(calls[-1][1]["original_outside_acquisition_cooling_retained"],False)
        expected=dict(before[-1][1],original_outside_acquisition_cooling_retained=False);self.assertEqual(calls[-1][1],expected)
    def test_candidate_namespace_keeps_all_other_values_and_default_immutable(self):
        inner=NS(additional_observer_evidence=lambda row:1,other=object());old=NS(original=inner,other=object())
        new=m.candidate_namespace(old,"NEW")
        self.assertIs(new.other,old.other);self.assertIs(new.original.other,inner.other)
        self.assertEqual(new.original.additional_observer_evidence,"NEW");self.assertTrue(callable(inner.additional_observer_evidence))
    def test_focused_closed_actual_frame_is_rejected_as_full_runtime(self):
        focus=json.loads((ROOT/"implementation/p09/evidence/p09-361-case156-native-pressure-failfast-explicit-focused3-r564.v1.json").read_text(encoding="utf-8"))
        row=dict(selected_test_index=156,source_frame=focus["focused_frame"])
        with self.assertRaises(ValueError):m.evidence(row,v.M.a)
    def test_wrong_epoch_rejected_before_native_evidence(self):
        for index in (None,True,155,250):
            with self.assertRaises(ValueError):m.evidence(dict(selected_test_index=index),v.M.a)
    def test_native_factory_delegates_original_load_and_fresh_bindings_once(self):
        seen=[];marker=object()
        def load(q,rate,c):seen.append((q,rate,c));return marker
        old=NS(load=load,model=v.NATIVE.model,frames=object())
        reader=NS(_read=lambda path,parse=False:(next(p for p in (policy.PRESSURE_PIN,policy.EARLY_PIN,policy.ACQUISITION_PIN) if p["path"]==path),bytearray(v.raw(next(p for p in (policy.PRESSURE_PIN,policy.EARLY_PIN,policy.ACQUISITION_PIN) if p["path"]==path)))),_bind=lambda path,pin:seen.append(path))
        new=m.native_namespace(old,policy,v.raw,v.M.base.scope)
        with patch.object(policy,"connect_api",return_value="CONNECTED") as connect:
            self.assertEqual(new.load(reader,14,"ORIGINAL_C"),"CONNECTED");self.assertEqual(connect.call_count,1)
            self.assertIs(connect.call_args.args[0],marker)
        self.assertEqual(len(seen),4);self.assertEqual(seen[0],(reader,14,"ORIGINAL_C"));self.assertIs(new.frames,old.frames)
        self.assertIs(old.load,load)

if __name__=="__main__":unittest.main()
