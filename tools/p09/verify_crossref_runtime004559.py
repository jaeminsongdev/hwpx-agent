"""Qualify only the changed004 admission/composition, retaining unchanged worker results."""
import ast,hashlib,importlib,json,re,subprocess,sys,time,unittest
from pathlib import Path
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch as entry
import crossref_external_batch_runtime as runtime
import crossref_runtime004_admission as admission

SELF='tools/p09/verify_crossref_runtime004559.py'
OUTPUT=entry.generation_names(current004=True)['code']
BASE='implementation/p09/evidence/p09-361-capture004-entry-code551.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-runtime004-559/'
ENTRY='tools/p09/run_external_crossref_fixed_batch.py'
RUNTIME='tools/p09/crossref_external_batch_runtime.py'
MODELS=('tools/p09/tests/test_crossref_generation004.py','tools/p09/tests/test_crossref_runtime004_admission.py')
PREIMAGES={ENTRY:ARCHIVE+'entry-before.py',RUNTIME:ARCHIVE+'runtime-before.py',MODELS[0]:ARCHIVE+'models-before.py'}
ENTRY_EDITS=(
    ('import crossref_external_batch_runtime as runtime\n','import crossref_external_batch_runtime as runtime\nimport crossref_runtime004_admission as runtime004\n'),
    ('p09-361-capture004-entry-code551.v1.json','p09-361-capture004-entry-code559.v1.json'),
    ('p09-361-capture004-entry-ready552.v1.json','p09-361-capture004-entry-ready560.v1.json'),
    ('p09-361-external-qualified-generation004-preflight.v1.json','p09-361-external-qualified-generation004-runtime559-preflight.v1.json'),
    ('        else:proof,manifest,paths=load_manifest(q,require_runtime_ready=execute)\n',
        "        else:proof,manifest,paths=load_manifest(q,require_runtime_ready=execute)\n        if current004:row['runtime004_qualification']=runtime004.require_qualification(q)\n"),
    ('        installed.runtime_pin_matches(python.pin(installed.fixed.PYTHON.name))\n',
        "        if current004:row['runtime004_current_images']=runtime004.verify_current_reader(python)\n        else:installed.runtime_pin_matches(python.pin(installed.fixed.PYTHON.name))\n"))
RUNTIME_EDITS=(
    ('import crossref_capture004_worker as capture004\n','import crossref_capture004_worker as capture004\nimport crossref_runtime004_admission as runtime004\n'),
    ("CAPTURE004_CASE_PATHS=CASE_PATHS|set(capture004.SOURCES)|{'tools/p09/crossref_capture004_namespace.py','tools/p09/crossref_capture004_worker.py'}\n",
        "CAPTURE004_CASE_PATHS=CASE_PATHS|set(capture004.SOURCES)|{'tools/p09/crossref_capture004_namespace.py','tools/p09/crossref_capture004_worker.py',\n    'tools/p09/crossref_runtime004_admission.py','tools/p09/crossref_python_current555.py'}\n"),
    ('    def __init__(self,guard,manifest,paths,label,shell_expected):\n',
        "    def __init__(self,guard,manifest,paths,label,shell_expected,*,current004=False):\n        require(type(current004)is bool,'EXACT_BOUNDARY004_FLAG')\n"),
    ('        installed.runtime_pin_matches(self.runtime.pin(installed.fixed.PYTHON.name))\n',
        '        if current004:self.runtime_profile=runtime004.verify_current_reader(self.runtime)\n        else:installed.runtime_pin_matches(self.runtime.pin(installed.fixed.PYTHON.name))\n'),
    ('        self.guard,self.manifest,self.shell_expected=guard,manifest,shell_expected;self.current=None;self.rows=[]\n',
        '        self.guard,self.manifest,self.shell_expected=guard,manifest,shell_expected;self.current=None;self.rows=[]\n        self.current004=fixed_capture004\n'),
    ("        self.current=Boundary(self.guard,self.manifest,self.paths,'case'+str(index),self.shell_expected)\n",
        "        self.current=Boundary(self.guard,self.manifest,self.paths,'case'+str(index),self.shell_expected,**({'current004':True}if self.current004 else{}))\n"),
    ("    qualification=Boundary(guard,manifest,all_paths,'current_session_qualification',shell_expected)\n",
        "    qualification=Boundary(guard,manifest,all_paths,'current_session_qualification',shell_expected,**({'current004':True}if fixed_capture004 else{}))\n"),
    ("    check_attempts();current=Boundary(guard,manifest,all_paths,'current_fixed_eight',shell_expected)\n",
        "    check_attempts();current=Boundary(guard,manifest,all_paths,'current_fixed_eight',shell_expected,**({'current004':True}if fixed_capture004 else{}))\n"))

def exact_changes(reader,path,edits):
    text=reader.text(PREIMAGES[path])
    for old,new in edits:
        r.c.require(text.count(old)==1,'P559_ONE_EXACT_REVIEWED_CHANGE_SITE');text=text.replace(old,new,1)
    r.c.require(text==reader.text(path),'P559_WHOLE_PREVIOUS_ENTRY_OR_RUNTIME_EXCEPT_CLOSED004_ADMISSION_PRESERVED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--changed-code-only'],'P559_NO_NATIVE_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P559_IMMUTABLE_CODE_PROOF')
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    modules=[importlib.import_module(Path(path).stem)for path in MODELS]
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=shell=images=None
    row=dict(state='FAILED_RUNTIME004_ADMISSION_CODE',own_cpu_selection=selection,generation=4,
        actual_Hancom_COM_ROT_or_Native_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        new_native_execution_authorized=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        old_Native_or_249_or_worker_PS_models_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        base=r.compact.unpack(q.json(BASE));c.require(q.snapshots[BASE]['sha256']=='f783dca3f6c9ecc755c8127544212720f9af480592bbcee5df2ce44a5d927fbc'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==245
            and base['contracts']==dict(run=33,errors=0,failures=0,skipped=0),'P559_EXACT551_CLOSED_BASELINE')
        host=r.compact.unpack(q.json(admission.QUALIFICATION));c.require(q.snapshots[admission.QUALIFICATION]['sha256']==admission.QUALIFICATION_SHA
            and host['state']==admission.QUALIFICATION_STATE and host['cleanup']is True
            and host['fresh_inputs']==host['final_fresh_hashes']==260,'P559_EXACT558_CLOSED_RUNTIME_WORKER_RESULT')
        for previous in(base,host):
            for pin in previous['source_pins']:
                current=q.pin(PREIMAGES.get(pin['path'],pin['path']))
                c.require((current['bytes'],current['sha256'])==(pin['bytes'],pin['sha256']),'P559_UNCHANGED_RETAINED_INPUT_OR_EXACT_ARCHIVED_PREIMAGE')
        entry_paths=entry.loaded_paths(exclude=(SELF,))|runtime.CAPTURE004_CASE_PATHS|set(runtime.capture004.SOURCES)
        for path in sorted(entry_paths|{SELF,*MODELS,*PREIMAGES.values()}):q.pin(path)
        exact_changes(q,ENTRY,ENTRY_EDITS);exact_changes(q,RUNTIME,RUNTIME_EDITS)
        row['whole_previous_source_outside004_admission_preserved']=True
        row['runtime004_qualification']=admission.require_qualification(q)
        images=a.AcceptanceReader(admission.profile.fixed.PYTHON.parent,guard.check)
        row['current_runtime_images']=admission.verify_current_reader(images)
        shell=a.AcceptanceReader(Path(runtime.candidate.original.SHELL).parent,guard.check)
        c.require(shell.pin(Path(runtime.candidate.original.SHELL).name)==base['external_shell_pins'][0],'P559_SAME_QUALIFIED_SHELL')
        cases=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)for m in modules)
        c.require(cases.countTestCases()==38,'P559_NEW11_AND_AFFECTED27_MODELS_ONLY')
        guard.check(force=True);result=unittest.TestResult();cases.run(result);guard.check(force=True)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=38,errors=0,failures=0,skipped=0),'P559_CHANGED004_MODELS_ALL_PASS')
        for path in(SELF,ENTRY,RUNTIME,*MODELS,'tools/p09/crossref_runtime004_admission.py'):ast.parse(q.text(path))
        runtime.absent_attempts(fixed_capture004=True)
        images.finish();shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(entry_paths),external_shell_pins=list(shell.snapshots.values()),
            external_shell_final_fresh_hashes=shell.final_fresh_hashes,runtime_disk_image_pins=list(images.snapshots.values()),
            runtime_disk_image_final_fresh_hashes=images.final_fresh_hashes,retained_worker_models=6,retained_PS_models=8,
            retained_worker_ready_denial=admission.QUALIFICATION,retained_runtime_and_worker_components_freshly_identical=True,
            public004_profile_connected_but_no_current_public_preflight_or_native_permit=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P559_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=entry.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state']==entry.CODE_STATE and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
