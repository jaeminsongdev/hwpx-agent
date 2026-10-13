"""Fixed complete oracle and acceptor for flat per-case DATA epochs.

Validate the same complete Native/product/owned-resource oracle, never a narrow
fixture or historical hash instead of current whole bytes. No recursively
imported per-case controllers; immutable exact next-case authority only.
"""
import argparse
import ast
import copy
import hashlib
import json
import sys
from types import SimpleNamespace as NS

import flat_current_queue_runtime as r

m=r.accepted115
a=m.a
candidate=m.candidate
SELF='tools/p09/flat_current_queue_acceptance.py'
TEST=r.TEST
PASS='PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE'


def require(ok,code):
    if not ok:raise ValueError('FLAT_ACCEPT_'+code)


def validator(raw,ctx,flat=True):
    project,proof=m.validator(raw)
    controllers=m.CONTROLLERS+((r.SELF,r.TEST,SELF,TEST) if flat else ())
    project.__globals__.update(runtime=ctx,CONTROLLERS=tuple(dict.fromkeys(controllers)),ORACLE_SCOPE=m.ORACLE_SCOPE)
    return project,dict(proof,flat_case_data_not_recursive_controller_import=True,
        explicit_runtime_index=ctx.INDEX,explicit_prior_count=ctx.BEFORE)


def validate_candidate(q,row,listing,oldbody,fresh,ctx,flat=True):
    require(type(row) is dict and row.get('synthetic_fixture_only_not_evidence',False) is False,'NO_SYNTHETIC_CANDIDATE')
    require(type(ctx.INDEX) is int and 115<=ctx.INDEX<=249 and ctx.BEFORE==ctx.INDEX-7,'EXACT_RUNTIME_CURSOR')
    require(listing['source_test_names'][ctx.INDEX-1]==ctx.CASE,'COMPILED_EXACT_CASE')
    project,proof=validator(candidate.read_source(q,candidate.ACCEPTOR_PIN),ctx,flat)
    check,old_proof=project(candidate.read_source(q,candidate.original.ORACLE_PIN),row,listing,oldbody)
    evidence=check(row,listing,oldbody,fresh,q.checkpoint)
    candidate.retained_evidence(row)
    a.fields(row['complete_runtime_budget'],dict(final_postcleanup_distinct_sample_wait_allowance_seconds=.5,
        final_postcleanup_same_owner_actual_sample_required=True),'ACTUAL_FINAL_RESOURCE_SAMPLE_COST')
    proof.update(original_validator_projection=old_proof,
        all_original_whole_Native_product_resource_and_cleanup_checks_retained=True,
        previous115_source_data_not_rebased=True)
    return evidence,proof


def prepare(q,root_pin):
    step=r.CONFIG;require(step is not None,'CONFIG_REQUIRED')
    require(type(root_pin) is dict and root_pin.get('path')==
        f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run001.v1.json','EXACT_ACTUAL_ROOT_PATH')
    a.exact(q.pin(step.path),step.pin,'UNCHANGED_STEP_DATA')
    row=a.read_exact(q,root_pin)
    require(row.get('synthetic_fixture_only_not_evidence',False) is False,'NO_SYNTHETIC_QUEUE_ACCEPTANCE')
    parent=a.read_exact(q,step.prior_queue_pin)
    state=m.PASS if step.index==116 else PASS
    a.fields(parent,dict(state=state,accepted_count_after=step.before,next_runtime_index=step.index,
        accepted_count_delta=1,resource_cleanup_confirmed=True,full249_current_qualified=False,
        signed16_current_qualified=False,P09_gate='OPEN'),'PRIOR_ACTUAL_AUTHORITY')
    a.exact(parent['runtime_candidate_pin'],step.prior_candidate_pin,'EXACT_PRIOR_CANDIDATE_PIN')
    listing=a.read_exact(q,a.scope.LIST_PIN);body=a.read_exact(q,a.BODY_PIN)
    fresh=a.packed.unpack(a.read_exact(q,a.FRESH_PIN),q.checkpoint)
    evidence,proof=validate_candidate(q,row,listing,body,fresh,r.context(step))
    a.resource_history(parent['resource_samples'])
    expected=a.scope.pins(row['source_freeze'])
    a.exact(expected.get(step.path),step.pin,'STEP_DATA_IN_REAL_NATIVE_FRAME')
    return row,listing,evidence,proof


def run_projection(raw,root_pin):
    step=r.CONFIG;require(step is not None,'CONFIG_REQUIRED')
    pin=candidate.ACCEPTOR_PIN
    require(type(raw) is bytes and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
        'EXACT_QUALIFIED113_ACCEPTOR')
    nodes=[n for n in ast.parse(raw.decode('utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='run']
    require(len(nodes)==1,'ONE_ORIGINAL_RUN')
    node=copy.deepcopy(nodes[0]);before=ast.dump(node,include_attributes=False);changes=[]
    values=dict(accepted_count_before=(106,step.before),accepted_count_after=(107,step.before+1),
        runtime_remaining_individual_cases=(142,249-step.before-1),next_runtime_index=(114,step.index+1),
        accepted_current_generation_case_count=(2,step.before+1-105),accepted=(107,step.before+1),
        remaining=(142,249-step.before-1),next_case=(114,step.index+1))
    for keyword in [n for n in ast.walk(node) if isinstance(n,ast.keyword)]:
        old=copy.deepcopy(keyword.value)
        if keyword.arg in values:
            x,y=values[keyword.arg]
            require(isinstance(keyword.value,ast.Constant) and type(keyword.value.value) is int and keyword.value.value==x,'CLOSED_QUEUE_METADATA')
            keyword.value=ast.Constant(y)
        elif keyword.arg=='accepted_test_indices':
            require(ast.dump(keyword.value,include_attributes=False)==ast.dump(ast.parse('[113]',mode='eval').body,include_attributes=False),
                'ONE_ORIGINAL_INDEX')
            keyword.value=ast.parse(repr([step.index]),mode='eval').body
        elif keyword.arg=='accepted_epoch_key':
            require(isinstance(keyword.value,ast.BinOp) and isinstance(keyword.value.right,ast.Constant)
                and keyword.value.right.value==':113','ONE_UNIQUE_EPOCH_KEY')
            keyword.value=copy.deepcopy(keyword.value);keyword.value.right.value=f':{step.index}'
        else:continue
        keyword.value._queue_before=old;changes.append(keyword.arg)
    require(len(changes)==10 and len(set(changes))==10,'TEN_CLOSED_QUEUE_METADATA_FIELDS')
    marker=ast.dump(ast.parse('guard.check(force=True)').body[0],include_attributes=False);waits=0
    class Wait(ast.NodeTransformer):
        def visit_Expr(self,n):
            nonlocal waits
            if ast.dump(n,include_attributes=False)==marker:
                extra=ast.parse('time.sleep(.5)').body[0];extra._wait_added=True;waits+=1;return [extra,n]
            return self.generic_visit(n)
    node=Wait().visit(node);require(waits==1,'ONE_ORIGINAL_FINAL_GUARD_WAIT')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_queue_before'):return copy.deepcopy(n._queue_before)
            return super().visit(n)
        def visit_Expr(self,n):
            if hasattr(n,'_wait_added'):return None
            return self.generic_visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,'ALL_ORIGINAL_ACCEPTOR_STATEMENTS_RETAINED')
    ctx=r.context(step)
    controllers=tuple(dict.fromkeys(m.CONTROLLERS+(r.SELF,r.TEST,SELF,TEST)))
    output=f'implementation/p09/evidence/p09-361-case{step.index}-current-epoch-accept001.v1.json'
    namespace=dict(candidate.original.__dict__)
    namespace.update(SELF=SELF,TEST=TEST,OUTPUT=output,ROOT_PIN=root_pin,PASS=PASS,runtime=ctx,
        CONTROLLERS=controllers,prepare=lambda q:prepare(q,root_pin))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),pin['path'],'exec'),namespace)
    return namespace['run'],dict(original_acceptor_AST_restored_exactly=True,queue_metadata_fields=10,
        original_final_force_guard_retained=True,explicit_distinct_sample_wait_seconds=.5,
        full_Native_product_oracle_not_replaced=True)


def run(root_pin):
    # Fixed small exact bootstrap; original guarded qualifier freshly verifies
    # source, step data and all imported controller/test bytes before acceptance.
    pin=candidate.ACCEPTOR_PIN
    with (a.c.ROOT/pin['path']).open('rb') as stream:raw=stream.read(pin['bytes']+1)
    execute,_=run_projection(raw,root_pin);return execute()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--case',type=int,required=True)
    parser.add_argument('--root-bytes',type=int,required=True);parser.add_argument('--root-sha256',required=True)
    args=parser.parse_args();r.configure(args.case)
    pin=dict(path=f'implementation/p09/evidence/p09-361-case{args.case}-current-runtime-run001.v1.json',
        bytes=args.root_bytes,sha256=args.root_sha256)
    a.scope.pins([pin]);raise SystemExit(run(pin))
