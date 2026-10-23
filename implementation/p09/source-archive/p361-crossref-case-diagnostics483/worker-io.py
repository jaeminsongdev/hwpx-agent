"""Bounded trusted Native worker transport, with exact-handle cleanup, never kill.

This helper grants no execution authority. A private qualified handler owns all
Native starts. Pressure/deadline failures stop work, retain the same handles,
and wait for user-owned permission sessions to exit instead of restarting them.
"""
import hashlib,json,queue,re,threading,time
import crossref_session_qualification as closed


def require(ok,code):
    if not ok:raise ValueError('XREF_NATIVE_TRANSPORT_'+code)


def safe_failure(error):
    value=error.args[0]if error.args else None
    return dict(error_type=type(error).__name__ if type(error)in(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)else'OtherError',
        error_code=value if type(value)is str and re.fullmatch(r'(?:XREF_|STOP_|P09_XREF_)[A-Z0-9_]{1,140}',value)else
            'XREF_NATIVE_TRANSPORT_INTERRUPTED'if isinstance(error,KeyboardInterrupt)else'XREF_NATIVE_TRANSPORT_FAILURE_NO_RAW_VALUES')


def result_notice(result):
    # Only closed machine-readable diagnostics may be printed or persisted in
    # the early notice. Never echo arbitrary worker messages, paths or values.
    code=result.get('error_code');phase=result.get('phase');kind=result.get('error_kind');hresult=result.get('error_hresult')
    phases={'closed_mode','prewarm','host_ready','exact_existing_owner','host_exact_owner_admission',
        'verified_close','host_kernel_close','current_live_release','fixed_eight'}
    return dict(state='NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP',
        worker_failed_or_uncertain=result.get('state')in('session_worker_failed_or_uncertain','fixed_eight_callbacks_failed_or_partial','fixed_eight_worker_failed_or_uncertain'),
        worker_error_code=code if type(code)is str and re.fullmatch(r'P09_XREF_(?:BIND|ROT)_[A-Z0-9_]{1,120}',code)else None,
        worker_error_kind=kind if type(kind)is str and kind in('COMException','InvalidOperationException','OtherException')else None,
        worker_error_hresult=hresult if type(hresult)is str and re.fullmatch(r'0x[0-9A-F]{8}',hresult)else None,
        worker_phase=phase if type(phase)is str and phase in phases else None,
        cleanup_confirmed=False,rerun_forbidden=True,native_execution_authorized=False,P09_complete=False)


def wait_native_exit(current,windows,notify):
    if current is None or current.closed:return
    last=0.
    while True:
        status=0 if current.process is None else windows.k.WaitForSingleObject(current.process,0)
        require(status in(0,258),'CLEANUP_EXACT_HANDLE_WAIT_FAILED')
        signaled=status==0
        info=windows.accounting(current.owner_job.job)
        if signaled and info['active_processes']==0:current.close();return
        now=time.monotonic()
        if now-last>=15:
            notify(dict(state='WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL',process_id=current.pid,
                exact_process_signaled=signaled,owned_job_active_processes=info['active_processes'],
                work_continuing=False,cleanup_pending=True,manual_resolution_required=True,rerun_forbidden=True));last=now
        time.sleep(.2)


def run(guard,worker,reader,start,handler,result_schema,env,notify,record):
    events=queue.Queue(maxsize=8);stop=threading.Event();threads=[];started=last=time.monotonic()
    counts=dict(stdout_bytes=0,stderr_bytes=0,requests=0,stream_error=None)
    hashes={k:hashlib.sha256()for k in('stdout','stderr')};result=None;interruption=None
    record.update(cleanup=False,owned_job=worker.profile)

    def emit(kind,value=None):
        while not stop.is_set():
            try:events.put((kind,value),timeout=.1);return
            except queue.Full:pass
    def read(name):
        try:
            stream=getattr(worker,name)
            if name=='stdout':
                for _ in range(160):
                    line=stream.readline(4098)
                    if not line:emit('eof');return
                    data=line.encode();counts['stdout_bytes']+=len(data);hashes[name].update(data)
                    if len(data)>4097 or not line.endswith('\n')or counts['stdout_bytes']>32768:
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
        start(reader,env=env)
        threads=[threading.Thread(target=read,args=(name,),daemon=True)for name in('stdout','stderr')]
        for thread in threads:thread.start()
        worker.signal_readonly_target();ended=False
        while not ended:
            guard.check();account=worker.observe();require(counts['stream_error']is None,counts['stream_error']or'STREAM_ERROR')
            if time.monotonic()-last>=15:
                sample=guard.samples[-1];notify(dict(state='CURRENT_NATIVE_WORKER_ACTIVE',requests=counts['requests'],
                    elapsed_seconds=round(time.monotonic()-started,1),system_CPU=sample['system_cpu_percent'],
                    available_RAM_percent=sample['available_ram_percent'],job_private_percent=account['peak_job_private_percent']));last=time.monotonic()
            try:kind,line=events.get(timeout=.1)
            except queue.Empty:continue
            if kind=='eof':ended=True;continue
            require(kind=='line','BOUNDED_READER_FAILED')
            value=json.loads(line,object_pairs_hook=closed.descriptor.original.unique_pairs)
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
                require(result is None,'NO_REQUEST_AFTER_RESULT');reply=handler.handle(line);counts['requests']+=1
                require(type(reply)is str and len(reply.encode())<=4096,'FIXED_REPLY_BOUND')
                require(worker.stdin.write(reply+'\n')==len(reply)+1,'REPLY_WRITE');worker.stdin.flush()
        worker.wait(timeout=2);record.update(exit_code=worker.returncode,result=result)
        require(result is not None and counts['stderr_bytes']==0,'ONE_RESULT_AND_EMPTY_STDERR')
    except BaseException as error:
        if isinstance(error,KeyboardInterrupt):interruption=error
        record.setdefault('transport_failure',safe_failure(error))
        notify(dict(state='NATIVE_TRANSPORT_FAILED_BEFORE_CLEANUP',**record['transport_failure'],
            cleanup_confirmed=False,rerun_forbidden=True,native_execution_authorized=False,P09_complete=False))
        raise
    finally:
        record['cleanup_pending']=True
        if interruption is not None:
            # Ctrl+C during the retained-owner wait must not silently enter
            # that same unbounded wait again in finally. No kill/close/replay.
            record['cleanup_failure']=safe_failure(interruption)
            raise interruption
        try:wait_native_exit(handler.current_native(),guard.windows,notify)
        except BaseException as error:
            record['cleanup_failure']=safe_failure(error)
            raise
        if worker.process is not None:
            if not worker.stdin.closed:worker.stdin.close();worker.profile['input_eof_sent']=True
            while worker.poll()is None:
                if time.monotonic()-last>=15:notify(dict(state='WAITING_SAME_WORKER_EXIT_NO_FORCE_KILL'));last=time.monotonic()
                time.sleep(.2)
            worker.wait(timeout=0)
        stop.set()
        for thread in threads:thread.join(timeout=2)
        joined=all(not thread.is_alive()for thread in threads)
        try:handler.close()
        finally:
            try:worker.close()
            finally:record.update(**counts,cleanup=worker.profile['cleanup_confirmed']and joined,owned_job=worker.profile,
                cleanup_pending=not(worker.profile['cleanup_confirmed']and joined),
                io_threads_joined=joined,elapsed_seconds=round(time.monotonic()-started,3),
                stdout_sha256=hashes['stdout'].hexdigest(),stderr_sha256=hashes['stderr'].hexdigest(),handler_summary=handler.summary())
    require(record['cleanup'],'ALL_EXACT_NATIVE_WORKER_QUERY_JOB_AND_IO_CLEANUP')
    return result
