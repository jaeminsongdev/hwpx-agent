"""Immutable v2 acceptance plus the 75% warning at inventory/final guard calls.

원 oracle/bytecode/두 실제 읽기/final hash/reusable workspace/terminal diagnostic
보존. 새 보호 코드가 Native 입력이었다고 소급 주장하지 않는다.
"""
import argparse
import json
from types import FunctionType

import optimized_current_queue_acceptance_v2 as prior
import terminal_metadata_pressure_v1 as pressure

SELF = "tools/p09/optimized_current_queue_acceptance_v3.py"
TEST = "tools/p09/tests/test_optimized_current_queue_acceptance_v3.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case144-terminal-pressure-code-r428.v1.json"
QUAL_STATE = "PASS_TERMINAL_PRESSURE_CODE21_NOT_NATIVE_OR_ACCEPTANCE"
CODE_PATHS = (pressure.SELF, pressure.TEST, SELF, TEST)


def require(ok, code):
    if not ok:
        raise ValueError("TERMINAL_ACCEPTANCE_" + code)


def qualify(q, m, pin):
    require(pin.get("path") == QUAL_PATH, "EXACT_QUALIFICATION_PATH")
    m.base.scope.pins([pin], 1)
    row = m.a.read_exact(q, pin)
    m.a.fields(row, dict(state=QUAL_STATE,
                         contracts=dict(run=21, errors=0, failures=0, skipped=0),
                         accepted_count_delta=0, cleanup_confirmed=True,
                         product_or_Native_or_acceptance_executed=False), "CODE21_NOT_PRODUCT")
    pins = m.base.scope.pins(row["new_code_pins"], 4)
    require(set(pins) == set(CODE_PATHS), "EXACT_FOUR_CODE_PINS")
    for name in CODE_PATHS:
        m.a.exact(q.pin(name), pins[name], "CURRENT_TESTED_TERMINAL_CODE")
    for pin in row["preserved_acceptance_code_pins"]:
        m.a.exact(q.pin(pin["path"]), pin, "UNCHANGED_PRIOR_ACCEPTANCE_CODE")
    return row


def projection(m, raw, root_pin, old_pin, new_pin, terminal_pin, leaf):
    private, proof = pressure.runtime(m)
    execute, state = prior.projection(private, raw, root_pin, old_pin, new_pin, leaf)
    original_prepare = execute.__globals__["prepare"]
    def prepare(q):
        result = original_prepare(q)
        qualify(q, m, terminal_pin)
        return result
    execute = FunctionType(execute.__code__, {**execute.__globals__, "prepare": prepare},
                           argdefs=execute.__defaults__, closure=execute.__closure__)
    state.terminal_pressure_projection = proof
    return execute, state


def run(m, root_pin, old_pin, new_pin, terminal_pin, diagnostic_name):
    states = []
    def projected(runtime, raw, rp, op, np, leaf):
        execute, state = projection(runtime, raw, rp, op, np, terminal_pin, leaf)
        states.append(state)
        return execute, state
    def publish(path, name, row):
        row["terminal_pressure_code_qualification_pin"] = terminal_pin
        row["terminal_pressure_guard_diagnostics"] = [pressure.summary(g)
            for state in states for g in state.guards]
        row["terminal_pressure_guard_qualified_not_actual_Native"] = True
        return prior.publish(path, name, row)
    # Preserve exact v2 runner bytecode and its exclusive bounded/fsynced writer.
    runner = FunctionType(prior.run.__code__, {**prior.run.__globals__,
                          "projection": projected, "publish": publish},
                          argdefs=prior.run.__defaults__, closure=prior.run.__closure__)
    return runner(m, root_pin, old_pin, new_pin, diagnostic_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, required=True)
    for prefix in ("root", "qualification", "persistent-qualification", "terminal-qualification"):
        parser.add_argument("--" + prefix + "-bytes", type=int, required=True)
        parser.add_argument("--" + prefix + "-sha256", required=True)
    parser.add_argument("--diagnostic", required=True)
    args = parser.parse_args()
    import flat_current_queue_direct_view_runtime_v4 as m
    m.data_path(args.case)
    m.base.configure(args.case)
    def pin(path, prefix):
        return dict(path=path, bytes=getattr(args, prefix + "_bytes"),
                    sha256=getattr(args, prefix + "_sha256"))
    row, receipt = run(m, pin(m.source.root_path(m.base.CONFIG), "root"),
                       pin(prior.prior.QUAL_PATH, "qualification"),
                       pin(prior.QUAL_PATH, "persistent_qualification"),
                       pin(QUAL_PATH, "terminal_qualification"), args.diagnostic)
    print(json.dumps(dict(state=row["state"], error_code=row.get("error_code"),
                          diagnostic_pin=receipt, accepted_count_delta=row.get("accepted_count_delta"),
                          cleanup_confirmed=row.get("cleanup_confirmed"))))
    raise SystemExit(0 if row["state"].startswith("PASS_")
                     and row.get("cleanup_confirmed") is True else 2)
