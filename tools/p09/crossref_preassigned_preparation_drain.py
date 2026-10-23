"""Wait for the SAME non-killing preparation Job tree after its bootstrap exits.

Bootstrap exit is not an empty-tree proof. Original close remains authoritative;
no force kill, retry, policy weakening, pressure admission or handle abandonment.
"""
import json,time
import crossref_preassigned_preparation as subject


class DrainedPreparationWorker(subject.PreparationWorker):
    def close(self):
        if self.closed:return super().close()
        # Preserve the original live-worker refusal. Only post-terminal tree
        # cleanup is waited here; this does not wait/retry/start Native work.
        if self.process is not None and self.process.poll()is None:return super().close()
        if self.job is not None:
            started=last=time.monotonic();observations=0;prefix=[]
            while True:
                info=self.windows.accounting(self.job);self.profile['last_job_accounting']=info;observations+=1
                if len(prefix)<8:prefix.append(info['active_processes'])
                self.profile['post_terminal_tree_drain']=dict(observations=observations,initial_active_prefix=prefix[:],
                    final_active=info['active_processes'],elapsed_seconds=round(time.monotonic()-started,3),
                    same_job_observed=True,forced_termination_invoked=False)
                if info['active_processes']==0:break
                if time.monotonic()-last>=15:
                    print(json.dumps(dict(stage='waiting_same_preparation_job_tree_no_force_close',active_processes=info['active_processes'],
                        elapsed_seconds=round(time.monotonic()-started,1))),flush=True);last=time.monotonic()
                time.sleep(.05)
        return super().close()
