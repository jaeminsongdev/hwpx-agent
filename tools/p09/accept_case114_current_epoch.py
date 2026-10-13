"""Distinct114 acceptance without Native/product replay.

Exact qualified113 acceptor and112 validator are retained. Only metadata/counts
and the three EXPECTED physical-duplicate counters are projected. New retained
mode checks prove two actual reads/fresh identities/lease returns/all cleanup.
Neither actual observations nor old failed receipts are rewritten as success.
"""
import ast
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace as NS

import accept_current_queue_epoch as original
import run_case114_current_queue as runtime

SELF='tools/p09/accept_case114_current_epoch.py'
TEST='tools/p09/tests/test_case114_current_epoch.py'
OUTPUT='implementation/p09/evidence/p09-361-case114-current-epoch-accept001.v1.json'
ROOT_PIN=None
PASS='PASS_EXACT114_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE'
ACCEPTOR_PIN=dict(path=original.SELF,bytes=12698,
    sha256='a4e35c9fadaa8c5c8c6c065a12285aed7411a2239da4f77e700d1851eeaf951a')
CONTROLLERS=original.CONTROLLERS+(runtime.SELF,runtime.TEST,runtime.native.SELF,runtime.native.TEST)
RUNTIME=NS(**{**vars(runtime),'attribution':runtime.stable.attribution})


def require(ok,code):
    if not ok:raise ValueError('ACCEPT114_'+code)


def mechanics_projection(node):
    node=copy.deepcopy(node);before=ast.dump(node,include_attributes=False);changes=[]
    for call in ast.walk(node):
        if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!='fields' or len(call.args)!=3:continue
        label=call.args[2]
        if not isinstance(label,ast.Constant) or label.value not in ('BORROWED_STREAMS','NATIVE_PACING'):continue
        keywords={k.arg:k for k in call.args[1].keywords}
        mapping={'duplicate_handles_opened':('2*n','n'),'duplicate_handles_closed':('2*n','n')} if label.value=='BORROWED_STREAMS' else {'open_reservations':('held+2*n','held+n')}
        for name,(before_text,after_text) in mapping.items():
            k=keywords[name]
            require(ast.dump(k.value,include_attributes=False)==ast.dump(ast.parse(before_text,mode='eval').body,include_attributes=False),
                'CLOSED_ORIGINAL_EXPECTED_DUPLICATE_COUNTER')
            old=copy.deepcopy(k.value);k.value=ast.parse(after_text,mode='eval').body;k.value._retained_before=old
            changes.append(name)
    require(sorted(changes)==['duplicate_handles_closed','duplicate_handles_opened','open_reservations'],'EXACT_THREE_PHYSICAL_EXPECTATIONS')
    # Match the separately pinned runtime's EXACT arithmetic construction, not
    # a reassociated float sum or a widened tolerance. The derived model binds
    # all margins, byte costs and the explicit2.05s PDH allowance as well.
    costs=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
        and n.func.id=='exact' and len(n.args)==3 and isinstance(n.args[2],ast.Constant)
        and n.args[2].value=='NO_HIDDEN_COST']
    require(len(costs)==1,'ONE_ORIGINAL_COST_EQUALITY')
    old=copy.deepcopy(costs[0].args[1])
    costs[0].args[1]=ast.parse("model['predicted_runtime_combined_seconds']",mode='eval').body
    costs[0].args[1]._retained_before=old
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_retained_before'):return copy.deepcopy(n._retained_before)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,'ALL_NONPHYSICAL_ORACLE_PREDICATES_RETAINED')
    return node


def retained_cost(required,rate):
    require(rate==14,'UNCHANGED_ACQUISITION_CEILING')
    return runtime.native.model(required,167)


ORACLE_SCOPE=NS(**{**vars(original.original.scope),'cost':retained_cost})


def projection(raw,name):
    require(type(raw) is bytes and len(raw)==ACCEPTOR_PIN['bytes']
        and hashlib.sha256(raw).hexdigest()==ACCEPTOR_PIN['sha256'],'EXACT_QUALIFIED113_ACCEPTOR')
    tree=ast.parse(raw.decode('utf-8'));found=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
    require(len(found)==1 and name in ('validator','run'),'ONE_ALLOWED_ORIGINAL_DEFINITION')
    node=copy.deepcopy(found[0]);before=ast.dump(node,include_attributes=False);changes=[]
    if name=='validator':
        text='namespace=dict(original.__dict__)'
        target=ast.dump(ast.parse(text).body[0],include_attributes=False)
        at=[i for i,n in enumerate(node.body) if ast.dump(n,include_attributes=False)==target]
        require(len(at)==1,'ONE_ORIGINAL_VALIDATOR_NAMESPACE')
        extra=ast.parse('node=mechanics_projection(node)').body[0];extra._additional_statement=True
        node.body.insert(at[0],extra)
        at=[i for i,n in enumerate(node.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
            and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name)
            and n.value.func.value.id=='namespace' and n.value.func.attr=='update']
        require(len(at)==1,'ONE_ORIGINAL_CODE_PINS_EXTENSION')
        extra=ast.parse("namespace['scope']=ORACLE_SCOPE").body[0];extra._additional_statement=True
        node.body.insert(at[0]+1,extra)
        changes=['physical_expected_counters','retained_physical_cost_model']
    else:
        mapping=dict(accepted_count_before=(106,107),accepted_count_after=(107,108),
            runtime_remaining_individual_cases=(142,141),next_runtime_index=(114,115),
            accepted_current_generation_case_count=(2,3),accepted=(107,108),remaining=(142,141),next_case=(114,115))
        for k in [n for n in ast.walk(node) if isinstance(n,ast.keyword)]:
            old=copy.deepcopy(k.value)
            if k.arg in mapping:
                x,y=mapping[k.arg];require(type(k.value) is ast.Constant and type(k.value.value) is int and k.value.value==x,'CLOSED_QUEUE_METADATA')
                k.value=ast.Constant(y)
            elif k.arg=='accepted_test_indices':
                require(ast.dump(k.value,include_attributes=False)==ast.dump(ast.parse('[113]',mode='eval').body,include_attributes=False),'ONE_ORIGINAL_CASE_INDEX')
                k.value=ast.parse('[114]',mode='eval').body
            elif k.arg=='accepted_epoch_key':
                require(isinstance(k.value,ast.BinOp) and isinstance(k.value.right,ast.Constant) and k.value.right.value==':113','ONE_UNIQUE_EPOCH_KEY')
                k.value=copy.deepcopy(k.value);k.value.right.value=':114'
            else:continue
            k.value._original_metadata=old;changes.append(k.arg)
        require(len(changes)==10 and len(set(changes))==10,'TEN_CLOSED_QUEUE_METADATA_FIELDS')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_original_metadata'):return copy.deepcopy(n._original_metadata)
            return super().visit(n)
        def visit_FunctionDef(self,n):
            n.body=[x for x in n.body if not hasattr(x,'_additional_statement')]
            return self.generic_visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,'ALL_QUALIFIED_ACCEPTOR_STATEMENTS_RETAINED')
    namespace=dict(original.__dict__)
    namespace.update(SELF=SELF,TEST=TEST,OUTPUT=OUTPUT,ROOT_PIN=ROOT_PIN,PASS=PASS,
        runtime=RUNTIME,CONTROLLERS=CONTROLLERS,mechanics_projection=mechanics_projection,
        ORACLE_SCOPE=ORACLE_SCOPE,prepare=prepare)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),ACCEPTOR_PIN['path'],'exec'),namespace)
    return namespace[name],dict(qualified113_acceptor_AST_restored_exactly=True,
        changed_metadata_or_new_explicit_mechanics=changes,actual_receipt_observations_modified=False,
        expected_duplicate_counter_changes=3 if name=='validator' else 0)


def read_source(q,pin):
    actual,buffer=q._read(pin['path'],parse=True);q._bind(pin['path'],actual)
    original.original.exact(actual,pin,'PRESERVED_QUALIFIED_SOURCE')
    return bytes(buffer)


def retained_evidence(row):
    original.additional_observer_evidence(row)
    n=len(row['source_freeze']);h=row['source_frame']['handles'];s=h['borrowed_byte_streams']
    original.original.fields(s,dict(duplicate_handles_opened=n,duplicate_handles_closed=n,
        duplicate_handles_remaining=0,duplicate_close_failed_attempts=0,
        shared_offset_resets=2*n,retained_within_one_live_frame_only=True,unbuffered_raw_streams=True,
        parsed_JSON_hash_or_byte_cache=False,physical_handle_ceiling=8192,
        new_duplicate_open_reservations=n,reused_stream_pressure_checkpoints=n,
        logical_read_leases=2*n,logical_read_lease_returns=2*n,pending_open_reservation=False,
        resource_callback_retained_on_reuse=True,cursor_reset_and_fresh_identity_on_each_pass=True),'REAL_RETAINED_MODE')
    require(type(s['physical_handle_peak']) is int and s['physical_handle_peak']==h['input_lock_handles_opened']+n
        and s['physical_handle_peak']<=8192,'TOTAL_REAL_PHYSICAL_HANDLE_CEILING')
    original.original.fields(row['complete_runtime_budget'],dict(
        removed_second_duplicate_handle_reservations=n,removed_second_duplicate_pacing_seconds=n/20,
        byte_or_native_costs_assumed_overlapped=False,parsed_JSON_hash_or_byte_cache=False),'NO_HIDDEN_OR_SKIPPED_BYTE_COST')


def prepare(q):
    require(type(ROOT_PIN) is dict,'COMPLETED_ACTUAL114_PIN_REQUIRED')
    a=original.original;row=a.read_exact(q,ROOT_PIN)
    parent=a.read_exact(q,runtime.PRIOR_ACCEPT_PIN)
    a.fields(parent,dict(state=original.PASS,accepted_count_after=107,accepted_count_delta=1,
        next_runtime_index=114,resource_cleanup_confirmed=True,full249_current_qualified=False,
        signed16_current_qualified=False,P09_gate='OPEN'),'PRIOR_ACTUAL107')
    listing=a.read_exact(q,a.scope.LIST_PIN);body=a.read_exact(q,a.BODY_PIN)
    fresh=a.packed.unpack(a.read_exact(q,a.FRESH_PIN),q.checkpoint)
    require(listing['source_test_names'][113]==runtime.CASE,'FULL249_EXACT_NEXT114')
    project,proof=projection(read_source(q,ACCEPTOR_PIN),'validator')
    check,original_proof=project(read_source(q,original.ORACLE_PIN),row,listing,body)
    evidence=check(row,listing,body,fresh,q.checkpoint);retained_evidence(row)
    a.resource_history(parent['resource_samples'])
    proof.update(original_validator_projection=original_proof,
        all_original_nonphysical_byte_identity_resource_Job_capture_cleanup_checks_retained=True)
    return row,listing,evidence,proof


def run():
    # Small exact bootstrap; original guarded qualifier freshly reads this
    # preserved source and both current acceptor files again before success.
    path=original.original.c.ROOT/ACCEPTOR_PIN['path']
    with path.open('rb') as stream:raw=stream.read(ACCEPTOR_PIN['bytes']+1)
    execute,_=projection(raw,'run')
    return execute()


if __name__=='__main__':raise SystemExit(run())
