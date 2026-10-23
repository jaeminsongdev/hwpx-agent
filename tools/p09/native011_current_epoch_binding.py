"""Bind original current-runtime metadata to real 805-source cohort evidence."""
import ast
import copy
import hashlib
import json
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_binding.py'
TEST='tools/p09/tests/test_native011_current_epoch_binding.py'
SOURCE=dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')
FRESH=dict(path='implementation/p09/evidence/locked-r07/p340-light-review-run131.v1.json',
    bytes=94990,sha256='6d05cb6bf810ff5c19c61d1bc2d76921a00abb00d0f959c51e5fed9402a782ff')
METADATA_CODE=(SELF,TEST,SOURCE['path'],'tools/p09/native011_current_epoch_scope.py',
    'tools/p09/tests/test_native011_current_epoch_scope.py','tools/p09/current_stored_runtime_scope.py',
    'tools/p09/tests/test_current_stored_runtime_scope.py','tools/p09/native011_current_cohort_listing.py',
    'tools/p09/tests/test_native011_current_cohort_listing.py','tools/p09/packed_receipt_json.py')


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_BINDING_'+code)


def metadata_control_names(scope,epoch):
    require(scope.SELF=='tools/p09/current_stored_runtime_scope.py'
        and epoch.SELF=='tools/p09/native011_current_epoch_scope.py','FIXED_METADATA_HELPER_IDENTITIES')
    names=set(METADATA_CODE)|{FRESH['path'],epoch.BODY['path'],scope.LIST_PIN['path']}
    require(len(names)==13,'CLOSED_TEN_CODE_THREE_DATA_ROLES')
    return names


def project_binding(raw,definitions,namespace):
    tree=ast.parse(raw);found=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='binding']
    require(len(found)==1,'ONE_WHOLE_ORIGINAL_BINDING')
    original=found[0];selected=copy.deepcopy(original);changes=[]
    class Count(ast.NodeTransformer):
        def visit_Compare(self,node):
            pattern=ast.Compare(left=ast.Call(func=ast.Name(id='len',ctx=ast.Load()),
                args=[ast.Name(id='rust',ctx=ast.Load())],keywords=[]),ops=[ast.Eq()],comparators=[ast.Constant(787)])
            if ast.dump(node,include_attributes=False)==ast.dump(pattern,include_attributes=False):
                changes.append(True);node.comparators[0]=ast.copy_location(ast.Constant(805),node.comparators[0])
            return self.generic_visit(node)
    selected=Count().visit(selected);require(len(changes)==1,'ONE_EXACT_RUST_COUNT_GUARD')
    inverse=copy.deepcopy(selected)
    class Undo(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value) is int and node.value==805:
                return ast.copy_location(ast.Constant(787),node)
            return node
    require(ast.dump(Undo().visit(inverse),include_attributes=False)==ast.dump(original,include_attributes=False),
        'WHOLE_BINDING_AST_INVERSE')
    source=ast.unparse(ast.fix_missing_locations(ast.Module(body=[selected],type_ignores=[])))
    function=definitions(source,('binding',),namespace).binding
    return function,dict(original_source_pin=SOURCE,whole_function_AST_inverse=True,
        original_historical131_and105_checks_preserved=True,changed_guard=dict(before=787,after=805),
        old_schema_PASS_fabricated=False)


class BoundScope:
    """One exact original binding transaction; never a Frame or product permission."""
    def __init__(self,scope,declaration,listing,controls,exe,archive_rows):
        self.base=scope;self.listing=copy.deepcopy(listing);self.calls=[];self.archive_rows=archive_rows
        self.current=scope.extend(declaration.current,controls)
        self.whole=scope.extend(declaration.whole,controls)
        self.translations=declaration.translations
        # No source module/global is patched; only this private explicit API is used.
        self.api=NS(**{**vars(scope),'EXE_PIN':dict(exe),
            'listing_inputs':self.listing_inputs,'compose':self.compose})

    def listing_inputs(self,row):
        require(self.calls==[] and row==self.listing,'ONE_EXACT_REAL_LIST_RECORD')
        self.calls.append('listing_inputs')
        return {n:dict(p) for n,p in self.current.items()}

    def compose(self,original,current):
        require(self.calls==['listing_inputs'],'ORIGINAL_BINDING_CALL_ORDER')
        require(self.base.pins(current)==self.current,'EXACT_CURRENT_DECLARATION_NO_SCOPE_SUBSTITUTION')
        source=self.base.pins(original,1658)
        archived=self.archive_rows(source,self.translations,self.base)
        expected=self.base.extend(archived,self.current)
        require(expected==self.whole,'INDEPENDENT_WHOLE_SCOPE_RECOMPOSITION')
        self.calls.append('compose')
        return expected


def prepare_binding(q,a,scope,epoch,build_contract,packed):
    declaration,listing,rust,translations=epoch.prepare(q,a,scope,build_contract)
    raw=q.text(SOURCE['path']);a.exact(q.snapshots[SOURCE['path']],SOURCE,'EXACT_WHOLE_ORIGINAL_NATIVE_METADATA_SOURCE')
    controls={}
    for name in sorted(metadata_control_names(scope,epoch)):
        actual=q.snapshots.get(name)
        if actual is None:actual=q.pin(name)
        controls[name]=dict(actual)
    controls=scope.pins(list(controls.values()))
    owner=BoundScope(scope,declaration,listing,controls,listing['compiled_test_executable_pin'],epoch.archive_rows)
    owner.api.LIST_PIN=dict(epoch.LIST)
    owner.api.CURRENT_LIBRARY=dict(rust['crates/product-cli/src/lib.rs'])
    owner.api.CURRENT_MODULE=dict(rust['crates/product-cli/src/reference_validation_product.rs'])
    function,projection=project_binding(raw,a.native.definitions,
        dict(scope=owner.api,packed=packed,require=require,FRESH_PIN=FRESH,BODY_PIN=epoch.BODY))
    required,observed_rust=function(q)
    require(required==owner.whole and observed_rust==set(rust) and len(observed_rust)==805
        and owner.calls==['listing_inputs','compose'],'ACTUAL_ORIGINAL_METADATA_TRANSACTION')
    return NS(scope=owner.api,required=required,rust=observed_rust,owner=owner,
        projection=projection,controls=controls,base=declaration)


def main(generation=1):
    require(type(generation) is int and generation in (1,2),'CLOSED_METADATA_GENERATION')
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('CURRENT805_METADATA_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    import native011_current_epoch_scope as epoch,native011_current_cohort_listing as listing
    import packed_receipt_json as packed
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import native011_source_generation_audit as audit
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_CURRENT805_ORIGINAL_METADATA_BINDING_NOT_RUNTIME',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,actual_Native_Frame_or_product_qualified=False,
        full_required_bytes_freshly_verified=False,worker_or_product_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        for name in (epoch.SELF,epoch.TEST,scope.SELF,'tools/p09/native011_current_cohort_listing.py',
                     'tools/p09/packed_receipt_json.py'):q.pin(name)
        actual=prepare_binding(q,a,scope,epoch,listing.build_contract,packed)
        require(set(q.snapshots)<=set(actual.required),'EVERY_ACTUAL_METADATA_READ_DECLARED_NO_OBSERVED_UNION')
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'ALL_METADATA_AND_ARCHIVE_INPUTS_CLOSING')
        row.update(state='PASS_ORIGINAL_CURRENT805_METADATA_BINDING_NOT_NATIVE_OR_PRODUCT',
            original_binding_projection=actual.projection,actual_binding_calls=actual.owner.calls,
            required_inputs=len(actual.required),required_sha256=epoch.digest(actual.required),
            declared_current_inputs=len(actual.owner.current),current_sha256=epoch.digest(actual.owner.current),
            complete_current_rust_count=len(actual.rust),compiled_candidate_pin=actual.scope.EXE_PIN,
            live_mutation_of_original_scope=False,prior_history_and_acceptances_not_rebased=True,
            explicit_binding_control_pins=list(actual.controls.values()),
            every_actual_metadata_input_in_required=True,controls_selected_before_consumption=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_CURRENT805_METADATA_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            process_creation_attempts=len(denied),resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,
            f'implementation/p09/evidence/p09-361-native011-current805-original-binding{generation:03}.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),
            required=row.get('required_inputs'),rust=row.get('complete_current_rust_count'),
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':
    require(sys.argv[1:] in ([],['--generation2']),'CLOSED_METADATA_ARGUMENTS')
    raise SystemExit(main(2 if sys.argv[1:] else 1))
