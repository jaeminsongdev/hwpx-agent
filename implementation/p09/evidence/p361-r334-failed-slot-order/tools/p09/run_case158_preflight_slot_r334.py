"""Reuse qualified V22; explicit fresh output slot, full original preflight.

No product CLI or retry loop. The output-slot code and its qualification are
fresh metadata witnesses; they are not retroactively claimed as Native inputs.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
from types import FunctionType
sys.path.insert(0,str(Path(__file__).resolve().parent))
_k=ctypes.WinDLL("kernel32",use_last_error=True)
_k.GetCurrentProcess.restype=ctypes.c_void_p
_k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
_k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
_p=_k.GetCurrentProcess()
if not (_k.SetPriorityClass(_p,0x4000) and _k.SetProcessAffinityMask(_p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
import flat_current_queue_envelope_runtime_v22 as m

SELF="tools/p09/run_case158_preflight_slot_r334.py"
TEST="tools/p09/tests/test_case158_preflight_slot_r334.py"
QUAL="implementation/p09/evidence/p09-361-case158-reusable-preflight-slot-code14-r685.v1.json"
QUAL_STATE="PASS_REUSABLE158_FULL_PREFLIGHT_OUTPUT_SLOT_CODE14_NOT_GO_OR_PRODUCT"
SLOT_PIN=dict(path="tools/p09/preflight_output_slot_v1.py",bytes=2477,
    sha256="51b2bf42fdba41b7704facc494ed89bc84eeabee1552635ea1ff4c2207e31238")
bundle,namespace_proof=m.namespace_bundle.load(m.c.ROOT,[SLOT_PIN],{})
slots=bundle.preflight_output_slot_v1


def admission(q):
    # 실패 자격을 먼저 거부하고, 정상 입력 전체는 원 admission에 그대로 넘긴다.
    code=q.json(QUAL)
    m.a.fields(code,dict(state=QUAL_STATE,contracts=dict(run=14,errors=0,failures=0,skipped=0),
        accepted_count_delta=0,cleanup_confirmed=True,actual_product_or_Native_executed=False),
        "NEW_OUTPUT_SLOT_COMPONENT_NOT_PRODUCT")
    expected={SELF,TEST,slots.SELF,slots.TEST}
    pins=m.base.scope.pins(code["new_code_pins"],4)
    m.a.require(set(pins)==expected,"ALL_CURRENT_OUTPUT_SLOT_CODE4")
    for name in sorted(pins):m.a.exact(q.pin(name),pins[name],"CURRENT_QUALIFIED_SLOT_BYTES")
    m.a.exact(pins[slots.SELF],SLOT_PIN,"BOOTSTRAP_AND_GUARDED_SLOT_SOURCE_SAME")
    for pin in code["source_pins"]:m.a.exact(q.pin(pin["path"]),pin,"PRESERVED_QUALIFIED_DEPENDENCIES")
    return m.own_inputs(q)


def projection(raw,leaf,sequence):
    original=m.preflight_projection(raw,leaf)
    selected,proof=slots.project(original,sequence)
    # 두 원 admission 호출을 같은 추가 증거 경계에 연결한다. 본문은 바꾸지 않는다.
    selected=FunctionType(selected.__code__,dict(selected.__globals__,
        own_inputs=admission,connection_data=admission),argdefs=selected.__defaults__,closure=selected.__closure__)
    selected.__kwdefaults__=original.__kwdefaults__
    return selected,proof


def run(sequence):
    m.base.configure(158);m.only158()
    slots.ensure_fresh(m.c.ROOT,sequence)
    def projected(raw,leaf):return projection(raw,leaf,sequence)[0]
    # Original full preflight driver and original exclusive writer remain.
    execute=m.prior.LINK.clone(m.prior.preflight,preflight_projection=projected)
    return execute()


if __name__=="__main__":
    try:
        ap=argparse.ArgumentParser();ap.add_argument("--sequence",type=int,required=True)
        args=ap.parse_args();raise SystemExit(run(args.sequence))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_SLOT_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code,
            actual_product_or_Native_executed=False,accepted_count_delta=0)))
        raise SystemExit(2) from None
