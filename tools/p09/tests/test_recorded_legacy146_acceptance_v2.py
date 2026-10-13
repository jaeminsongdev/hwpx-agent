import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace as NS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import recorded_legacy146_acceptance_v2 as migration
import flat_current_queue_native_diagnostic_runtime_v6 as v6


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v6.M.base.CONFIG is None:v6.M.base.configure(146)

    def test_entire_original_prepare_and_only_three_dependencies(self):
        old=v6.API.prepare;new=migration.preparation(v6)
        self.assertIs(old.__code__,new.__code__)
        self.assertIs(old.__defaults__,new.__defaults__)
        self.assertIs(old.__closure__,new.__closure__)
        self.assertEqual(set(old.__globals__),set(new.__globals__))
        for key,value in old.__globals__.items():
            if key not in {"source","data_path","validate_data"}:self.assertIs(new.__globals__[key],value)
        self.assertIs(new.__globals__["own_inputs"],v6.own_inputs)

    def test_real_original_DATA004_closed_schema_keeps_inherited_postcheck_keys(self):
        new=migration.preparation(v6)
        path=new.__globals__["data_path"](146)
        row=json.loads((v6.M.c.ROOT/path).read_text(encoding="utf-8"))
        self.assertIs(new.__globals__["validate_data"](row,v6.M.base.CONFIG),row)
        self.assertIn("connection_code_pins",row)
        self.assertIn("connection_qualification_pin",row)
        self.assertEqual(path,v6.M.data_path(146))
        self.assertNotEqual(path,v6.data_path(146))

    def native_fixture(self,missing=False):
        data_path=v6.data_path(146)
        pin=dict(path=data_path,bytes=1,sha256="1"*64)
        cp=[dict(path=name,bytes=1,sha256="2"*64) for name in (v6.SELF,v6.TEST)]
        qual=dict(path=v6.QUAL_PATH,bytes=1,sha256="3"*64)
        data=dict(qualification_pin=qual,controller_code_pins=cp,native_component_pins=v6.FIXED_PINS)
        frozen=[pin,qual]+cp+v6.FIXED_PINS
        if missing:frozen.remove(cp[0])
        q=NS(snapshots={data_path:pin})
        return q,data,dict(source_freeze=frozen)

    def test_all_new_controller_and_components_still_inside_real_native(self):
        q,data,row=self.native_fixture()
        with patch.object(v6.M.a,"read_exact",return_value=data),patch.object(v6,"validate_data",return_value=data):
            self.assertEqual(migration.native_scope(q,v6,row),15)

    def test_missing_native_controller_cannot_be_hidden_by_old_data(self):
        q,data,row=self.native_fixture(True)
        with patch.object(v6.M.a,"read_exact",return_value=data),patch.object(v6,"validate_data",return_value=data):
            with self.assertRaises(ValueError):migration.native_scope(q,v6,row)

    def test_original_full_oracle_error_propagates(self):
        def failed(q,pin):raise ValueError("WHOLE_ORACLE_FAILED")
        with patch.object(migration,"preparation",return_value=failed), \
             patch.object(migration.prior,"checked_record",return_value={}), \
             patch.object(migration,"qualify",return_value={}):
            m=migration.runtime(v6)
            with self.assertRaisesRegex(ValueError,"WHOLE_ORACLE_FAILED"):m.API.prepare(None,migration.ROOT_PIN)

    def test_success_keeps_actual_legacy_backend_and_failed_optimizer(self):
        row=dict(unchanged=True)
        with patch.object(migration,"preparation",return_value=lambda q,p:(row,{}, {},{})), \
             patch.object(migration.prior,"checked_record",return_value=row), \
             patch.object(migration,"qualify",return_value={}), \
             patch.object(migration,"native_scope",return_value=15):
            result=migration.runtime(v6).API.prepare(None,migration.ROOT_PIN)
        self.assertIs(result[0],row)
        info=result[3]["recorded_legacy146_format_route"]
        self.assertEqual(info["actual_backend"],"ORIGINAL_PDH")
        self.assertFalse(info["failed_native_optimizer_promoted_to_success"])
        self.assertFalse(info["Native_or_product_reexecuted"])


if __name__=="__main__":unittest.main()

