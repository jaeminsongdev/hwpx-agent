"""Strict115 whole Native/product candidate -> distinct109 queue authority.

Preserve original113 acceptor and112 full oracle, projecting only explicit
metadata, reviewed physical duplicate accounting and complete serial costs.
The original final guard takes a real distinct sample after0.5s, never zero.
No product/Native replay, synthetic acceptance, prior-epoch rebase or Gate PASS.
"""
import ast
import copy
import hashlib
from types import SimpleNamespace as NS

import accept_case114_current_epoch as candidate
import run_case115_current_queue as runtime

a=candidate.original.original
SELF='tools/p09/accept_case115_current_epoch.py'
TEST='tools/p09/tests/test_case115_current_epoch.py'
OUTPUT='implementation/p09/evidence/p09-361-case115-current-epoch-accept001.v1.json'
ROOT_PIN=dict(path='implementation/p09/evidence/p09-361-case115-current-runtime-run001.v1.json',
    bytes=2110604,sha256='8ace299a092df4e1639b6ea9cd871a88f942f310e348533e1057ade70c12bee9')
PASS='PASS_EXACT115_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE'
CONTROLLERS=candidate.CONTROLLERS+(runtime.SELF,runtime.TEST,runtime.handoff.SELF,
    runtime.handoff.TEST,runtime.final_sample.SELF)
RUNTIME=NS(**{**vars(runtime),'attribution':runtime.stable.attribution})


def require(ok,code):
    if not ok:raise ValueError('ACCEPT115_'+code)


def cost(required,rate):
    require(rate==14,'UNCHANGED_ACQUISITION_CEILING')
    return runtime.runtime_budget(required,167)


ORACLE_SCOPE=NS(**{**vars(a.scope),'cost':cost})


def validator(raw):
    check,proof=candidate.projection(raw,'validator')
    check.__globals__.update(runtime=RUNTIME,CONTROLLERS=CONTROLLERS,ORACLE_SCOPE=ORACLE_SCOPE)
    return check,dict(proof,case115_metadata_bound=True,explicit_final_resource_wait_cost_seconds=.5,
        all_original_whole_source_product_Job_resource_cleanup_predicates_retained=True)


def prepare(q):
    require(type(ROOT_PIN) is dict,'COMPLETED_ACTUAL115_PIN_REQUIRED')
    row=a.read_exact(q,ROOT_PIN);parent=a.read_exact(q,runtime.PRIOR_ACCEPT_PIN)
    a.fields(parent,dict(state=runtime.accepted114.PASS,accepted_count_before=107,accepted_count_after=108,
        accepted_count_delta=1,next_runtime_index=115,resource_cleanup_confirmed=True,
        product_and_source_epochs_distinct=True,Native_product_single_frame_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,P09_gate='OPEN'),'PRIOR_DISTINCT108')
    listing=a.read_exact(q,a.scope.LIST_PIN);body=a.read_exact(q,a.BODY_PIN)
    fresh=a.packed.unpack(a.read_exact(q,a.FRESH_PIN),q.checkpoint)
    require(listing['source_test_names'][114]==runtime.CASE,'FULL249_EXACT_NEXT115')
    project,proof=validator(candidate.read_source(q,candidate.ACCEPTOR_PIN))
    check,old_proof=project(candidate.read_source(q,candidate.original.ORACLE_PIN),row,listing,body)
    evidence=check(row,listing,body,fresh,q.checkpoint)
    candidate.retained_evidence(row)
    a.fields(row['complete_runtime_budget'],dict(final_postcleanup_distinct_sample_wait_allowance_seconds=.5,
        final_postcleanup_same_owner_actual_sample_required=True),'REAL_FINAL_RESOURCE_SAMPLE_COST')
    a.resource_history(parent['resource_samples'])
    proof.update(original_validator_projection=old_proof,
        same_frame_Native_and_actual_product_complete=True,prior114_distinct_epoch_not_promoted_to_same_frame=True)
    return row,listing,evidence,proof


def run_projection(raw):
    pin=candidate.ACCEPTOR_PIN
    require(type(raw) is bytes and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
        'EXACT_QUALIFIED113_ACCEPTOR')
    nodes=[n for n in ast.parse(raw.decode('utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='run']
    require(len(nodes)==1,'ONE_ORIGINAL_ACCEPTOR_RUN')
    node=copy.deepcopy(nodes[0]);before=ast.dump(node,include_attributes=False);changes=[]
    values=dict(accepted_count_before=(106,108),accepted_count_after=(107,109),
        runtime_remaining_individual_cases=(142,140),next_runtime_index=(114,116),
        accepted_current_generation_case_count=(2,4),accepted=(107,109),remaining=(142,140),next_case=(114,116))
    for keyword in [n for n in ast.walk(node) if isinstance(n,ast.keyword)]:
        old=copy.deepcopy(keyword.value)
        if keyword.arg in values:
            x,y=values[keyword.arg]
            require(isinstance(keyword.value,ast.Constant) and type(keyword.value.value) is int and keyword.value.value==x,
                'CLOSED_ORIGINAL_QUEUE_METADATA')
            keyword.value=ast.Constant(y)
        elif keyword.arg=='accepted_test_indices':
            require(ast.dump(keyword.value,include_attributes=False)==ast.dump(ast.parse('[113]',mode='eval').body,include_attributes=False),
                'ONE_ORIGINAL_INDEX')
            keyword.value=ast.parse('[115]',mode='eval').body
        elif keyword.arg=='accepted_epoch_key':
            require(isinstance(keyword.value,ast.BinOp) and isinstance(keyword.value.right,ast.Constant)
                and keyword.value.right.value==':113','ONE_ORIGINAL_EPOCH_KEY')
            keyword.value=copy.deepcopy(keyword.value);keyword.value.right.value=':115'
        else:continue
        keyword.value._queue_before=old;changes.append(keyword.arg)
    require(len(changes)==10 and len(set(changes))==10,'TEN_EXACT_QUEUE_METADATA_FIELDS')
    # Prevent zero-delta K32 at qualifier closing too; original force guard and
    # every resource/deadline predicate remain. This is a modeled cadence wait,
    # not an error suppression or new CPU observer.
    marker=ast.dump(ast.parse('guard.check(force=True)').body[0],include_attributes=False);waits=0
    class Wait(ast.NodeTransformer):
        def visit_Expr(self,n):
            nonlocal waits
            if ast.dump(n,include_attributes=False)==marker:
                extra=ast.parse('time.sleep(.5)').body[0];extra._final_wait_added=True;waits+=1;return [extra,n]
            return self.generic_visit(n)
    node=Wait().visit(node);require(waits==1,'ONE_FINAL_DISTINCT_SAMPLE_WAIT')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_queue_before'):return copy.deepcopy(n._queue_before)
            return super().visit(n)
        def visit_Expr(self,n):
            if hasattr(n,'_final_wait_added'):return None
            return self.generic_visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,'ALL_ORIGINAL_ACCEPTOR_STATEMENTS_RETAINED')
    namespace=dict(candidate.original.__dict__)
    namespace.update(SELF=SELF,TEST=TEST,OUTPUT=OUTPUT,ROOT_PIN=ROOT_PIN,PASS=PASS,
        runtime=RUNTIME,CONTROLLERS=CONTROLLERS,prepare=prepare)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),pin['path'],'exec'),namespace)
    return namespace['run'],dict(original_acceptor_AST_restored_exactly=True,
        queue_metadata_projected=changes,original_final_guard_retained=True,
        qualifier_distinct_sample_wait_seconds=.5,extra_observer_or_sample_zero_fabricated=False)


def run():
    q=None
    # Exact small bootstrap only; the guarded original run freshly checks it,
    # this acceptor, its tests and imported closure before immutable success.
    pin=candidate.ACCEPTOR_PIN
    with (a.c.ROOT/pin['path']).open('rb') as stream:raw=stream.read(pin['bytes']+1)
    execute,_=run_projection(raw);return execute()


if __name__=='__main__':raise SystemExit(run())
