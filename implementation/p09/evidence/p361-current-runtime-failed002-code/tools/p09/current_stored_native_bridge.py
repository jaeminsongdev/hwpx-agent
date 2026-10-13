"""Lean exact-definition loading for the original whole-input Native frame.

Seven immutable source pins, no legacy top-level runner/test imports. Original
Native/borrowed handle implementations are imported normally and unchanged.
Original pressure, timed/phase locks, saturation latch and held-path definitions
are compiled verbatim, with only the modeled acquisition RATE bound explicitly
within the old14/s ceiling. This module does not create handles or authorize GO.
"""
import ast
import copy
import math
import os
import re
import threading
import time
from types import SimpleNamespace as NS

import audit_evidence_io as audit
import borrowed_locked_streams as borrowed
import runtime_input_frame as frames

SELF="tools/p09/current_stored_native_bridge.py"
TEST="tools/p09/tests/test_current_stored_native_bridge.py"
SOURCES=(
    dict(path="tools/p09/near_saturation_read_backpressure.py",bytes=6072,sha256="82ad99f21ed2e3bf100e20809cea38173bb1e7749b71ab2430d661a8fd905162"),
    dict(path="tools/p09/native_open_backpressure.py",bytes=1672,sha256="6b282003cc3b837eb6d156a883e134b971efda0697615ce2cf198302ce85c641"),
    dict(path="tools/p09/lower_native_acquisition_pressure.py",bytes=3426,sha256="9f3c96656266df4a345a0927a4a066963a1e5b3a2c125f520260e0fe0e8cbaea"),
    dict(path="tools/p09/qualify_rejected_parent_connection_r2.py",bytes=22123,sha256="aa5eedf38ba1c816bb85d5b23cb584320a48fbdbdfb12d66da965302c05c4efe"),
    dict(path="tools/p09/qualify_acquisition_phase_pressure.py",bytes=17050,sha256="b9fd030f1b4d1526b5d7bd21bf095ebf906e2cce0d4cd4e11919a147fd3b2813"),
    dict(path="tools/p09/review_checkpoint_queue_stop.py",bytes=15604,sha256="2ca7510312eab46ccda26c894b84ae3900ef29688fefc25061cc1af8b2fbb797"),
    dict(path="tools/p09/resume_preserved106_queue_runtime.py",bytes=228355,sha256="499dfe358b31728f0ebb1d0bc21398bdcce7dbd77d8c424a9fff8b58c252770b"),
)
DEFINITIONS=(
    ("PressureCheckpoint",), ("PressureInputLocks",), ("InputLocks",),
    ("closed_code","TimedInputLocks"), ("InputLocks",), ("EarlySourceCheckpoint",),
    ("HeldPathSource","HeldPathGuard","read_with_held_path_guards","AcquisitionDiagnostics",
     "AcquisitionNative","OneWayNativeSaturationCheckpoint","AcquisitionInputLocks"),
)


def require(ok,code):
    if not ok:raise ValueError("CURRENT_STORED_NATIVE_"+code)


def definitions(text,names,namespace):
    """Execute selected immutable definitions only, never module statements."""
    require(type(text) is str and type(names) is tuple and names and len(set(names))==len(names),"DEFINITION_REQUEST")
    tree=ast.parse(text);selected=[]
    for name in names:
        found=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name]
        require(len(found)==1,"EXACT_ONE_DEFINITION")
        node=found[0]
        require(not node.decorator_list,"NO_DEFINITION_DECORATOR")
        for child in ast.walk(node):
            require(not isinstance(child,(ast.Import,ast.ImportFrom)),"NO_SELECTED_IMPORT")
            if isinstance(child,ast.Call) and isinstance(child.func,ast.Name):
                require(child.func.id not in ("eval","exec","__import__"),"NO_DYNAMIC_SELECTED_IMPORT")
        selected.append(node)
    scope=dict(namespace)
    exec(compile(ast.Module(body=selected,type_ignores=[]),"<immutable-native-definitions>","exec"),scope)
    return NS(**{name:scope[name] for name in names})


def load(reader,acquisition_rate,c):
    require(type(acquisition_rate) is int and 1<=acquisition_rate<=14,"ORIGINAL_ACQUISITION_CEILING")
    require(c.POLICY["sample_seconds"]==.5,"ORIGINAL_SAMPLE_INTERVAL")
    texts=[]
    for pin in SOURCES:
        text=reader.text(pin["path"])
        require(reader.snapshots[pin["path"]]==pin,"EXACT_SOURCE_PIN_BEFORE_DEFINITIONS")
        texts.append(text)
    common=dict(require=require,math=math,time=time,copy=copy,os=os,threading=threading,re=re)
    pressure=definitions(texts[0],DEFINITIONS[0],dict(common,c=c,WARNING_PERCENT=95,COOL_SAMPLES=2,MAX_PAUSE_WINDOWS=8))
    pressure.time=time
    native=definitions(texts[1],DEFINITIONS[1],dict(common,borrowed=borrowed,pressure=pressure))
    native.borrowed=borrowed
    lower=definitions(texts[2],DEFINITIONS[2],dict(common,original=native,RATE=20,ORIGINAL_CEILING=32))
    lower.original=native
    timed=definitions(texts[3],DEFINITIONS[3],dict(common,m=NS(m=NS(lower=lower)),
        LABELS=("before_acquire","after_acquire","before_parent","after_parent","before_release")))
    profile=definitions(texts[4],DEFINITIONS[4],dict(common,runtime=NS(connection=timed),lower=lower,
        RATE=acquisition_rate,UPPER=20))
    early=definitions(texts[5],DEFINITIONS[5],dict(common,m=NS(entry=NS(locks=borrowed.locks),p=NS(c=c)),
        WARNING=90,COOL=2,MAX_WINDOWS=8))
    selected=definitions(texts[6],DEFINITIONS[6],dict(common,m=NS(profile=profile),audit=audit,
        CASE111_SATURATION_POLICY_STOP="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION"))
    # 원 phase class의 역사적30% summary label만 현재 RATE/20로 정확히 표시한다.
    # 원 acquire/check/pacer/identity/close 메서드는 수정하거나 복제하지 않는다.
    class InputLocks(selected.AcquisitionInputLocks):
        def summary(self):
            row=super().summary()
            row["acquisition_phase_pressure"]["nominal_acquisition_density_reduction_percent"]=100*(1-acquisition_rate/20)
            row["lean_exact_definition_sources"]=list(SOURCES)
            row["historical_runner_top_level_imported"]=False
            return row
    return NS(InputLocks=InputLocks,EarlySourceCheckpoint=early.EarlySourceCheckpoint,
        PressureCheckpoint=pressure.PressureCheckpoint,OneWayNativeSaturationCheckpoint=selected.OneWayNativeSaturationCheckpoint,
        read_with_held_path_guards=selected.read_with_held_path_guards,HeldPathGuard=selected.HeldPathGuard,
        original_phase_base=profile.InputLocks,source_pins=list(SOURCES),selected_definitions=DEFINITIONS)
