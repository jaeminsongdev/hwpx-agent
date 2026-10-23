"""Original four-stage owned monitor for the actual owned metadata preparation.

No marker authorizes product execution or changes a Native deadline. The
original monitor, Job, sampler, failure preservation and cleanup remain intact.
"""
import ast
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import native011_current_epoch_owned_audit as original

SELF='tools/p09/native011_engine_owned_metadata_preparation_owned.py'
TEST='tools/p09/tests/test_native011_engine_owned_metadata_preparation_owned.py'
TARGET='tools/p09/native011_engine_owned_metadata_preparation.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-engine-owned-metadata-preparation-owned001.v1.json'
CHILD_PASS='PASS_PREPARATION_FULL_OWNED_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE'
OWNED_PASS='PASS_OWNED_FULL_ENGINE_OWNED_METADATA_PREPARATION_NOT_NATIVE'
EXTRA=(TEST,original.SELF,original.TEST,'tools/p09/native011_engine_owned_metadata_callback.py',
    'tools/p09/tests/test_native011_engine_owned_metadata_callback.py',
    'tools/p09/native011_engine_owned_metadata_connection.py','tools/p09/tests/test_native011_engine_owned_metadata_connection.py',
    'tools/p09/native011_engine_owned_metadata_adoption.py','tools/p09/tests/test_native011_engine_owned_metadata_adoption.py',
    'tools/p09/native011_metadata_tail_probe.py','tools/p09/tests/test_native011_metadata_tail_probe.py',
    'tools/p09/native011_current_epoch_audit.py','tools/p09/tests/test_native011_current_epoch_audit.py',
    'tools/p09/tests/test_native011_engine_owned_metadata_preparation.py')


def require(ok,code):
    if not ok:raise ValueError('OWNED_METADATA_PREPARATION_'+code)


def validate(proof,read):
    require(proof['state']==CHILD_PASS and proof['cleanup_confirmed'] is True
        and proof['fresh_inputs']==proof['final_fresh_hashes']>0 and proof['process_creation_attempts']==0
        and proof['actual_Native_Frame_created'] is proof['actual_product_executed'] is proof['GO_authorized'] is False
        and proof['Native_clock_reset_or_extended'] is False and proof['shared_budget_restored'] is True
        and proof['parent_attempts']==proof['Frame_instances']==proof['worker_attempts']==proof['worker_calls']==0,
        'COMPLETE_PREPARATION_NEVER_NATIVE_OR_PRODUCT')
    prep=proof['owned_metadata_preparation'];epochs=prep['epochs']
    require([e['stage'] for e in epochs]==['construction','opening','metadata','closing']
        and all(e['cleanup_confirmed'] is True and 0<e['elapsed_seconds']<600 for e in epochs),
        'FOUR_ORIGINAL_PREPARATION600_EPOCHS')
    first=prep['whole_opening'];last=prep['whole_closing'];meta=prep['metadata']
    require(first==last and first['actual_complete'] is True
        and first['fresh_inputs']==prep['declared_whole_inputs']==proof['whole_inputs']
        and first['bytes_read']==prep['declared_whole_bytes']
        and first['full_pin_sha256']==prep['whole_pin_sha256'],'BOTH_COMPLETE_WHOLE_BOUNDARIES')
    require(meta['state']=='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE'
        and meta['fresh_inputs']==meta['final_fresh_hashes']>0
        and meta['selected_current_inputs']==proof['current_inputs']
        and proof['shared_parent_connection']['preaudit_callback_attempts']==1
        and proof['shared_parent_connection']['original_preaudit_denial_before_metadata_IO'] is True
        and meta['callback_attempts']==2
        and meta['metadata_body_executed'] is True
        and meta['Frame_created'] is meta['worker_created'] is meta['GO_authorized'] is False
        and meta['preparation_only_owned_allocation'] is True and meta['complete_product_input_pins_qualified'] is False
        and meta['original_owned_allocation_assignment_prefix']['original_statements_executed']==2,
        'ORIGINAL_FULL_CALLBACK_AND_CLOSING_WITH_OWNED_PREFIX')
    adopted=prep['actual_owned_metadata_adoption']
    require(adopted['original_engine_owned_assignment_adopted'] is True and adopted['failed'] is False
        and adopted['assignment_attempts']==adopted['assignment_completed']==1
        and adopted['semantic_fresh_inputs']==adopted['semantic_final_fresh_hashes']==meta['fresh_inputs']
        and adopted['physical_read_passes']==prep['original_query_requests']==meta['physical_read_passes']
        and adopted['physical_bytes_read']==meta['physical_bytes_read']==sum(prep['actual_paced_bytes_by_kind'].values())
        and adopted['original_owned_rates']==dict(binary=1048576,other=2097152),
        'ACTUAL_ORIGINAL_OWNED_POLICY_AND_PHYSICAL_IO')
    source=proof['preparation_source_evidence']
    require(source['fresh_inputs']==source['final_fresh_hashes']==len(source['source_pins'])>0
        and source['constructor_reader_reused'] is False
        and source['callback_projection']['entire_original_metadata_body_inverse'] is True
        and source['callback_projection']['changed_allocation_dependency_sites']==1
        and source['connection']['original_engine_metadata_IO_rates']==dict(binary=1048576,other=2097152),
        'SEPARATE_COMPLETE_SOURCE_READER_AND_ORIGINAL_BODY')
    for phase,pin in prep['completed_stage_checkpoint_pins'].items():
        require(phase in ('opening','metadata','closing'),'NAMED_ORIGINAL_CHECKPOINTS')
        value=read(pin)
        require(value['phase']==phase and value['execution_scope_whole_sha256']==prep['whole_pin_sha256']
            and value['GO_authorized'] is False and value['accepted_count_delta']==0
            and value['evidence']['whole_opening']==first,'FRESH_ORIGINAL_STAGE_CHECKPOINT')
        if phase in ('metadata','closing'):require(value['evidence']['metadata']==meta,'FRESH_COMPLETE_METADATA_CHECKPOINT')
        if phase=='closing':require(value['evidence']['whole_closing']==last,'FRESH_COMPLETE_CLOSING_CHECKPOINT')
    require(set(prep['completed_stage_checkpoint_pins'])=={'opening','metadata','closing'},'ALL_THREE_CHECKPOINTS')
    observed=read(proof['shared_decoder_timing_observation_artifact'])
    require(observed['attempts']==observed['completed']==1 and observed['failed'] is False
        and set(observed['roles'])=={'metadata'}
        and observed['original_shared']['shared_limit_seconds']==5.
        and observed['original_shared']['metadata_registered'] is True
        and observed['original_shared']['Frame_registered'] is False
        and 0<=observed['original_shared']['total_decoder_work_seconds']<5.,
        'ACTUAL_UNCHANGED_METADATA_SHARED5_NOT_COMBINED_FRAME_CREDIT')
    return source['source_pins']


def project(raw):
    node,parent_proof=original.project(raw);before=copy.deepcopy(node);counts={}
    def remember(old,new,key):
        counts[key]=counts.get(key,0)+1;new._owned_preparation_before=copy.deepcopy(old);return ast.copy_location(new,old)
    class Adapt(ast.NodeTransformer):
        def visit_Assign(self,item):
            if len(item.targets)==1 and isinstance(item.targets[0],ast.Name):
                name=item.targets[0].id
                if name=='output':return remember(item,ast.parse('output=_owned_preparation_output').body[0],'output')
                if name=='command':return remember(item,ast.parse("command=[sys.executable,'-B',str(c.ROOT/TARGET)]").body[0],'command')
            return self.generic_visit(item)
        def visit_Constant(self,item):
            values={'PASS_OWNED_NATIVE011_ACTUAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE':OWNED_PASS,
                'FAILED_OWNED_NATIVE011_METADATA_AND_WHOLE_NOT_NATIVE':'FAILED_OWNED_ENGINE_OWNED_METADATA_PREPARATION_NOT_NATIVE'}
            if type(item.value) is str and item.value in values:return remember(item,ast.Constant(values[item.value]),'label')
            return item
        def visit_Expr(self,item):
            call=item.value
            if (isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='require'
                and len(call.args)==2 and isinstance(call.args[1],ast.Constant)
                and call.args[1].value=='EXACT_ACTUAL_METADATA_NOT_NATIVE_OR_PRODUCT'):
                return remember(item,ast.parse('_owned_validate_metadata_preparation(proof,q,a)').body[0],'validate')
            return self.generic_visit(item)
        def visit_Subscript(self,item):
            if (isinstance(item.value,ast.Name) and item.value.id=='proof' and isinstance(item.slice,ast.Constant)
                and item.slice.value in ('metadata','whole_batch')):
                return remember(item,ast.parse("proof['owned_metadata_preparation']["+repr(item.slice.value)+"]",mode='eval').body,'result')
            return self.generic_visit(item)
        def visit_For(self,item):
            if (isinstance(item.iter,ast.Tuple) and len(item.iter.elts)>2 and isinstance(item.iter.elts[0],ast.Name)
                and item.iter.elts[0].id=='SELF' and isinstance(item.iter.elts[1],ast.Name) and item.iter.elts[1].id=='TARGET'):
                saved=copy.deepcopy(item)
                item.iter.elts.extend(ast.Constant(name) for name in EXTRA)
                counts['sources']=counts.get('sources',0)+1;item._owned_preparation_before=saved
            return self.generic_visit(item)
    revised=Adapt().visit(node)
    require(counts==dict(output=1,label=2,sources=1,command=1,validate=1,result=2),'EXACT_MONITOR_CONNECTION_SITES')
    class Undo(ast.NodeTransformer):
        def visit(self,item):
            if hasattr(item,'_owned_preparation_before'):return copy.deepcopy(item._owned_preparation_before)
            return super().visit(item)
    require(ast.dump(Undo().visit(copy.deepcopy(revised)),include_attributes=False)==ast.dump(before,include_attributes=False),
        'ENTIRE_PARENT_MONITOR_AST_INVERSE')
    return revised,dict(parent=parent_proof,entire_parent_monitor_AST_inverse=True,sites=counts,
        original_four_phase_monitor_Job_resource_limits_and_cleanup_retained=True,
        original_Native_or_product_authorized=False)


def main():
    require(sys.argv[1:]==[],'CLOSED_NO_GO_ENTRY');root=Path(__file__).resolve().parents[2]
    path=root/original.SOURCE['path']
    for member in (path,*path.parents):
        require(not member.is_symlink() and not member.is_junction(),'DIRECT_ORIGINAL_MONITOR_SOURCE')
        if member==root:break
    with path.open('rb') as stream:raw=stream.read(original.SOURCE['bytes']+1)
    node,proof=project(raw);env=dict(__name__='p09_owned_metadata_preparation_private',__file__=original.SOURCE['path'])
    exec(compile(raw,original.SOURCE['path'],'exec'),env)
    def terminal(owned,capture,row,stdout,stderr,actual):
        return original.preserve_terminal_failure(owned,capture,row,stdout,stderr,NS(seen=actual.seen,MARKERS=env['MARKERS']))
    def observing(actual,markers,owned,capture,row):
        return original.observe_markers(actual,markers,owned,capture,row,terminal)
    def validated(proof,q,a):
        for pin in validate(proof,lambda pin:a.read_exact(q,pin)):
            a.exact(q.pin(pin['path']),pin,'ACTUAL_PREPARATION_COMPONENT_SOURCE_POSTCHECK')
    env.update(SELF=SELF,TARGET=TARGET,_preserve_terminal_failure=terminal,_observe_markers=observing,
        _owned_validate_metadata_preparation=validated,_owned_preparation_output=OUTPUT)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),original.SOURCE['path'],'exec'),env)
    before=sys.argv;sys.argv=[before[0],'--attempt','1','--generation','3']
    try:return env['main']()
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
