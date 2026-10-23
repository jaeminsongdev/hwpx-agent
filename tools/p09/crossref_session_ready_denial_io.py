"""Actual worker kernel binding and genuine root-Job denial, with a Native constructor trap.

No Native can start even if the expected parent condition changes. Same owned
worker/Job/query handles are retained to terminal cleanup; never force-killed.
"""
import hashlib,json,queue,threading,time
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_session_qualification as protocol
import crossref_session_worker as transport


def run(guard,reader,shell_pin,env,row):
    c=r.c;owned=session=None;threads=[];events=queue.Queue(maxsize=4);stop=threading.Event();started=last=time.monotonic()
    step=dict(stage='actual_session_worker_kernel_binding_and_root_denial_no_native',cleanup=False,requests=0)
    row['steps'].append(step);stats=dict(stdout_bytes=0,stderr_bytes=0,stream_error=None)
    out_hash=hashlib.sha256();err_hash=hashlib.sha256()

    def emit(kind,value=None):
        while not stop.is_set():
            try:events.put((kind,value),timeout=.1);return
            except queue.Full:pass

    def stdout_io():
        try:
            for _ in range(4):
                line=owned.stdout.readline(4098)
                if not line:emit('eof');return
                data=line.encode();stats['stdout_bytes']+=len(data);out_hash.update(data)
                if len(data)>4097 or not line.endswith('\n')or stats['stdout_bytes']>32768:
                    stats['stream_error']='SESSION_DENIAL_STDOUT_BOUND';emit('error');return
                emit('line',line.rstrip('\r\n'))
            stats['stream_error']='SESSION_DENIAL_TOTAL_FRAME_BOUND';emit('error')
        except(OSError,ValueError,UnicodeError):stats['stream_error']='SESSION_DENIAL_STDOUT_IO';emit('error')

    def stderr_io():
        try:
            while True:
                part=owned.stderr.read(512)
                if not part:return
                data=part.encode();stats['stderr_bytes']+=len(data);err_hash.update(data)
                if stats['stderr_bytes']>4096:stats['stream_error']='SESSION_DENIAL_STDERR_BOUND';emit('error');return
        except(OSError,ValueError,UnicodeError):stats['stream_error']='SESSION_DENIAL_STDERR_IO';emit('error')

    original_backend=protocol.startup.PreassignedNativeStartup
    try:
        parent=protocol.owned.read_parent_cpu(guard.windows)
        c.require(parent['job_present']is True,'SESSION_DENIAL_REQUIRES_CURRENT_NONJOBLESS_PARENT_NO_NATIVE_TEST')
        step['current_parent_job_observation']=parent
        owned=transport.SessionWorker(guard);step['owned_job']=owned.profile
        owned.start_session_worker(reader,env=env)
        session=protocol.SessionQualifier(guard,owned,lambda:(_ for _ in()).throw(ValueError('SESSION_DENIAL_NATIVE_IMAGE_MUST_NOT_BE_REQUESTED')),shell_pin)
        threads=[threading.Thread(target=stdout_io,daemon=True),threading.Thread(target=stderr_io,daemon=True)]
        for thread in threads:thread.start()
        # The genuine original parent denial must happen BEFORE this trap.
        # It is impossible for this verification to create a Native process.
        with patch.object(protocol.startup,'PreassignedNativeStartup',side_effect=ValueError('SESSION_DENIAL_NATIVE_CONSTRUCTOR_TRAP'))as trap:
            owned.signal_readonly_target();result=None;ended=False
            while not ended:
                guard.check();account=owned.observe();c.require(time.monotonic()-started<90,'STOP_SESSION_DENIAL_READONLY_DEADLINE')
                c.require(stats['stream_error']is None,stats['stream_error']or'SESSION_DENIAL_IO')
                if time.monotonic()-last>=15:
                    sample=guard.samples[-1];print(json.dumps(dict(stage=step['stage'],requests=step['requests'],elapsed=round(time.monotonic()-started,1),
                        system_CPU=sample['system_cpu_percent'],available_RAM_percent=sample['available_ram_percent'],
                        job_private_percent=account['peak_job_private_percent'])),flush=True);last=time.monotonic()
                try:kind,line=events.get(timeout=.1)
                except queue.Empty:continue
                if kind=='eof':ended=True;continue
                c.require(kind=='line','SESSION_DENIAL_READER_FAILED')
                value=json.loads(line,object_pairs_hook=protocol.descriptor.original.unique_pairs)
                if value.get('schema_version')==protocol.REQUEST:
                    c.require(result is None,'SESSION_DENIAL_NO_REQUEST_AFTER_RESULT')
                    reply=session.respond(line);decoded=json.loads(reply);step['requests']+=1
                    if step['requests']==1:
                        c.require(not decoded['acknowledged']and decoded['owner_descriptor']is None
                            and decoded['error_code']=='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE'
                            and session.current is None and session.worker_lease is not None,'GENUINE_PARENT_JOB_DENIAL_AFTER_EXACT_WORKER_BIND_BEFORE_NATIVE')
                        step['actual_worker_kernel_binding']=session.worker_lease.observe()
                    else:c.require(step['requests']==2 and value['operation']=='failed'and decoded['acknowledged'],'EXACT_ONE_FAILED_FINISH_AFTER_PARENT_DENIAL')
                    c.require(owned.stdin.write(reply+'\n')==len(reply)+1,'SESSION_DENIAL_REPLY_WRITE');owned.stdin.flush()
                else:
                    c.require(result is None and step['requests']==2,'SESSION_DENIAL_ONE_RESULT_AFTER_TWO_MESSAGES');result=value
            owned.wait(timeout=2);step.update(exit_code=owned.returncode,result=result,native_constructor_trap_calls=trap.call_count)
            c.require(trap.call_count==0 and session.current is None and session.primary_error=='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE'
                and session.finished and session.stopped and not session.lifecycle_candidate,'ACTUAL_ORIGINAL_PARENT_DENIAL_NOT_TRAP_DENIAL_OR_NATIVE_EXECUTION')
            c.require(step['exit_code']==2 and result is not None and result['state']=='session_worker_failed_or_uncertain'
                and result['phase']=='host_ready'and not result['COM_owner_observed']and result['cleanup']['remaining_owned_process_count']==-1
                and not result['document_opened_or_saved']and not result['fixed_eight_executed']and not result['native_startup_qualified'],
                'ACTUAL_WORKER_DENIAL_RESULT_NOT_COM_DOCUMENT_OR_SESSION_SUCCESS')
    finally:
        c.require(protocol.startup.PreassignedNativeStartup is original_backend,'ORIGINAL_NATIVE_CONSTRUCTOR_RESTORED_AFTER_DENIAL_TRAP')
        if owned is not None:
            if owned.process is not None:
                if not owned.stdin.closed:owned.stdin.close();owned.profile['input_eof_sent']=True
                while owned.poll()is None:
                    if time.monotonic()-last>=15:
                        print(json.dumps(dict(stage='waiting_same_session_denial_worker_cleanup_no_force_kill',elapsed=round(time.monotonic()-started,1))),flush=True);last=time.monotonic()
                    time.sleep(.2)
                owned.wait(timeout=0)
            stop.set()
            for thread in threads:thread.join(timeout=2)
            joined=all(not thread.is_alive()for thread in threads)
            if session is not None:session.close();step['session_summary']=session.summary()
            try:owned.close()
            finally:step.update(cleanup=owned.profile['cleanup_confirmed']and joined,owned_job=owned.profile,io_threads_joined=joined)
        step.update(**stats,stdout_sha256=out_hash.hexdigest(),stderr_sha256=err_hash.hexdigest(),elapsed_seconds=round(time.monotonic()-started,3))
    c.require(step['cleanup']and step['stderr_bytes']==0 and step['stream_error']is None,'SESSION_DENIAL_ALL_QUERY_IO_AND_JOB_HANDLES_CLOSED_WITHOUT_KILL')
