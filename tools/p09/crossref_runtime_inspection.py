"""Bounded actual host/protocol/parent-observation composition; no native provider.

Both supported reply probes are readonly. Even an erroneous positive first ACK
is rejected inside the fixed worker before native slot/session creation.
"""
import hashlib
import json
import queue
import threading
import time

from crossref_owned_host_process import OwnedHostProcess
from crossref_native_host_channel import HostProtocol,REQUEST
from crossref_producer_records import ParentObservations,current_inventory

RESULT='hwpx-agent.private.crossref-runtime-inspection/v1'


def require(ok,code):
    if not ok:raise ValueError('XREF_RUNTIME_INSPECTION_'+code)


class ClosedInspectionScope:
    """Real closed policy, never a mock that claims native resource admission."""
    def __init__(self,checkpoint,reply_probe):
        self.check=checkpoint;self.reply_probe=reply_probe;self.profiles=[];self.current=None
        self.checkpoint_calls=0;self.admission_calls=0;self.finish_calls=0
    def checkpoint(self,index,step):
        self.check();self.checkpoint_calls+=1
        require(index==1 and step=='prepare_slot','NO_LATER_WORK')
        if self.reply_probe=='positive_transport_guard':return
        raise ValueError('STOP_XREF_NATIVE_STARTUP_UNQUALIFIED')
    def admit_owner(self,*args):
        self.admission_calls+=1
        raise ValueError('STOP_XREF_NATIVE_PROVIDER_ABSENT')
    def finish(self,index,status):
        # No pressure check: the failed-case finish must remain reachable.
        require(index==1 and status=='failed' and self.current is None,'CLOSED_FINISH_ONLY')
        self.finish_calls+=1


class BoundedInspectionPipes:
    """IO-drain threads only, not resource samplers; no raw persistent logs."""
    def __init__(self,process):
        self.events=queue.Queue(maxsize=16);self.errors=[];self.stderr=bytearray();self.stdout_bytes=0
        self.threads=[threading.Thread(target=self._out,args=(process.stdout,),daemon=True),
            threading.Thread(target=self._err,args=(process.stderr,),daemon=True)]
        for thread in self.threads:thread.start()
    def _out(self,stream):
        try:
            while True:
                line=stream.readline(16385)
                if not line:break
                size=len(line.encode('utf-8'));self.stdout_bytes+=size
                require(line.endswith('\n') and size<=16384 and self.stdout_bytes<=32768,'STDOUT_LIMIT')
                self.events.put(line.rstrip('\r\n'),timeout=1)
        except (ValueError,OSError,UnicodeError,queue.Full):self.errors.append('XREF_RUNTIME_INSPECTION_STDOUT_FAILED')
        finally:
            try:self.events.put(None,timeout=1)
            except queue.Full:self.errors.append('XREF_RUNTIME_INSPECTION_EVENT_QUEUE_FULL')
    def _err(self,stream):
        try:
            while True:
                chunk=stream.read(1024)
                if not chunk:break
                require(len(self.stderr)+len(chunk.encode('utf-8'))<=4096,'STDERR_LIMIT')
                self.stderr.extend(chunk.encode('utf-8'))
        except (ValueError,OSError,UnicodeError):self.errors.append('XREF_RUNTIME_INSPECTION_STDERR_FAILED')
    def join(self):
        for thread in self.threads:thread.join(timeout=2)
        require(not any(thread.is_alive() for thread in self.threads),'IO_DRAIN_NOT_TERMINAL')


def wait_empty_owned_job(process):
    # Observe this exact still-open Job only. Timeout retains it; no kill/restart.
    end=time.monotonic()+2
    while process.windows.accounting(process.job)['active_processes']:
        require(time.monotonic()<end,'OWNED_TREE_EXIT_NOT_YET_CONFIRMED')
        time.sleep(.05)


def inspect_connection(guard,reader,reply_probe='negative'):
    require(type(reply_probe) is str and reply_probe in ('negative','positive_transport_guard'),'FIXED_READONLY_PROBE')
    scope=ClosedInspectionScope(guard.check,reply_probe)
    observations=ParentObservations(scope,reader)
    protocol=HostProtocol(observations.checkpoint,observations.admit_owner,observations.finish)
    process=OwnedHostProcess(guard.windows,guard.check)
    pipes=None;target=None;request_count=0;maximum_active=0
    try:
        process.start_waiting(reader,role='runtime_connection')
        process.signal_readonly_target()
        pipes=BoundedInspectionPipes(process)
        deadline=time.monotonic()+60  # Fixed readonly inspection only; not reusable for native prompts.
        while True:
            guard.check();info=process.observe();maximum_active=max(maximum_active,info['active_processes'])
            require(time.monotonic()<deadline,'READONLY_OBSERVATION_DEADLINE')
            require(not pipes.errors,'BOUNDED_PIPE_READ_FAILED')
            try:line=pipes.events.get(timeout=.5)
            except queue.Empty:continue
            if line is None:break
            packet=json.loads(line)
            require(type(packet) is dict,'CHILD_PACKET_OBJECT')
            if packet.get('schema_version')==REQUEST:
                request_count+=1;require(request_count<=2,'INSPECTION_REQUEST_COUNT')
                answer=protocol.respond(line)
                require(process.stdin.write(answer+'\n')==len(answer)+1,'REPLY_WRITE')
                process.stdin.flush()
            else:
                require(target is None and packet.get('schema_version')==RESULT,'ONE_CLOSED_CHILD_RESULT')
                target=packet
        process.stdin.close();process.wait(timeout=2);pipes.join();wait_empty_owned_job(process)
        require(process.returncode==0 and not pipes.stderr and not pipes.errors and target is not None,'READONLY_CHILD_FAILED')
        require(target['state']=='closed_fixed_eight_runtime_inspected_not_native' and
            target['actual_Hangul_or_COM'] is False and target['native_directories_created'] is False and
            target['native_execution_authorized'] is False and target['native_provenance_qualified'] is False,
            'CLOSED_CHILD_RESULT_NOT_NATIVE')
        require(target['first_reply_checked'] is True and
            target['positive_or_invalid_reply_blocked'] is (reply_probe=='positive_transport_guard'),'TRANSPORT_DENIAL_GUARD')
        require(request_count==2 and scope.checkpoint_calls==1 and scope.admission_calls==0 and scope.finish_calls==1 and
            len(observations.records)==1 and observations.records[0]['finish_status']=='failed' and
            not observations.records[0]['owner_admissions'] and not observations.records[0]['artifacts'],
            'ACTUAL_PROTOCOL_AND_PARENT_OBSERVATION_CLOSED')
        inventory=current_inventory(reader)
        require(all(row['state']=='NOT_RUN' for row in inventory['cases']),'NATIVE_INVENTORY_ABSENT')
        process.close()
        return dict(state='actual_closed_host_batch_protocol_parent_composition_not_native',reply_probe=reply_probe,
            request_count=request_count,worker_result=target,protocol=protocol.summary(),
            parent_records=observations.records,host_profile=process.profile,maximum_active_owned_processes=maximum_active,
            stdout_bytes=pipes.stdout_bytes,stderr_bytes=len(pipes.stderr),stderr_sha256=hashlib.sha256(pipes.stderr).hexdigest(),
            io_threads_joined=True,actual_fixed_inventory=inventory,actual_Hangul_or_COM=False,
            native_provenance_qualified=False,native_execution_authorized=False,
            complete_native_guard_integration_qualified=False,p09_complete=False)
    except BaseException as error:
        # EOF gives this readonly worker a graceful exit; never restart or force-kill it.
        if process.process is not None and not process.stdin.closed:process.stdin.close()
        if process.process is None or process.poll() is not None:
            if pipes is not None:pipes.join()
            process.close()
        # A live/observation-timeout handle is retained for inspection, not called terminal.
        error.owned_host_process=process;error.inspection_pipes=pipes
        raise
