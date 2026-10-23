"""492: current003 public entry/runtime glue, new25 + directly affected legacy5. Never Native."""
import ast,copy,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch as entry
import crossref_external_batch_runtime as runtime

SELF='tools/p09/verify_crossref_generation003.py'
TEST='tools/p09/tests/test_crossref_generation003.py'
LEGACY='tools/p09/tests/test_crossref_qualified_entry.py'
OLD002='tools/p09/tests/test_crossref_generation002.py'
OUTPUT=entry.generation_names(current003=True)['code']
ARCHIVE='implementation/p09/source-archive/p361-capture003-entry492/'
RUNTIME='tools/p09/crossref_external_batch_runtime.py'

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,r.c.ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def remove_flag(node):
    r.c.require(len(node.args.kwonlyargs)==1 and node.args.kwonlyargs[0].arg=='fixed_capture003','EXACT_CLOSED_SCOPE_KEYWORD_ONLY')
    node.args.kwonlyargs=[];node.args.kw_defaults=[]

def runtime_inverse(current,original):
    tree=ast.parse(current);old=ast.parse(original)
    class LegacyNames(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id=='check_attempts':node.id='absent_attempts'
            return node
    result=[]
    for node in tree.body:
        if isinstance(node,ast.Import)and any(a.name=='crossref_capture003_worker'for a in node.names):continue
        if isinstance(node,ast.Assign)and isinstance(node.targets[0],ast.Name)and node.targets[0].id=='CAPTURE003_CASE_PATHS':continue
        if isinstance(node,ast.FunctionDef):
            if node.name=='fixed_input_pins':continue
            if node.name=='absent_attempts':remove_flag(node);node.body=node.body[2:]
            if node.name=='capture_artifacts':
                remove_flag(node);node.body=node.body[1:]
                loop=next(n for n in node.body if isinstance(n,ast.For))
                r.c.require(isinstance(loop.body[0].value,ast.IfExp),'EXACT_CAPTURE003_ARTIFACT_DIRECTORY_CHOICE')
                loop.body[0].value=loop.body[0].value.orelse
            if node.name=='execute':
                remove_flag(node);node.body=node.body[3:];LegacyNames().visit(node)
                for child in node.body:
                    if isinstance(child,ast.Assign)and isinstance(child.targets[0],ast.Name):
                        name=child.targets[0].id
                        if name=='cases':child.value.keywords=[]
                        if name=='full':child.value=child.value.orelse
                    if isinstance(child,ast.Try):
                        for statement in child.body:
                            if isinstance(statement,ast.Assign)and isinstance(statement.targets[0],ast.Subscript):
                                if isinstance(statement.targets[0].slice,ast.Constant)and statement.targets[0].slice.value=='artifacts':statement.value=statement.value.orelse
        if isinstance(node,ast.ClassDef)and node.name=='Boundary':
            init=node.body[0];init.body=[n for n in init.body if not(isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='fixed_pins')]
            for child in ast.walk(init):
                if isinstance(child,ast.Name)and child.id=='fixed_pins':child.id='INPUT_PINS'
        if isinstance(node,ast.ClassDef)and node.name=='CaseInputs':
            init=node.body[0];remove_flag(init);init.body=init.body[1:-1]
            begin=node.body[1]
            for child in ast.walk(begin):
                if isinstance(child,ast.Call):
                    child.args=[ast.Name(id='CASE_PATHS',ctx=ast.Load())if isinstance(a,ast.Attribute)and isinstance(a.value,ast.Name)
                        and a.value.id=='self'and a.attr=='paths'else a for a in child.args]
        result.append(node)
    tree.body=result
    r.c.require(ast.dump(tree,include_attributes=False)==ast.dump(old,include_attributes=False),
        'WHOLE_ORIGINAL_RUNTIME_AST_RESTORED_EXCEPT_FIXED003_NAMESPACE_INPUT_AND_WORKER_SELECTION')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--code-models-only'],'CAPTURE003_CODE_MODELS_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'CAPTURE003_CODE492_IMMUTABLE')
    models=load(TEST,'p09_current003_models');legacy=load(LEGACY,'p09_current003_legacy');old002=load(OLD002,'p09_current003_old002')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=shell=None;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE003_ENTRY_CODE_PACKAGE',own_cpu_selection=selection,steps=[],generation=3,
        actual_Hancom_ROT_COM_or_worker_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,retained_compiled_or_powershell_models_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        proofs={}
        for path,sha in(
            ('implementation/p09/evidence/p09-361-capture003-powershell490.v1.json','0bb615761917ae69dea90fa0569210105e941ab8f7ea3292b8e7569f5b495ef7'),
            ('implementation/p09/evidence/p09-361-capture003-worker491.v1.json','c576ff48bd0ed52844e97a79cfda8f2dc61a42a6f08216de8473030e8c3d3ba0')):
            proof=r.compact.unpack(q.json(path));c.require(q.snapshots[path]['sha256']==sha and proof['state'].startswith('PASS_')
                and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']>0,'EXACT_ACCEPTED003_NAMESPACE_AND_WORKER_PROOFS')
            proofs.update({p['path']:p for p in proof['source_pins']})
        dependencies=entry.loaded_paths(exclude=(SELF,))|set(runtime.candidate.SOURCES)|runtime.CAPTURE003_CASE_PATHS
        dependencies-=set(runtime.fixed_input_pins(True));row['entry_dependency_paths']=sorted(dependencies)
        c.require(entry.SELF in dependencies and runtime.CAPTURE003_CASE_PATHS<=dependencies|set(runtime.fixed_input_pins(True)),'COMPLETE003_ENTRY_AND_EVERY_CASE_INPUT_CLOSURE')
        changed={entry.SELF,RUNTIME}
        for path in sorted(dependencies):
            pin=q.pin(path)
            if path in proofs and path not in changed:c.require(pin==proofs[path],'ORIGINAL_GUARDS_OWNER_WORKER_LIMITS_AND_VERIFIED003_PROGRAM_UNCHANGED')
        for path in(SELF,TEST,LEGACY,OLD002,ARCHIVE+'runtime-original.py',ARCHIVE+'entry-original.py'):q.pin(path)
        runtime_inverse(q.text(RUNTIME),q.text(ARCHIVE+'runtime-original.py'));row['whole_original_runtime_ast_inverse_verified']=True
        for path,(size,sha)in runtime.fixed_input_pins(True).items():
            pin=q.pin(path);c.require((pin['bytes'],pin['sha256'])==(size,sha),'EXACT_ORIGINAL_INPUT_AND_BOTH_FIXED_READONLY_PROBES')
        runtime.absent_attempts(fixed_capture003=True)
        for key in('claim','output'):
            target=c.ROOT/entry.generation_names(current003=True)[key]
            c.require(not target.exists()and not target.is_symlink(),'CURRENT003_UNCONSUMED_NO_REPLAY')
        new=list(unittest.defaultTestLoader.loadTestsFromTestCase(models.Generation003));c.require(len(new)==25,'EXACT25_NEW003_GLUE_MODELS')
        affected=[legacy.EntryContracts(name)for name in('test_31_boundary_uses_fresh_pin_for_repeated_native_image_checks',
            'test_32_case_boundaries_are_fresh_one_at_a_time_not_history_replay','test_34_artifact_binding_requires_all_sixteen_closed_native_sessions')]
        affected+=[old002.Tests(name)for name in('test_current_manifest_uses_new_code_without_old_authority','test_new_public_preflight_never_claims_or_executes_even_if_prerequisites_pass')]
        result=unittest.TestResult();row['contract_names']=[test.id()for test in new+affected]
        for test in new+affected:test.run(result);guard.check(force=True)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=30,errors=0,failures=0,skipped=0),'ALL_NEW25_AFFECTED5_CURRENT003_MODELS')
        for path in(SELF,TEST,entry.SELF,RUNTIME):ast.parse(q.text(path))
        shell=a.AcceptanceReader(Path(runtime.candidate.original.SHELL).parent,guard.check);shell.pin(Path(runtime.candidate.original.SHELL).name)
        shell.finish();q.finish();guard.check(force=True);row['state']=entry.CODE_STATE
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CAPTURE003_CODE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            external_shell_pins=[]if shell is None else list(shell.snapshots.values()),external_shell_final_hashes=0 if shell is None else shell.final_fresh_hashes,
            resource_samples=samples,elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'entry_dependencies':len(row.get('entry_dependency_paths',[])),'receipt':pin}),flush=True)
    return 0 if row['state']==entry.CODE_STATE and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
