"""Separate opt-in direct-view expectations; NOT connected to runtime134.

Never rewrite a candidate's observations or historical retained-stream oracle.
Clone only the qualified projector's globals. Preserve every original statement
except three physical duplicate expectations, the direct guard field name, and
the exact explicitly charged cost expression. Undo must recover the input AST.
The added checks are native mechanics only, not product/Gate qualification.
"""
import ast
import copy
from types import FunctionType, SimpleNamespace as NS

import held_native_read_views_v1 as views

SELF = "tools/p09/held_native_view_oracle_v1.py"
TEST = "tools/p09/tests/test_held_native_view_oracle_v1.py"
INVENTORY_REQUESTS = 167
FINAL_SAMPLE_SECONDS = .5


def require(ok, code):
    if not ok:
        raise ValueError("DIRECT_VIEW_ORACLE_" + code)


def mechanics_projection(node):
    node = copy.deepcopy(node)
    before = ast.dump(node, include_attributes=False)
    changes = []
    for call in ast.walk(node):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                and call.func.id == "fields" and len(call.args) == 3
                and isinstance(call.args[2], ast.Constant)):
            continue
        label = call.args[2].value
        if label not in ("BORROWED_STREAMS", "NATIVE_PACING"):
            continue
        require(isinstance(call.args[1], ast.Call)
                and isinstance(call.args[1].func, ast.Name)
                and call.args[1].func.id == "dict", "EXACT_EXPECTATION_DICTIONARY")
        keywords = {k.arg: k for k in call.args[1].keywords}
        mapping = ({"duplicate_handles_opened": ("2*n", "0"),
                    "duplicate_handles_closed": ("2*n", "0")}
                   if label == "BORROWED_STREAMS"
                   else {"open_reservations": ("held+2*n", "held")})
        for name, (old_text, new_text) in mapping.items():
            require(name in keywords, "ALL_PHYSICAL_EXPECTATIONS_PRESENT")
            keyword = keywords[name]
            require(ast.dump(keyword.value, include_attributes=False)
                    == ast.dump(ast.parse(old_text, mode="eval").body,
                                include_attributes=False), "EXACT_ORIGINAL_PHYSICAL_TERM")
            old = copy.deepcopy(keyword.value)
            keyword.value = ast.parse(new_text, mode="eval").body
            keyword.value._direct_before = old
            changes.append(name)
        if label == "BORROWED_STREAMS":
            name = "original_resource_guards_and_pacing_retained"
            require(name in keywords and isinstance(keywords[name].value, ast.Constant)
                    and keywords[name].value.value is True,
                    "EXACT_ORIGINAL_GUARD_EXPECTATION")
            keyword = keywords[name]
            keyword._direct_guard_before = name
            keyword.arg = "original_resource_and_byte_rate_guards_retained"
            changes.append("explicit_direct_resource_guard_field")
    costs = [n for n in ast.walk(node) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "exact"
             and len(n.args) == 3 and isinstance(n.args[2], ast.Constant)
             and n.args[2].value == "NO_HIDDEN_COST"]
    require(len(costs) == 1, "ONE_ORIGINAL_COST_EQUALITY")
    old = copy.deepcopy(costs[0].args[1])
    costs[0].args[1] = ast.parse("model['predicted_runtime_combined_seconds']",
                               mode="eval").body
    costs[0].args[1]._direct_before = old
    changes.append("exact_complete_direct_cost")
    require(sorted(changes) == sorted(["duplicate_handles_opened", "duplicate_handles_closed",
            "open_reservations", "explicit_direct_resource_guard_field",
            "exact_complete_direct_cost"]), "EXACT_FIVE_REVIEWED_CHANGES")

    class Undo(ast.NodeTransformer):
        def visit(self, item):
            if hasattr(item, "_direct_before"):
                return copy.deepcopy(item._direct_before)
            return super().visit(item)

        def visit_keyword(self, item):
            if hasattr(item, "_direct_guard_before"):
                item.arg = item._direct_guard_before
            return self.generic_visit(item)

    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False)
            == before, "ALL_OTHER_ORIGINAL_PREDICATES_RESTORED_EXACTLY")
    return node


def runtime_budget(required, requests):
    require(type(requests) is int and requests == INVENTORY_REQUESTS,
            "UNCHANGED_WHOLE_RUST_INVENTORY")
    result = views.model(required, requests)
    result.update(final_postcleanup_distinct_sample_wait_allowance_seconds=FINAL_SAMPLE_SECONDS,
                  final_postcleanup_same_owner_actual_sample_required=True)
    result["predicted_runtime_combined_seconds"] += FINAL_SAMPLE_SECONDS
    result["nominal_fits_unchanged_deadline"] = result["predicted_runtime_combined_seconds"] < 600
    require(result["nominal_fits_unchanged_deadline"], "FINAL_SAMPLE_INSIDE_ORIGINAL600")
    return result


def cost(required, rate):
    require(type(rate) is int and rate == 14, "UNCHANGED_ACQUISITION14")
    return runtime_budget(required, INVENTORY_REQUESTS)


def project_checker(qualified_projector, original_scope):
    require(type(qualified_projector) is FunctionType
            and "mechanics_projection" in qualified_projector.__globals__
            and "ORACLE_SCOPE" in qualified_projector.__globals__,
            "QUALIFIED_FULL_PROJECTOR_INTERFACE")
    scope = NS(**{**vars(original_scope), "cost": cost})
    environment = dict(qualified_projector.__globals__,
                       mechanics_projection=mechanics_projection, ORACLE_SCOPE=scope)
    result = FunctionType(qualified_projector.__code__, environment,
                          argdefs=qualified_projector.__defaults__,
                          closure=qualified_projector.__closure__)
    require(result.__code__ is qualified_projector.__code__, "FULL_PROJECTOR_CODE_UNCHANGED")
    return result


def native_mechanics(frame, required, exact, fields):
    """Additional facts only. CLOSED focused evidence does not become COMMITTED."""
    n = len(required)
    require(n > 0, "NONEMPTY_WHOLE_SCOPE")
    total = sum(pin["bytes"] for pin in required.values())
    fields(frame, dict(input_count=n, input_bytes=total), "DIRECT_SCOPE")
    h = frame["handles"]
    fields(h, dict(input_lock_handles_remaining=0, input_lock_cleanup_confirmed=True,
        handle_close_failed_attempts=0, active_reader_bindings=0, active_byte_streams=0,
        maximum_lock_seconds=600, byte_stream_identity_checks=2*n,
        separate_pathname_reopens=0), "DIRECT_ORIGINAL_HANDLE_LIFETIMES")
    held = h["input_lock_handles_opened"]
    require(type(held) is int and n <= held <= 8192, "ORIGINAL_PHYSICAL_HANDLE_CEILING")
    exact(h["input_lock_handles_closed"], held, "ALL_REAL_HELD_HANDLES_CLOSED")
    s = h["held_native_read_views"]
    exact(s, h["borrowed_byte_streams"], "BOTH_SUMMARIES_SAME_ACTUAL_OBSERVATIONS")
    fields(s, dict(duplicate_handles_opened=0, duplicate_handles_closed=0,
        duplicate_handles_remaining=0, duplicate_close_failed_attempts=0,
        CRT_descriptors_created=0, shared_offset_resets=2*n,
        active_borrow_binding=False, logical_views_opened=2*n, logical_views_closed=2*n,
        logical_views_remaining=0, logical_view_close_failed_attempts=0,
        pending_view_reservation=False, existing_pressure_checkpoints=2*n,
        direct_returned_bytes=2*total, byte_stream_pathname_reopens=0,
        original_held_handles_closed_by_borrower=False,
        original_pre_read_stream_identity_check_retained=True,
        physical_open_pacer_not_mutated=True, original_resource_and_byte_rate_guards_retained=True,
        input_scope_reduced=False, file_byte_hash_or_JSON_cache=False,
        product_or_Native_runtime_qualified=False, measured_CPU_or_freeze_improvement_claimed=False),
        "ALL_ACTUAL_DIRECT_VIEW_FACTS")
    count = s["direct_readinto_attempts"]
    require(type(count) is int and count >= 2*n, "REAL_BOUNDED_READ_ATTEMPTS")
    exact(s["direct_readinto_completed"], count, "ALL_REAL_READS_COMPLETED")
    fields(h["native_open_pacing"], dict(maximum_opens_per_second=20,
        open_reservations=held, idle_time_cannot_accumulate_multiple_open_credits=True),
        "NO_NONEXISTENT_PHYSICAL_OPEN_COST")
    return dict(input_count=n, actual_two_pass_bytes=2*total,
                physical_duplicates=0, native_mechanics_only_not_product_or_Gate=True)


def retained_evidence(row, original_candidate):
    """Explicit replacement for new backend only, AFTER full original oracle."""
    original_candidate.original.additional_observer_evidence(row)
    a = original_candidate.original.original
    required = a.scope.pins(row["source_freeze"])
    # This function itself cannot bless a focused CLOSED frame as product evidence.
    a.fields(row["source_frame"], dict(frame_state="COMMITTED", registered_live_frame=False,
        original_owned_cleanup_confirmed_before_release=True,
        original_two_actual_per_case_byte_reads_retained=True), "FULL_COMMITTED_FRAME_REQUIRED")
    native_mechanics(row["source_frame"], required, a.exact, a.fields)
    a.fields(row["complete_runtime_budget"], runtime_budget(required, INVENTORY_REQUESTS),
             "ALL_COMPLETE_COST_TERMS_WITH_FINAL_SAMPLE")
    require(row.get("synthetic_fixture_only_not_evidence", False) is False,
            "NO_SYNTHETIC_ACCEPTANCE")
    return True
