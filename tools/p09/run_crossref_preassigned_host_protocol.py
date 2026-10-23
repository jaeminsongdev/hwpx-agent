"""398: new v2 composition16/PS8/actual pipe1, fake owners only; no Native/COM/ROT.

Protocol frames are streamed (4096 bytes/frame, exactly152), never retained as
logs. The original32768 diagnostic cap and readonly90sec owned-Job guard remain.
"""
import hashlib,importlib.util,json,queue,re,subprocess,sys,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_preassigned_host_protocol as subject

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-host398.v1.json'
DRIVER='tools/p09/run_crossref_preassigned_host_protocol.py'
PYTEST='tools/p09/tests/test_crossref_preassigned_host_protocol.py'
PSTEST='implementation/p09/tools/test-crossref-preassigned-host-channel.ps1'
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')
PREVIOUS='implementation/p09/evidence/p09-361-crossref-existing-owner-capture396.v1.json'
PSNAMES={'closed_descriptor','no_descriptor_authority','unknown_descriptor_field','creation_descriptor',
    'escaped_duplicate_reply','old_reply_rejected','unexpected_descriptor_rejected','unknown_reply_field'}
WIRENAME='xref_v2_wire::all_eight_models_and_canonical_descriptors'


def safe_code(error):
    value=error.args[0]if error.args else None
    return value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'V2_TEST_FAILURE_NO_RAW_VALUES'


def open_worker(guard,env,mode):
    return r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',
        str(r.c.ROOT/PSTEST),mode],windows=guard.windows,allowed_executables=[str(SHELL)],cwd=r.c.ROOT,checkpoint=guard.check,env=env)


def run_ps_models(guard,env,row):
    c=r.c;owned=capture=None;started=time.monotonic();step=dict(stage='new_x86_powershell_v2_models8',cleanup=False);row['steps'].append(step)
    try:
        owned=open_worker(guard,env,'-ModelsOnly');capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_V2_MODELS_READONLY_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            safe_error_codes=re.findall(r'(?m)^Error: (P09_XREF_[A-Z0-9_]{1,120})\r?$',stderr),
            summary_observed='8 passed; 0 failed; 0 ignored; v2_models_only_not_native'in stdout)
        c.require(step['exit_code']==0 and not stderr and len(tests)==8 and {name for name,status in tests}=={'xref_v2_ps::'+n for n in PSNAMES}
            and all(status=='ok'for name,status in tests)and step['summary_observed'],'EXACT8_NEW_X86_V2_MODELS_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def run_wire(guard,env,row,models):
    c=r.c;owned=None;threads=[];events=queue.Queue(maxsize=8);stop=threading.Event();started=last=time.monotonic()
    step=dict(stage='actual_x86_python_pipes_full_eight_fake_owners',cleanup=False,requests=0,admissions=0,tests=[])
    row['steps'].append(step)
    stats=dict(stdout_bytes=0,stderr_bytes=0,wire_bytes=0,diagnostic_bytes=0,stream_error=None)
    out_hash=hashlib.sha256();err_hash=hashlib.sha256();stderr_parts=[]

    def emit(kind,value=None):
        while not stop.is_set():
            try:events.put((kind,value),timeout=.1);return
            except queue.Full:pass

    def stdout_io():
        try:
            # 152 closed protocol frames + exactly one test marker and summary.
            for _ in range(155):
                line=owned.stdout.readline(4098)
                if not line:emit('eof');return
                data=line.encode('utf-8');stats['stdout_bytes']+=len(data);out_hash.update(data)
                if len(data)>4097 or not line.endswith('\n'):
                    stats['stream_error']='V2_WIRE_LINE_BOUND';emit('error');return
                emit('line',line.rstrip('\r\n'))
            stats['stream_error']='V2_WIRE_TOTAL_FRAME_BOUND';emit('error')
        except(OSError,ValueError,UnicodeError):stats['stream_error']='V2_WIRE_STDOUT_IO';emit('error')

    def stderr_io():
        try:
            while True:
                part=owned.stderr.read(512)
                if not part:return
                data=part.encode('utf-8');stats['stderr_bytes']+=len(data);err_hash.update(data)
                if stats['stderr_bytes']>4096:stats['stream_error']='V2_WIRE_STDERR_BOUND';emit('error');return
                stderr_parts.append(part)
        except(OSError,ValueError,UnicodeError):stats['stream_error']='V2_WIRE_STDERR_IO';emit('error')

    try:
        owned=open_worker(guard,env,'-WireModelsOnly')
        threads=[threading.Thread(target=stdout_io,daemon=True),threading.Thread(target=stderr_io,daemon=True)]
        for thread in threads:thread.start()
        with models.ModelHost()as model:
            ended=False;summary=False
            while not ended:
                guard.check();account=owned.observe();c.require(time.monotonic()-started<90,'STOP_V2_WIRE_READONLY_DEADLINE')
                c.require(stats['stream_error']is None,stats['stream_error']or'V2_WIRE_STREAM')
                if time.monotonic()-last>=15:
                    sample=guard.samples[-1];print(json.dumps(dict(stage=step['stage'],requests=step['requests'],elapsed=round(time.monotonic()-started,1),
                        system_CPU=sample['system_cpu_percent'],available_RAM_percent=sample['available_ram_percent'],
                        job_private_percent=account['peak_job_private_percent'])),flush=True);last=time.monotonic()
                try:kind,line=events.get(timeout=.1)
                except queue.Empty:continue
                if kind=='eof':ended=True;continue
                c.require(kind=='line','V2_WIRE_READER_FAILED')
                if line.startswith('{'):
                    c.require(not summary and not step['tests']and step['requests']<152,'V2_WIRE_REQUEST_COUNT_ORDER')
                    request=subject.decode_request(line);reply=model.respond(line);decoded=json.loads(reply)
                    step['requests']+=1;stats['wire_bytes']+=len(line.encode())+1
                    if request['operation']=='admit_owner':step['admissions']+=1
                    c.require(decoded['acknowledged']is True,'V2_WIRE_FAKE_SCOPE_ACKNOWLEDGED')
                    c.require(owned.stdin.write(reply+'\n')==len(reply)+1,'V2_WIRE_REPLY_WRITE');owned.stdin.flush()
                else:
                    stats['diagnostic_bytes']+=len(line.encode())+1;c.require(stats['diagnostic_bytes']<=32768,'V2_WIRE_ORIGINAL_DIAGNOSTIC_BOUND')
                    if line=='test '+WIRENAME+' ... ok':
                        c.require(not step['tests']and not summary,'V2_WIRE_SINGLE_TEST_MARKER');step['tests'].append((WIRENAME,'ok'))
                    elif line=='test result: ok. 1 passed; 0 failed; 0 ignored; v2_wire_fake_owners_not_native':
                        c.require(len(step['tests'])==1 and not summary,'V2_WIRE_SINGLE_SUMMARY');summary=True
                    else:raise ValueError('V2_WIRE_UNEXPECTED_DIAGNOSTIC_NO_RAW_VALUES')
            owned.wait(timeout=2);owned.observe();step['exit_code']=owned.returncode
            c.require(step['exit_code']==0 and summary and step['requests']==152 and step['admissions']==16 and len(step['tests'])==1,
                'EXACT152_WIRE_MESSAGES_AND16_FAKE_OWNER_ADMISSIONS_NO_RETRIES')
            result=model.host.summary();c.require(result['protocol']['all_eight_callback_cases_returned']is True
                and result['scope']['all_eight_callback_cases_returned']is True and len(model.created)==16
                and len(result['scope']['retired_sessions'])==16 and not result['native_execution_authorized'],
                'ALL_EIGHT_MODEL_CALLBACKS_AND16_RETIRED_MODEL_SESSIONS_NOT_NATIVE')
            model.scope.close();step['modeled_host_summary']=model.host.summary()
    finally:
        stop.set()
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            for thread in threads:thread.join(timeout=2)
            joined=all(not thread.is_alive()for thread in threads)
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed']and joined,owned_job=owned.profile,io_threads_joined=joined)
        step.update(**stats,stdout_sha256=out_hash.hexdigest(),stderr_sha256=err_hash.hexdigest(),elapsed_seconds=round(time.monotonic()-started,3),
            safe_error_codes=re.findall(r'(?m)^Error: (P09_XREF_[A-Z0-9_]{1,120})\r?$', ''.join(stderr_parts)))
    c.require(step['cleanup']and step['stderr_bytes']==0 and step['stream_error']is None,'V2_WIRE_EMPTY_STDERR_AND_OWNED_CLEANUP')


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'V2_HOST398_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_V2_PREASSIGNED_HOST398',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,readonly_x86_test_workers_only=True,fixed_eight_executed=False,
        native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,old_tests_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);prior=r.compact.unpack(q.json(PREVIOUS))
        c.require(q.snapshots[PREVIOUS]['sha256']=='cb433c26468811ef62d02d1420ed7d5bdbc8b735057dca37fb3686f1ed589b06'
            and prior['state'].startswith('PASS_')and prior['cleanup']and prior['fresh_inputs']==prior['final_fresh_hashes']==193,
            'ORIGINAL396_PASS_AND_FAILURE_HISTORY_PRESERVED_NOT_REEXECUTED')
        for pin in prior['source_pins']:c.require(q.pin(pin['path'])==pin,'PREVIOUS_PRODUCTION_AND_VERIFICATION_SOURCES_UNCHANGED')
        for path in(DRIVER,PYTEST,PSTEST,'tools/p09/crossref_preassigned_host_protocol.py',
            'implementation/p09/tools/crossref-preassigned-host-channel.ps1','implementation/p09/tools/crossref-owned-active-source.ps1',
            'implementation/p09/tools/crossref-case-flow.ps1','implementation/p09/tools/crossref-host-channel.ps1'):q.pin(path)
        spec=importlib.util.spec_from_file_location('p09_v2_host_contracts',c.ROOT/PYTEST)
        models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        original=subject.sessions.startup.PreassignedNativeStartup
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();unittest.defaultTestLoader.loadTestsFromModule(models).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=16,errors=0,failures=0,skipped=0),'EXACT16_NEW_V2_PROTOCOL_SCOPE_MODELS_NO_SKIPS')
        c.require(subject.sessions.startup.PreassignedNativeStartup is original,'ORIGINAL_NATIVE_CONSTRUCTOR_RESTORED')
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        env=r.audit.environment();env['PYTHONDONTWRITEBYTECODE']='1'
        print(json.dumps(dict(state='V2_HOST398_PREFLIGHT',inputs=len(q.snapshots),new_python_models=16,powershell_models=8,wire_frames=152,actual_native=False)),flush=True)
        run_ps_models(guard,env,row);run_wire(guard,env,row,models)
        c.require(subject.sessions.startup.PreassignedNativeStartup is original,'ORIGINAL_NATIVE_CONSTRUCTOR_RESTORED_AFTER_WIRE_MODELS')
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_V2_SCOPE16_X86_MODELS8_ACTUAL_PIPE152_MODEL_OWNERS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='exact_existing_owner_lease_transfer_and_worker_case_factory_then_separate_native_session_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,AssertionError,subprocess.SubprocessError)as error:
        row.update(error_type=type(error).__name__,error_code=safe_code(error))
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes',
            'external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup','requests','admissions','stdout_bytes','stderr_bytes')},
                'cases':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
