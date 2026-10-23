"""Same post-terminal Job drain pattern as preparation_drain, for the fixed stdlib-only Python child.

The original live-child refusal and authoritative close stay unchanged. No creation, resume, force kill or resource admission in cleanup.
"""
import json,time
import crossref_preassigned_readonly as original
class DrainedReadonlyProcess(original.PreassignedReadonlyProcess):
    def close(self):
        if self.closed or self.process is None:return super().close()
        if self.windows.k.WaitForSingleObject(self.process,0)!=0:return super().close()
        job=self.envelope.job;started=last=time.monotonic();observations=0;prefix=[]
        while True:
            # The SAME terminal process handle remains held; never reacquire/reuse a PID or create another child.
            original.require(self.windows.k.WaitForSingleObject(self.process,0)==0,'SAME_TERMINAL_READONLY_HANDLE')
            info=self.windows.accounting(job);observations+=1
            if len(prefix)<8:prefix.append(info['active_processes'])
            self.profile['post_terminal_tree_drain']=dict(observations=observations,initial_active_prefix=prefix[:],
                final_active=info['active_processes'],elapsed_seconds=round(time.monotonic()-started,3),
                same_job_observed=True,same_terminal_process_handle_observed=True,forced_termination_invoked=False)
            if info['active_processes']==0:break
            if time.monotonic()-last>=15:
                print(json.dumps(dict(stage='waiting_same_terminal_readonly_job_no_force_close',active_processes=info['active_processes'],
                    elapsed_seconds=round(time.monotonic()-started,1))),flush=True);last=time.monotonic()
            time.sleep(.05)
        return super().close()
