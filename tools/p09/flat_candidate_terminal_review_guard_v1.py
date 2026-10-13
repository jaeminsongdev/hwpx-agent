"""Read-only admission precheck, not a new queue acceptor or retry controller.

Prebody stops must be rejected BEFORE the retained original oracle projection
reads capture_diagnostics. Reuse the exact prepare bytecode/dependencies except
its stronger candidate-validation dependency. No duplicate root read/cache.
Old qualified acceptors/controllers remain untouched; product connection NOT_RUN.
"""
from types import FunctionType

import flat_current_queue_budget_acceptance_v1 as original

a = original.a
SELF = "tools/p09/flat_candidate_terminal_review_guard_v1.py"
TEST = "tools/p09/tests/test_flat_candidate_terminal_review_guard_v1.py"


def require_completed_body(row):
    a.fields(row, dict(state=original.original.r.PASS, exit_code=0, worker_created=True,
        product_body_observed=True, Native_source_frame_qualified=True,
        current_generation_runtime_candidate_qualified=True,
        cleanup_confirmed=True, owned_tree_empty=True, stop_reason=None),
        "TERMINAL_REVIEW_COMPLETED_BODY_REQUIRED")
    # This only rejects missing prebody output; does not replace its full oracle.
    a.require(type(row["capture_diagnostics"]) is dict,
              "TERMINAL_REVIEW_CAPTURE_REQUIRED")
    return True


def validate_candidate(q, row, listing, oldbody, fresh, ctx, flat=True):
    require_completed_body(row)
    return original.validate_candidate(q, row, listing, oldbody, fresh, ctx, flat)


def prepare_projection(raw):
    environment = dict(original.prepare_projection.__globals__,
                       validate_candidate=validate_candidate)
    unchanged = FunctionType(original.prepare_projection.__code__, environment,
                             argdefs=original.prepare_projection.__defaults__)
    return unchanged(raw)


def prepare_for_readonly_review(q, root_pin):
    # Exact same source/DATA/root/prior authority/original full oracle checks.
    # No run() entry or queue writer; not product/runtime/Gate qualification.
    q.pin(SELF); q.pin(TEST)
    environment = dict(original.prepare.__globals__,
                       prepare_projection=prepare_projection)
    unchanged = FunctionType(original.prepare.__code__, environment,
                             argdefs=original.prepare.__defaults__)
    return unchanged(q, root_pin)
