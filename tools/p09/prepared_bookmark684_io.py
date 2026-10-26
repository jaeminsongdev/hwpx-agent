"""Non-Native candidate603: unblock failed request transport BEFORE exact-handle cleanup.
Not wired into consumed001..009, not an executable/Native/retry/timeout-policy permit.
Original result-retaining-owner policy, guard calls, byte/frame limits and no-kill stay intact.
"""
import hashlib,json,queue,re,threading,time
import crossref_session_qualification as closed
from crossref_native_worker_io import wait_native_exit
from prepared_bookmark684_notice import result_notice

SELF='tools/p09/prepared_bookmark684_io.py'
SITES={'accept_case112_current_epoch','locked_runtime_inputs','audit_evidence_io',
    'conservative_maintenance','crossref_native_worker_io603','crossref_native_worker_io',
    'crossref_qualified_batch','crossref_preassigned_host_protocol','crossref_preassigned_session_scope',
    'crossref_session_qualification','crossref_owned_host_process','crossref_native_startup'}
STEPS={'prepare_slot','create_save_session','source_open','source_bind','opened_save','opened_probe','sdk_insert',
    'saved_save','saved_probe','save_session_close','create_reopen_session','fresh_saved_open','reopened_save',
    'reopened_probe','reopen_session_close','final_source_check'}

def require(ok,code):
    if not ok:raise ValueError('XREF_NATIVE_TRANSPORT_'+code)

def safe_failure(error):
    value=error.args[0]if error.args else None
    code=value if type(value)is str and re.fullmatch(
        r'(?:XREF_|STOP_|P09_XREF_|P58_|P206_LOCK_|CURRENT_EPOCH_ACCEPT_)[A-Z0-9_]{1,140}',value)else(
        'XREF_NATIVE_TRANSPORT_INTERRUPTED'if isinstance(error,KeyboardInterrupt)else'XREF_NATIVE_TRANSPORT_FAILURE_NO_RAW_VALUES')
    kind=type(error).__name__ if type(error)in(ValueError,OSError,KeyError,TypeError,AttributeError,
        KeyboardInterrupt,json.JSONDecodeError)else'OtherError'
    row=dict(error_type=kind,error_code=code);trace=error.__traceback__;site=None;limit=0
    while trace is not None and limit<64:
        module=trace.tb_frame.f_globals.get('__name__');name=trace.tb_frame.f_code.co_name
        if module in SITES and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,63}',name)and 0<trace.tb_lineno<100000:
            site=dict(module=module,function=name,line=trace.tb_lineno)
        trace=trace.tb_next;limit+=1
    if site is not None:row['error_site']=site
    return row

def request_context(value):
    # This is last-received diagnostic context, never a request/ownership permit.
    row={}
    for key,maximum in(('sequence',256),('case_index',8)):
        item=value.get(key)
        if type(item)is int and 1<=item<=maximum:row[key]=item
    op=value.get('operation')
    if type(op)is str and op in('ready','admit_owner','checkpoint','finish','closed','failed'):row['operation']=op
    step=value.get('step')
    if type(step)is str and step in STEPS:row['step']=step
    return row

def snapshot(record,counts,hashes,handler,started,joined):
    record.update(**dict(counts),elapsed_seconds=round(time.monotonic()-started,3),
        stdout_sha256=hashes['stdout'].copy().hexdigest(),stderr_sha256=hashes['stderr'].copy().hexdigest(),
        diagnostic_snapshot_complete=joined)
    try:record['handler_summary']=handler.summary()
    except BaseException as error:
        if isinstance(error,(SystemExit,KeyboardInterrupt)):raise
        record.setdefault('handler_summary_failure',safe_failure(error))

def run(guard,worker,reader,start,handler,result_schema,env,notify,record):
    events=queue.Queue(maxsize=8);stop=threading.Event();threads=[];started=last=time.monotonic()
    counts=dict(stdout_bytes=0,stderr_bytes=0,requests=0,stream_error=None)
    hashes={k:hashlib.sha256()for k in('stdout','stderr')};result=None;interruption=None;primary=None;phase='not_started';last_request=None
    record.update(cleanup=False,owned_job=worker.profile)

    def emit(kind,value=None):
        while not stop.is_set():
            try:events.put((kind,value),timeout=.1);return
            except queue.Full:pass
    def read(name):
        try:
            stream=getattr(worker,name)
            if name=='stdout':
                # Eight cases: READY + 8*(16 checkpoints+2 admissions+2 closes+finish)
                # + RESULT = 170 frames, then one bounded EOF read.
                for _ in range(171):
                    line=stream.readline(4098)
                    if not line:emit('eof');return
                    data=line.encode();counts['stdout_bytes']+=len(data);hashes[name].update(data)
                    if len(data)>4097 or not line.endswith('\n')or counts['stdout_bytes']>65536:
                        counts['stream_error']='XREF_NATIVE_TRANSPORT_STDOUT_BOUND';emit('error');return
                    emit('line',line.rstrip('\r\n'))
                counts['stream_error']='XREF_NATIVE_TRANSPORT_FRAME_COUNT_BOUND';emit('error')
            else:
                while True:
                    part=stream.read(512)
                    if not part:return
                    data=part.encode();counts['stderr_bytes']+=len(data);hashes[name].update(data)
                    if counts['stderr_bytes']>4096:counts['stream_error']='XREF_NATIVE_TRANSPORT_STDERR_BOUND';emit('error');return
        except(OSError,ValueError,UnicodeError):counts['stream_error']='XREF_NATIVE_TRANSPORT_PIPE_IO';emit('error')

    try:
        phase='start';start(reader,env=env)
        threads=[threading.Thread(target=read,args=(name,),daemon=True)for name in('stdout','stderr')]
        for thread in threads:thread.start()
        phase='signal';worker.signal_readonly_target();ended=False
        while not ended:
            phase='guard_check';guard.check();phase='worker_observe';account=worker.observe();require(counts['stream_error']is None,counts['stream_error']or'STREAM_ERROR')
            if time.monotonic()-last>=15:
                sample=guard.samples[-1];notify(dict(state='CURRENT_NATIVE_WORKER_ACTIVE',requests=counts['requests'],
                    elapsed_seconds=round(time.monotonic()-started,1),system_CPU=sample['system_cpu_percent'],
                    available_RAM_percent=sample['available_ram_percent'],job_private_percent=account['peak_job_private_percent']));last=time.monotonic()
            try:kind,line=events.get(timeout=.1)
            except queue.Empty:continue
            if kind=='eof':ended=True;continue
            require(kind=='line','BOUNDED_READER_FAILED')
            phase='decode_frame';value=json.loads(line,object_pairs_hook=closed.descriptor.original.unique_pairs)
            require(type(value)is dict,'FRAME_OBJECT_REQUIRED')
            if value.get('schema_version')==result_schema:
                require(result is None,'ONE_RESULT');result=value
                record['result']=result
                record['handler_summary']=handler.summary()
                # Publish BEFORE any wait for the same native process. The
                # failed result must survive pending cleanup and interruption.
                notify(result_notice(result))
                # A failed worker can retain RCWs until EOF. Observe its same
                # Native handle/tree before EOF, never retry Close/Quit or launch.
                if result.get('retained_live_or_uncertain_owners',0):
                    wait_native_exit(handler.current_native(),guard.windows,notify)
                    if not worker.stdin.closed:worker.stdin.close();worker.profile['input_eof_sent']=True
            else:
                require(result is None,'NO_REQUEST_AFTER_RESULT');last_request=request_context(value)
                phase='handle_request';reply=handler.handle(line);counts['requests']+=1
                phase='validate_reply';require(type(reply)is str and len(reply.encode())<=4096,'FIXED_REPLY_BOUND')
                phase='write_reply';require(worker.stdin.write(reply+'\n')==len(reply)+1,'REPLY_WRITE');worker.stdin.flush()
        phase='worker_wait';worker.wait(timeout=2);record.update(exit_code=worker.returncode,result=result)
        phase='validate_result';require(result is not None and counts['stderr_bytes']==0,'ONE_RESULT_AND_EMPTY_STDERR')
    except BaseException as error:
        primary=error
        if isinstance(error,KeyboardInterrupt):interruption=error
        record.setdefault('transport_failure',dict(safe_failure(error),transport_phase=phase,last_received_request=last_request))
        snapshot(record,counts,hashes,handler,started,False)
        notify(dict(state='NATIVE_TRANSPORT_FAILED_BEFORE_CLEANUP',**record['transport_failure'],
            cleanup_confirmed=False,rerun_forbidden=True,native_execution_authorized=False,P09_complete=False))
        raise
    finally:
        record['cleanup_pending']=True;finished=False;joined=None
        try:
            if interruption is not None:
                record['cleanup_failure']=safe_failure(interruption)
                raise interruption
            # Only a failed transport with NO worker result may be stuck waiting
            # for our reply. EOF drives its original fail-closed owned cleanup.
            # A returned result retaining uncertain owners keeps the old policy.
            if primary is not None and result is None and worker.process is not None:
                if not worker.stdin.closed:
                    worker.stdin.close();worker.profile['input_eof_sent']=True
                record['abort_eof_sent_before_native_wait']=True
            wait_native_exit(handler.current_native(),guard.windows,notify)
            if worker.process is not None:
                if not worker.stdin.closed:
                    worker.stdin.close();worker.profile['input_eof_sent']=True
                while worker.poll()is None:
                    if time.monotonic()-last>=15:
                        notify(dict(state='WAITING_SAME_WORKER_EXIT_NO_FORCE_KILL',work_continuing=False,
                            cleanup_pending=True,manual_resolution_required=True,rerun_forbidden=True))
                        last=time.monotonic()
                    time.sleep(.2)
                worker.wait(timeout=0)
            handler.close()
            # Drain/stop readers before the original worker closes their pipes.
            stop.set()
            for thread in threads:thread.join(timeout=2)
            joined=all(not thread.is_alive()for thread in threads)
            require(joined,'IO_THREADS_RETAINED_NO_FORCED_PIPE_CLOSE')
            worker.close();finished=True
        except BaseException as cleanup_error:
            record['cleanup_failure']=safe_failure(cleanup_error)
            # Do not overwrite the original timeout/protocol error with a later
            # cleanup error. An explicit user interrupt still takes precedence.
            if primary is None or isinstance(cleanup_error,KeyboardInterrupt):raise
        finally:
            stop.set()
            if joined is None:
                for thread in threads:thread.join(timeout=2)
                joined=all(not thread.is_alive()for thread in threads)
            snapshot(record,counts,hashes,handler,started,joined)
            confirmed=finished and worker.profile['cleanup_confirmed']and joined and 'handler_summary_failure'not in record
            record.update(cleanup=confirmed,owned_job=worker.profile,cleanup_pending=not confirmed,
                io_threads_joined=joined)
    require(record['cleanup'],'ALL_EXACT_NATIVE_WORKER_QUERY_JOB_AND_IO_CLEANUP')
    return result
