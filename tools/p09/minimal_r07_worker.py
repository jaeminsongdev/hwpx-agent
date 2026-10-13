"""P204 execution-only worker: same owned GO/Job and exact immutable r07 EXE.

과거 검사/보고 모듈을 worker에 import하지 않는다. 원 maintenance 두 소스는
고정 byte로 확인하고 source에서만 import한다. 원 Job/GO/환경/옵션은 유지한다.
이 파일 자체의 실제 owned 실행 연결은 별도 부모 검증이 필요하다.
"""
import hashlib
import importlib.machinery
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
SELF='tools/p09/minimal_r07_worker.py'
TEST='tools/p09/tests/test_minimal_r07_worker.py'
PARENT=dict(path='implementation/p09/evidence/p09-186-observed-r07-list-output.source-closing-run01.v1.json',
    bytes=339893,sha256='7b06997d3b8090967597fad1d12b94446e20e3a17ba206233ae8711fdb1d455d')
EXE=dict(path='target/p09-175-xml-initial-capacity/debug/deps/form_stored_provider-p152-r07.exe',
    bytes=14216704,sha256='2b47e5815500549401f6f1960d92ba67f0d3410fc39d91cc91fd7f886d67dc5d')
TARGET=ROOT/'target/p09-175-xml-initial-capacity'
TASK_ARGS=['test','-p','hwpx-agent-cli','--test','form_stored_provider']
CORE_PINS={
    'tools/p09/conservative_maintenance.py':dict(bytes=29237,sha256='11b1a55aed7a11ed6a2e8b0dd4d6b6dd73d4019fffa5deabe7e0827665173ad9'),
    'tools/p09/audit_evidence_io.py':dict(bytes=5653,sha256='84b7dae287ac01c7ec308ca302762ec283406fca3fa43bc469882a3913578a8f')}


def require(ok,code):
    if not ok:raise ValueError('P204_MINIMAL_'+code)


def bounded_bytes(path,expected):
    require(path.resolve().is_relative_to(ROOT),'READ_OUTSIDE_ROOT')
    current=path
    while current!=ROOT:
        require(not current.is_symlink() and not current.is_junction(),'SOURCE_LINK_OR_REPARSE')
        require(current.parent!=current,'ANCESTOR_BOUNDARY');current=current.parent
    require(path.is_file() and path.stat().st_size==expected['bytes'],'SOURCE_SIZE')
    with path.open('rb') as stream:raw=stream.read(expected['bytes']+1)
    require(len(raw)==expected['bytes'] and hashlib.sha256(raw).hexdigest()==expected['sha256'],'SOURCE_BYTE_HASH')
    return raw


def load_maintenance():
    loader=importlib.machinery.SourceFileLoader;original=loader.get_code
    def source_only(instance,fullname):
        path=Path(instance.path)
        if path.resolve().is_relative_to(ROOT):
            name=path.relative_to(ROOT).as_posix()
            require(name in CORE_PINS,'ONLY_TWO_CORE_IMPORTS')
            raw=bounded_bytes(path,CORE_PINS[name])
            return instance.source_to_code(raw,instance.path)
        return original(instance,fullname)
    loader.get_code=source_only
    try:
        import conservative_maintenance as maintenance
        # 이미 import된 경우에도 source drift를 거부한다. 캐시/파일은 수정하지 않는다.
        for name,pin in CORE_PINS.items():bounded_bytes(ROOT/name,pin)
        return maintenance
    finally:loader.get_code=original


def inventory():
    parent=json.loads(bounded_bytes(ROOT/PARENT['path'],PARENT).decode('utf-8'))
    require(parent['compiled_test_executable_pin']==EXE and parent['compiled_test_count']==249
        and parent['current_Rust_input_count']==785 and parent['current_source_module_instance_count']==59
        and parent['full249_current_qualified'] is False and parent['product_complete'] is False
        and parent['P09_gate']=='OPEN','COMPILED_ONLY_PINNED_PARENT')
    return parent


def select(index,parent=None):
    require(type(index) is int and 1<=index<=249,'CASE_RANGE')
    parent=inventory() if parent is None else parent;names=parent['source_test_names']
    require(len(names)==len(set(names))==249 and parent['compiled_test_executable_pin']==EXE,'EXACT249_CURRENT_EXE')
    name=names[index-1]
    require(isinstance(name,str) and re.fullmatch('[A-Za-z_][A-Za-z0-9_:]*',name)
        and not name.startswith('actual_import::formula_policy_issuer::corpus::'),'REGULAR_PUBLIC_CASE_ONLY')
    return name,[name,'--exact','--test-threads=1','--format=pretty','--color=never']


def worker(task):
    match=re.fullmatch(r'p204-r07-case-([0-9]{3})-tests',task);require(match is not None,'TASK_SCOPE')
    index=int(match[1]);require(task==f'p204-r07-case-{index:03}-tests','TASK_CANONICAL')
    _,arguments=select(index);c=load_maintenance();original_call=c.subprocess.call
    old_tasks,old_target=c.TASKS,c.TARGET
    def selected(args,**kw):
        require(args[1:]==[*TASK_ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(TARGET),
            '--','--test-threads=1'] and kw['cwd']==ROOT and kw['stdin']==c.subprocess.DEVNULL,'ORIGINAL_ARGUMENTS')
        require(all(kw['env'][k]==value for k,value in dict(CARGO_BUILD_JOBS='1',RUST_TEST_THREADS='1',
            RUSTUP_AUTO_INSTALL='0',CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',
            CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true').items()),'ORIGINAL_ENVIRONMENT')
        kw['env']=dict(kw['env'],RUST_TEST_NOCAPTURE='0')
        return original_call([str(ROOT/EXE['path']),*arguments],**kw)
    c.TASKS={task:TASK_ARGS};c.TARGET=TARGET;c.subprocess.call=selected
    try:return c.worker(task)  # 원 GO/Job을 유지하며 실제 limit/cleanup은 부모가 확인한다.
    finally:c.TASKS=old_tasks;c.TARGET=old_target;c.subprocess.call=original_call


if __name__=='__main__':
    try:
        require(len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task'],'OWNED_ENTRY_ONLY')
        raise SystemExit(worker(sys.argv[3]))
    except (ValueError,OSError,KeyError,TypeError) as error:
        code=str(error) if re.fullmatch(r'P204_MINIMAL_[A-Z0-9_]+',str(error)) else 'P204_MINIMAL_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code)));raise SystemExit(2) from None
