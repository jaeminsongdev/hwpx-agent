"""Exact frozen focused driver, private held-guard reader dependency only.

No change to CODE13 producer/driver sources or accepted runtime157. The157
controller namespace supplies only its qualified Native factory/reader class.
The eight-input CLOSED proof does not execute or qualify158/product/Gate.
"""
import json
import sys
from types import FunctionType,SimpleNamespace as NS
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_physical_io_r324 as original
import held_envelope_boundary_guard_v1 as connection
import flat_current_queue_product_window_runtime_v18 as v

SELF="tools/p09/run_case158_guarded_envelope_focus_r324.py"
QUAL="implementation/p09/evidence/p09-361-case158-held-envelope-guard-code7-r627.v1.json"
a=original.launch.a
readers=[]

class Reader(a.AcceptanceReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);readers.append(self)
        self.pin(SELF)
        qual=self.json(QUAL)
        a.fields(qual,dict(state="PASS_HELD_ENVELOPE_ORIGINAL_FRAME_DECODER_GUARD_CODE7_NOT_ACTUAL_NATIVE_OR_PRODUCT",
            contracts=dict(run=7,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"GUARD_CODE7")
        for pin in qual["source_pins"]:a.exact(self.pin(pin["path"]),pin,"FRESH_BOUNDARY_CONNECTION")
        for path in (v.SELF,v.TEST):self.pin(path)
        if v.M.base.CONFIG is None:v.M.base.configure(157)
        a.exact(v.M.base.CONFIG.index,157,"HISTORICAL_FACTORY_CONTEXT_NOT158_BODY")
        a.exact(self.pin(v.M.base.CONFIG.path),v.M.base.CONFIG.pin,"FACTORY_STEP_SOURCE")

def emit(raw):
    row=json.loads(raw)
    if readers:
        q=readers[-1]
        row["additional_guard_connection_inputs"]=[q.snapshots[p] for p in
            (SELF,QUAL,connection.SELF,connection.TEST) if p in q.snapshots]
    row["frozen_CODE13_driver_code_retained"]=True
    row["private_boundary_dependency_connection_used"]=True
    print(json.dumps(row,ensure_ascii=True,allow_nan=False))

private_a=NS(**{**vars(a),"AcceptanceReader":Reader})
private_launch=NS(**{**vars(original.launch),"a":private_a})
private_physical=NS(**{**vars(original.physical),"boundary_reader_type":connection.boundary_reader_type})
driver=FunctionType(original.main.__code__,dict(original.main.__globals__,launch=private_launch,
    physical=private_physical,print=emit),argdefs=original.main.__defaults__,closure=original.main.__closure__)
a.require(driver.__code__ is original.main.__code__,"UNCHANGED_FULL_FOCUSED_DRIVER")

if __name__=="__main__":raise SystemExit(driver("focus"))
