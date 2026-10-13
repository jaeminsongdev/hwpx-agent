"""Distinct reviewed metadata root, same complete fixed Native/product oracle.

Only the authorized root path metadata changes in the immutable prepare AST.
The original complete validator/acceptor code is retained with added controller
pins and metadata binding checks. No fixture/root001 acceptance or queue replay.
"""
import argparse
import ast
import copy
import json
import sys
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_acceptance as original
import flat_current_queue_metadata_runtime as runtime

a = original.a
SELF = 'tools/p09/flat_current_queue_metadata_acceptance.py'
TEST = runtime.TEST
CONTROLLERS = (runtime.SELF, runtime.TEST, SELF, 'tools/p09/metadata_pressure_failfast.py')


def require(ok, code):
    if not ok:
        raise ValueError('METADATA_ACCEPT_' + code)


def root_path(step):
    run = 2 if step.index == 120 else 1
    return f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run{run:03}.v1.json'


def validator(raw, ctx, flat=True):
    project, proof = original.validator(raw, ctx, flat)
    project.__globals__['CONTROLLERS'] = tuple(dict.fromkeys(
        project.__globals__['CONTROLLERS'] + CONTROLLERS))
    return project, dict(proof, reviewed_metadata_controller_pins_added=True,
                         original_full_oracle_not_replaced=True)


def validate_candidate(q, row, listing, oldbody, fresh, ctx, flat=True):
    # Same function code with only the stronger validator dependency substituted.
    env = dict(original.validate_candidate.__globals__)
    env['validator'] = validator
    unchanged = FunctionType(original.validate_candidate.__code__, env,
                             argdefs=original.validate_candidate.__defaults__)
    evidence, proof = unchanged(q, row, listing, oldbody, fresh, ctx, flat)
    scope = row['bootstrap_metadata']['early_pressure']['metadata_failfast_connection']
    a.fields(scope, dict(warning_CPU_percent=75, warning_stops=0, latched=False,
                         active=False, original_checkpoint_restored=True,
                         original_hard_guard_first=True, added_sampler_or_native_query=False,
                         added_cooling_waits=0, automatic_retry_or_resume=False,
                         cleanup_guarded=False, complete_source_reads_or_deadlines_weakened=False),
             'REAL_RESTORED_METADATA_SCOPE')
    require(type(scope['checks']) is int and scope['checks'] > 0, 'ACTUAL_CHECKPOINTS')
    proof['metadata_binding_actual_restored_checked'] = True
    return evidence, proof


def prepare_projection(raw):
    tree = ast.parse(raw.decode('utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'prepare']
    require(len(nodes) == 1, 'ONE_FROZEN_PREPARE')
    node = copy.deepcopy(nodes[0])
    before = ast.dump(node, include_attributes=False)
    changes = 0
    class Project(ast.NodeTransformer):
        def visit_JoinedStr(self, n):
            nonlocal changes
            n = self.generic_visit(n)
            if any(isinstance(x, ast.Constant) and x.value == '-current-runtime-run001.v1.json'
                   for x in n.values):
                changes += 1
                new = ast.parse('root_path(step)', mode='eval').body
                new._original_root = copy.deepcopy(n)
                return new
            return n
    node = Project().visit(node)
    require(changes == 1, 'ONE_AUTHORIZED_ROOT_METADATA_CHANGE')
    class Undo(ast.NodeTransformer):
        def visit(self, n):
            if hasattr(n, '_original_root'):
                return copy.deepcopy(n._original_root)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == before,
            'ALL_FROZEN_PREPARE_STATEMENTS_RETAINED')
    env = dict(original.__dict__)
    env.update(root_path=root_path, validate_candidate=validate_candidate,
               r=NS(**{**vars(original.r), 'context': runtime.context}))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 original.SELF, 'exec'), env)
    return env['prepare']


def prepare(q, root_pin):
    data = runtime.reviewed_inputs(q, 2 if original.r.CONFIG.index == 120 else 1)
    source = q.text(original.SELF).encode('utf-8')
    # Compare original raw bytes using its preserved qualification, not an AST
    # alone. q.text newline conversion is irrelevant only after exact q.pin.
    qualification = a.read_exact(q, runtime.QUALIFIED)
    pins = {p['path']: p for p in qualification['frozen_core_pins']}
    a.exact(q.snapshots[original.SELF], pins[original.SELF], 'FROZEN_ACCEPTOR_BYTES')
    row, listing, evidence, proof = prepare_projection(source)(q, root_pin)
    expected = original.r.scope.pins(row['source_freeze'])
    for pin in data['connection_code_pins']:
        a.exact(expected[pin['path']], pin, 'CONNECTION_CODE_INSIDE_WHOLE_NATIVE_FRAME')
    a.exact(expected[runtime.data_path(original.r.CONFIG.index)],
            q.snapshots[runtime.data_path(original.r.CONFIG.index)], 'CONNECTION_DATA_INSIDE_FRAME')
    return row, listing, evidence, proof


def run(root_pin):
    require(root_pin.get('path') == root_path(original.r.CONFIG), 'EXACT_REVIEWED_ROOT')
    pin = original.candidate.ACCEPTOR_PIN
    with (a.c.ROOT / pin['path']).open('rb') as stream:
        raw = stream.read(pin['bytes'] + 1)
    execute, _ = original.run_projection(raw, root_pin)
    execute.__globals__.update(SELF=SELF, TEST=TEST, runtime=runtime.context(original.r.CONFIG),
        CONTROLLERS=tuple(dict.fromkeys(execute.__globals__['CONTROLLERS'] + CONTROLLERS)),
        prepare=lambda q: prepare(q, root_pin))
    return execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', type=int, required=True)
    parser.add_argument('--root-bytes', type=int, required=True)
    parser.add_argument('--root-sha256', required=True)
    args = parser.parse_args()
    original.r.configure(args.case)
    root = dict(path=root_path(original.r.CONFIG), bytes=args.root_bytes, sha256=args.root_sha256)
    original.r.scope.pins([root])
    raise SystemExit(run(root))
