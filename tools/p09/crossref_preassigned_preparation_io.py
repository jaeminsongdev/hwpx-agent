"""Two real preparation frames only; bounded IO threads, sole original sampler.

No force kill. On failure EOF is sent and the SAME handle is observed to terminal
before closing the original non-killing one-percent Job. Never launch/retry Native.
"""
import hashlib,json,queue,re,threading,time
import named_style_verification_runtime as r
import crossref_preassigned_preparation as subject
import crossref_preassigned_preparation_drain as drain


def run(guard,reader,env,row):
    c=r.c;owned=None;threads=[];events=queue.Queue(maxsize=4);stop=threading.Event();started=last=time.monotonic()
    step=dict(stage='actual_non_killing_one_percent_preparation_worker_v2_denial',cleanup=False,requests=0)
    row['steps'].append(step);stats=dict(stdout_bytes=0,stderr_bytes=0,stream_error=None)
    out_hash=hashlib.sha256();err_hash=hashlib.sha256();stderr_parts=[];protocol=subject.DenialProtocol()

    def emit(kind,value=None):
        while not stop.is_set():
            try:events.put((kind,value),timeout=.1);return
            except queue.Full:pass

    def stdout_io():
        try:
            for _ in range(4):
                line=owned.stdout.readline(4098)
                if not line:emit('eof');return
                data=line.encode('utf-8');out_hash.update(data);stats['stdout_bytes']+=len(data)
                if len(data)>4097 or not line.endswith('\n')or stats['stdout_bytes']>32768:
                    stats['stream_error']='PREPARATION_STDOUT_FRAME_OR_DIAGNOSTIC_LIMIT';emit('error');return
                emit('line',line.rstrip('\r\n'))
            stats['stream_error']='PREPARATION_TOTAL_FRAME_LIMIT';emit('error')
        except(OSError,ValueError,UnicodeError):stats['stream_error']='PREPARATION_STDOUT_IO_FAILED';emit('error')

    def stderr_io():
        try:
            while True:
                part=owned.stderr.read(512)
                if not part:return
                data=part.encode('utf-8');err_hash.update(data);stats['stderr_bytes']+=len(data)
                if stats['stderr_bytes']>4096:stats['stream_error']='PREPARATION_STDERR_LIMIT';emit('error');return
                stderr_parts.append(part)
        except(OSError,ValueError,UnicodeError):stats['stream_error']='PREPARATION_STDERR_IO_FAILED';emit('error')

    try:
        owned=drain.DrainedPreparationWorker(guard.windows,guard.check)
        step['owned_job']=owned.profile
        owned.start_preparation(reader,env=env)
        owned.profile['bootstrap_pid']=owned.process.pid
        threads=[threading.Thread(target=stdout_io,daemon=True),threading.Thread(target=stderr_io,daemon=True)]
        for thread in threads:thread.start()
        owned.signal_readonly_target();ended=False;result=None
        while not ended:
            guard.check();account=owned.observe();c.require(time.monotonic()-started<90,'STOP_PREPARATION_READONLY_DEADLINE')
            c.require(stats['stream_error']is None,stats['stream_error']or'PREPARATION_STREAM_ERROR')
            if time.monotonic()-last>=15:
                sample=guard.samples[-1];print(json.dumps(dict(stage=step['stage'],requests=step['requests'],elapsed=round(time.monotonic()-started,1),
                    system_CPU=sample['system_cpu_percent'],available_RAM_percent=sample['available_ram_percent'],
                    job_private_percent=account['peak_job_private_percent'])),flush=True);last=time.monotonic()
            try:kind,line=events.get(timeout=.1)
            except queue.Empty:continue
            if kind=='eof':ended=True;continue
            c.require(kind=='line','PREPARATION_BOUNDED_READER_FAILED')
            value=json.loads(line,object_pairs_hook=subject.wire.original.unique_pairs)
            if value.get('schema_version')==subject.wire.REQUEST:
                c.require(result is None,'PREPARATION_NO_REQUEST_AFTER_SUMMARY')
                reply=protocol.respond(line);step['requests']+=1
                c.require(owned.stdin.write(reply+'\n')==len(reply)+1,'PREPARATION_REPLY_WRITE');owned.stdin.flush()
            else:
                c.require(result is None and protocol.sequence==2,'PREPARATION_SINGLE_SUMMARY_AFTER_TWO_REQUESTS');result=value
        owned.wait(timeout=2);owned.observe();step.update(exit_code=owned.returncode,result=result)
        c.require(step['exit_code']==0 and step['requests']==2 and result is not None
            and result['state']=='closed_preassigned_worker_controller_prepared_not_native'
            and result['planned_cases']==8 and result['callback_cases_entered']==1 and result['host_messages']==2
            and result['stopped_phase']=='prepare_slot'and result['retained_case_states']==1 and result['first_reply_checked']
            and result['adapter_and_window_identity_prewarmed']and result['original_probe_lease_held']and result['probe_lease_closed']
            and not result['positive_reply_blocked']and not result['native_directory_or_owner_or_trace_created']
            and not result['actual_Hangul_ROT_or_COM']and not result['native_execution_authorized']and not result['native_startup_qualified'],
            'ACTUAL_NEW_CONTROLLER_DENIAL_BEFORE_NATIVE_SLOT_AND_CLEANUP_NOT_NATIVE_QUALIFICATION')
    finally:
        # This is not a cancellation/retry of Native. The fixed target is denied
        # before the first file mutation; EOF lets its original cleanup finish.
        if owned is not None:
            if owned.process is not None:
                if not owned.stdin.closed:owned.stdin.close();owned.profile['input_eof_sent']=True
                while owned.poll()is None:
                    if time.monotonic()-last>=15:
                        print(json.dumps(dict(stage='waiting_same_preparation_handle_cleanup_no_force_kill',elapsed=round(time.monotonic()-started,1))),flush=True);last=time.monotonic()
                    time.sleep(.2)
                owned.wait(timeout=0)
            stop.set()
            for thread in threads:thread.join(timeout=2)
            joined=all(not thread.is_alive()for thread in threads)
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed']and joined,owned_job=owned.profile,io_threads_joined=joined)
        step.update(**stats,stdout_sha256=out_hash.hexdigest(),stderr_sha256=err_hash.hexdigest(),elapsed_seconds=round(time.monotonic()-started,3),
            safe_error_codes=re.findall(r'(?m)^Error: (P09_XREF_[A-Z0-9_]{1,120})\r?$', ''.join(stderr_parts)))
    c.require(step['cleanup']and step['stderr_bytes']==0 and step['stream_error']is None,'PREPARATION_EMPTY_STDERR_AND_NON_KILLING_OWNED_CLEANUP')
