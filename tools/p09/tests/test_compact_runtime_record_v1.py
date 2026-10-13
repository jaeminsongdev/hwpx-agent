import copy
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import compact_runtime_record_v1 as m
import flat_current_queue_native_diagnostic_runtime_v11 as v11

def original(file,row):
    raw_dump=json.dump
    return raw_dump(row,file,indent=2,ensure_ascii=True,allow_nan=False)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v11.M.base.CONFIG is None:v11.M.base.configure(150)
    def test_values_types_array_strings_and_all_kwargs_preserved(self):
        row=dict(integer=0,float=0.0,flag=False,none=None,text="한글 a : b\\n quote",items=[1," x ",True])
        before=copy.deepcopy(row);calls=[];state=NS(actual_dump_calls=0,writer_errors_propagated=0)
        def write(r,f,**kw):calls.append((r,kw));return json.dump(r,f,**kw)
        out=io.StringIO();m.wrap(write,state)(row,out,indent=2,ensure_ascii=False,allow_nan=False,sort_keys=False)
        self.assertEqual(row,before);parsed=json.loads(out.getvalue())
        for key,value in row.items():self.assertIs(type(parsed[key]),type(value));self.assertEqual(parsed[key],value)
        self.assertEqual(calls[0][1],dict(indent=None,separators=(",",":"),ensure_ascii=False,allow_nan=False,sort_keys=False))
        self.assertEqual(state.actual_dump_calls,1)
    def test_lazy_capture_uses_actual_outer_writer_at_execution_time(self):
        fn,state,proof=m.connect(original);before=json.dump;seen=[]
        def outer(row,file,**kw):seen.append("outer");return before(row,file,**kw)
        with patch.object(json,"dump",outer):
            out=io.StringIO();fn(out,dict(x=1))
        self.assertEqual(seen,["outer"]);self.assertIs(json.dump,before)
        self.assertEqual(state.actual_capture_count,1);self.assertEqual(out.getvalue(),'{"x":1}')
    def test_writer_errors_and_bad_profiles_not_hidden(self):
        state=NS(actual_dump_calls=0,writer_errors_propagated=0)
        def fail(*a,**kw):raise OSError("MOCK")
        with self.assertRaises(OSError):m.wrap(fail,state)({},io.StringIO(),indent=2)
        self.assertEqual(state.writer_errors_propagated,1)
        for kw in (dict(indent=4),dict(indent=True),dict(separators=(";",":"))):
            with self.assertRaises(ValueError):m.wrap(fail,state)({},io.StringIO(),**kw)
    def test_every_other_actual_engine_code_field_and_globals_retained(self):
        engine,_=v11.template();old=engine.run_owned;new,state,proof=m.connect(old)
        self.assertEqual(new.__code__.replace(co_code=old.__code__.co_code,co_names=old.__code__.co_names),old.__code__)
        self.assertIs(new.__defaults__,old.__defaults__);self.assertIs(new.__closure__,old.__closure__)
        self.assertTrue(all(new.__globals__[k] is v for k,v in old.__globals__.items()))
        self.assertFalse(proof["default_json_module_mutated"])
        self.assertEqual(state.actual_dump_calls,0)
    def test_actual_full_engine_write_path_no_Native_product_or_file_creation(self):
        engine,_=v11.template();fn,state,proof=m.connect(engine.run_owned);out=io.StringIO()
        real=fn.__globals__["c"];before=json.dump
        class FakePath:
            def __truediv__(self,name):return self
            def __str__(self):return "D:/component-no-file"
            def exists(self):return False
        fake=NS(**{**vars(real),"ROOT":FakePath()})
        def run(*a):
            row=dict(state="DEFERRED_NOT_STARTED",writer_authorized=False,samples=[],cleanup_confirmed=True,
                     owned_tree_empty=True,stop_reason="NOT_RUN",tests_passed=0)
            json.dump(row,out,indent=2);return 2
        fake.run=run
        from types import FunctionType
        tested=FunctionType(fn.__code__,dict(fn.__globals__,c=fake),argdefs=fn.__defaults__,closure=fn.__closure__)
        self.assertEqual(tested(1),2)
        value=json.loads(out.getvalue())
        self.assertFalse(value["Native_source_frame_qualified"]);self.assertFalse(value["actual_product_child_executed"])
        self.assertIsNone(value["source_frame"]);self.assertEqual(value["passed_test_names"],[])
        self.assertEqual(out.getvalue(),json.dumps(value,separators=(",",":"),ensure_ascii=True))
        self.assertEqual(state.actual_capture_count,1);self.assertEqual(state.actual_dump_calls,1)
        self.assertIs(json.dump,before)
    def test_missing_capture_and_nonfinite_values_fail(self):
        def missing():return None
        with self.assertRaises(ValueError):m.connect(missing)
        fn,_,_=m.connect(original)
        with self.assertRaises(ValueError):fn(io.StringIO(),dict(value=float("nan")))

if __name__=="__main__":unittest.main()
