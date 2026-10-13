"""Exact one parent-pin selector for the already completed lean130 root.

No root mutation, ordinary runtime PASS alias, body/Native replay or scope cut.
Original acceptor/Native/product/resource oracle remains; parent uses explicit
preserved_failed_product_root_pin. New verifier code qualifies independently.
"""
import argparse
import json
import sys
from types import FunctionType
from types import SimpleNamespace as NS

import flat_preserved129_lean_connection_v2 as lean

source, base, a, c = lean.source, lean.base, lean.a, lean.c
SELF = "tools/p09/accept_flat_lean130_compound_parent_v1.py"
TEST = "tools/p09/tests/test_accept_flat_lean130_compound_parent_v1.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case130-compound-parent-selector-code-r330.v1.json"
ROOT_PIN = dict(path="implementation/p09/evidence/p09-361-case130-current-runtime-run001.v1.json",
    bytes=2417619, sha256="4596a1972a5f5e0cfa1160d9672ce3d01c6feaef7e62cf83d800317eef351a26")


def require(ok, code):
    if not ok: raise ValueError("LEAN130_PARENT_" + code)


def projection(raw, original):
    require(base.CONFIG is not None and base.CONFIG.index == 130, "ONLY_COMPOUND_PARENT130")
    fn = original(raw)
    code = fn.__code__
    old, new = "runtime_candidate_pin", "preserved_failed_product_root_pin"
    require(sum(type(x) is str and x == old for x in code.co_consts) == 1, "ONE_EXPECTED_PARENT_SELECTOR")
    constants = tuple(new if type(x) is str and x == old else x for x in code.co_consts)
    fixed = code.replace(co_consts=constants)
    require(fixed.replace(co_consts=code.co_consts) == code, "ALL_ORIGINAL_PREPARE_CODE_RETAINED")
    return FunctionType(fixed, dict(fn.__globals__), argdefs=fn.__defaults__)


def qualify(q, pin):
    require(pin["path"] == QUAL_PATH, "EXACT_QUALIFICATION_PATH")
    row = a.read_exact(q, pin)
    a.fields(row, dict(state="PASS_ACTUAL130_FULL_PREPARE_AND_COMPOUND_PARENT_SELECTOR_NOT_QUEUE",
        accepted_count_after=123, accepted_count_delta=0, cleanup_confirmed=True,
        actual_original_full_native_product_oracle_checked=True,
        body_or_Native_replayed=False), "REAL_QUALIFIER_NOT_ACCEPTANCE")
    a.exact(row["contracts"], dict(run=13, errors=0, failures=0, skipped=0), "EXACT_SELECTOR_SCOPE13")
    require(set(base.scope.pins(row["new_code_pins"],2)) == {SELF,TEST}, "ALL_NEW_SELECTOR_CODE")
    for p in row["new_code_pins"]: a.exact(q.pin(p["path"]),p,"CURRENT_TESTED_SELECTOR_CODE")


def inherited_scope(api, q):
    """Only exact independently committed predecessor pins, never root observations."""
    parent = a.read_exact(q, base.CONFIG.prior_queue_pin)
    fresh = api.parent_header(parent, base.CONFIG)
    previous = a.read_exact(q, api.contract.SOURCE_PIN)
    return base.scope.extend(base.scope.pins(previous["required_source_pins"]), fresh)


def scoped_validator(original, inherited):
    # Both the closed dimension derivation and original full oracle use the
    # identical stronger composition. No pin/count is taken from actual130.
    required = base.scope.pins(list(inherited.values()))
    def validator(raw, ctx, flat=True):
        project, proof = original(raw, ctx, flat)
        old_scope = project.__globals__["ORACLE_SCOPE"]
        old_original = project.__globals__["original"]
        def compose(body, current):
            return base.scope.extend(old_scope.compose(body, current), required)
        scoped = NS(**{**vars(old_scope), "compose": compose})
        project.__globals__.update(ORACLE_SCOPE=scoped,
            original=NS(**{**vars(old_original), "scope": scoped}))
        return project, dict(proof, complete_independent_compound_predecessor_scope_added=True,
            all_original_oracle_statements_and_cost_guards_retained=True,
            expected_pins_not_copied_from_actual130=True, inherited_pin_count=len(required))
    return validator


def prepare(q, pin):
    a.exact(pin, ROOT_PIN, "ACTUAL_COMPLETED130_ONLY")
    lean.own_inputs(q)
    api, _ = lean.namespace(q)
    original_validator = FunctionType(api.validator.__code__, dict(api.validator.__globals__),
        argdefs=api.validator.__defaults__)
    original_binding = FunctionType(api.binding.__code__, dict(api.binding.__globals__),
        argdefs=api.binding.__defaults__)
    bound = {}
    def binding(reader):
        # Execute the complete original body/source/observer binding exactly once
        # in its original place. Capture its independently validated pin result,
        # not receipt bytes/JSON, rather than rereading both large predecessors
        # before the same original binding reads them again.
        require(not bound, "ONE_COMPLETE_ORIGINAL_PREDECESSOR_BINDING")
        inherited, rust = original_binding(reader)
        bound["inherited"] = inherited
        api.validate_candidate.__globals__["validator"] = scoped_validator(original_validator, inherited)
        return inherited, rust
    api.prepare.__globals__["binding"] = binding
    original = api.prepare_projection
    api.prepare.__globals__["prepare_projection"] = lambda raw: projection(raw, original)
    row, listing, evidence, proof = api.prepare(q, pin)
    expected = base.scope.pins(row["source_freeze"])
    for name in (lean.SELF, lean.TEST, lean.DATA_PATH):
        a.exact(expected.get(name), q.snapshots[name], "EXECUTED_LEAN_CODE_INSIDE_NATIVE_FRAME")
    return row,listing,evidence,dict(proof, one_compound_parent_pin_selector_bound=True,
        original_all_Native_product_Job_resource_and_cleanup_checks_retained=True,
        actual_prior_authority_document_not_rewritten=True,
        independently_bound_compound_predecessor_input_count=len(bound["inherited"]),
        original_complete_predecessor_binding_executed_once=True,
        duplicate_new_predecessor_receipt_reads_removed=True,
        original_binding_bytecode_unchanged=True,
        expected_compound_scope_not_derived_from_actual130=True)


def accept(code_pin):
    require(base.CONFIG is not None and base.CONFIG.index == 130, "ONLY_CASE130_ACCEPTANCE")
    def checked(q,pin):
        # Native preparation is an independent frame. New verifier qualification
        # is checked afterwards, before any authority publication or final hashes.
        # Never pretend new verifier files were in the already completed Native.
        result = prepare(q,pin)
        qualify(q,code_pin)
        return result
    # Full runtime context/controllers are the ACTUAL lean130 executed code.
    # New acceptor code is independently qualified/fresh, never retroactively
    # claimed inside the previous Native frame.
    files=(lean.SELF,lean.TEST)+tuple(p["path"] for p in lean.SOURCES)
    env=dict(source.accept.__globals__,SELF=SELF,TEST=TEST,
        CONTROLLERS=tuple(dict.fromkeys(source.CONTROLLERS+files)),
        context=lean.context,prepare=checked)
    return FunctionType(source.accept.__code__,env,argdefs=source.accept.__defaults__)(ROOT_PIN)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--qualification-bytes",type=int,required=True)
    parser.add_argument("--qualification-sha256",required=True)
    args=parser.parse_args();base.configure(130)
    pin=dict(path=QUAL_PATH,bytes=args.qualification_bytes,sha256=args.qualification_sha256)
    base.scope.pins([pin],1);raise SystemExit(accept(pin))
