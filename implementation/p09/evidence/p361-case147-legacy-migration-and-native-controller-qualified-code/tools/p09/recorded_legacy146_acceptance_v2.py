"""Exact legacy146 successor restores original DATA004 postcheck dependency.

원 full prepare와 전체 legacy oracle bytecode 그대로. own_inputs는 원 V6
DATA006/source qualification을 그대로 읽고, 그 ALL pins가 실제 Native frame
안에 있는지 별도 강화 검사한다. V1 schema failure/root/optimizer failure 보존.
"""
from types import FunctionType, SimpleNamespace as NS

import recorded_legacy146_acceptance_v1 as prior

SELF = "tools/p09/recorded_legacy146_acceptance_v2.py"
TEST = "tools/p09/tests/test_recorded_legacy146_acceptance_v2.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case146-legacy-schema-code6-r452.v1.json"
QUAL_STATE = "PASS_PINNED146_ORIGINAL_DATA_SCHEMA_AND_STRONGER_NATIVE_PINS_CODE6_NOT_ACCEPTANCE"
ROOT_PIN = prior.ROOT_PIN
FAILURE_PIN = prior.FAILURE_PIN


def require(ok, code):
    if not ok:
        raise ValueError("RECORDED_LEGACY146_SCHEMA_V2_" + code)


def preparation(v6):
    original = v6.API.prepare
    env = dict(original.__globals__, source=v6.M.API.prepare.__globals__["source"],
               data_path=v6.M.data_path, validate_data=v6.M.validate_data)
    changed = {"source", "data_path", "validate_data"}
    require(set(env) == set(original.__globals__) and all(
        env[name] is value for name,value in original.__globals__.items() if name not in changed),
        "ONLY_FORMAT_AND_ORIGINAL_DATA_DEPENDENCIES")
    fn = FunctionType(original.__code__, env, argdefs=original.__defaults__, closure=original.__closure__)
    require(fn.__code__ is original.__code__ and fn.__defaults__ is original.__defaults__
            and fn.__closure__ is original.__closure__, "FULL_PREPARE_BYTECODE_UNCHANGED")
    return fn


def qualify(q, v6):
    old = prior.qualify(q, v6.M)
    pin = q.pin(QUAL_PATH)
    row = v6.M.a.read_exact(q, pin)
    v6.M.a.fields(row, dict(state=QUAL_STATE, contracts=dict(run=6,errors=0,failures=0,skipped=0),
        accepted_count_delta=0, cleanup_confirmed=True,
        Native_product_or_acceptance_executed=False), "SCHEMA_CODE6_NOT_PRODUCT")
    code = v6.M.base.scope.pins(row["new_code_pins"],2)
    require(set(code) == {SELF,TEST}, "EXACT_NEW_CODE2")
    for name,expected in code.items():
        v6.M.a.exact(q.pin(name),expected,"QUALIFIED_CURRENT_SCHEMA_CODE")
    v6.M.a.exact(row["recorded_root_pin"],ROOT_PIN,"SAME_EXACT_RECORD")
    v6.M.a.exact(row["preserved_failure_pin"],FAILURE_PIN,"OPTIMIZER_REMAINS_FAILED")
    return dict(prior_migration_qualification_pin=old,schema_qualification_pin=pin)


def native_scope(q, v6, row):
    path = v6.data_path(v6.M.base.CONFIG.index)
    pin = q.snapshots[path]
    data = v6.validate_data(v6.M.a.read_exact(q,pin),v6.M.base.CONFIG)
    expected = v6.M.base.scope.pins(row["source_freeze"])
    pins = [pin,data["qualification_pin"]]+data["controller_code_pins"]+data["native_component_pins"]
    for required in pins:
        v6.M.a.exact(expected.get(required["path"]),required,"ALL_V6_AND_COMPONENT_PINS_IN_REAL_NATIVE")
    return len(pins)


def runtime(v6):
    require(v6.SELF=="tools/p09/flat_current_queue_native_diagnostic_runtime_v6.py",
            "ONLY_RECORDED_V6_CONTROLLER")
    full = preparation(v6)
    def prepare(q,root_pin):
        recorded = prior.checked_record(q,v6.M,root_pin)
        qualification = qualify(q,v6)
        row,listing,evidence,proof = full(q,root_pin)
        v6.M.a.exact(row,recorded,"SAME_EXACT_ROOT_AFTER_FULL_ORACLE")
        count = native_scope(q,v6,row)
        return row,listing,evidence,dict(proof,recorded_legacy146_format_route=dict(
            recorded_root_pin=ROOT_PIN,preserved_failure_pin=FAILURE_PIN,
            qualification_pins=qualification,actual_backend="ORIGINAL_PDH",
            original_DATA004_postchecks_preserved=True,additional_DATA006_native_pins_checked=count,
            full_original_product_source_resource_oracle_retained=True,
            failed_native_optimizer_promoted_to_success=False,
            Native_or_product_reexecuted=False,new_code_not_retroactive_Native_input=True))
    api = NS(**{**vars(v6.API),"prepare":prepare})
    return NS(**{**vars(v6.M),"SELF":v6.SELF,"TEST":v6.TEST,"API":api,
                 "own_inputs":v6.own_inputs,"data_path":v6.data_path,
                 "validate_data":v6.validate_data,"template":v6.template,
                 "context":v6.context,"validator":v6.validator})

