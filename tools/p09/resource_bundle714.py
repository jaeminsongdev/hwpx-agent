"""One original guard sampler + existing620 attribution, with lossless phase records.

No resource decisions/cadence/baseline change, additional thread/WMI/system sample,
or hot-host process query. Failed/original samples are never replaced with zeros.
"""
import json,math,time
import metadata_cpu_observer620 as attribution

SCHEMA='hwpx-agent.verification-phase-resource714/v1'
PHASES=frozenset(('startup','input_binding','model_checks','build','tests','readback',
    'binary_binding','final_binary','final_source','final_resource','backend_inspection'))
MAX_SAMPLES=4096
MAX_PHASES=256
MAX_BYTES=2*1024*1024

def require(ok,code):
    if not ok:raise ValueError('XREF_RESOURCE714_'+code)

class Attached:
    def __init__(self,guard,*,factory=attribution.Attached,clock=time.monotonic):
        require(not guard.samples and not getattr(guard.windows,'_resource_bundle714',False),'COLD_SINGLE_GUARD')
        self.guard,self.window,self.clock=guard,guard.windows,clock
        self.started=clock();require(type(self.started)in(int,float)and math.isfinite(self.started),'CLOCK')
        self.observer=factory(guard)
        self.prior_sample=self.window.sample
        self.current_phase='startup';self.phases=[dict(phase='startup',before_sample=0)]
        self.calls=0;self.last=self.started;self.closed=False
        def sample():
            # Original errors and resource values propagate before annotation.
            row=self.prior_sample()
            now=self.clock()
            require(type(now)in(int,float)and math.isfinite(now)and now>=self.last,'MONOTONIC_CLOCK')
            require(self.calls<MAX_SAMPLES,'SAMPLE_LIMIT')
            require(all(key not in row for key in('verification_phase714','resource_sequence714',
                'resource_elapsed714','resource_observation_interval714')),'UNMODIFIED_ROW')
            self.calls+=1
            row.update(verification_phase714=self.current_phase,resource_sequence714=self.calls,
                resource_elapsed714=now-self.started,resource_observation_interval714=now-self.last)
            self.last=now
            return row
        self.wrapper=sample;self.window.sample=sample;self.window._resource_bundle714=True
    def phase(self,name):
        require(not self.closed and name in PHASES,'CLOSED_PHASE_NAME')
        if self.current_phase==name:return
        require(len(self.phases)<MAX_PHASES,'PHASE_LIMIT')
        self.current_phase=name;self.phases.append(dict(phase=name,before_sample=self.calls))
    def close(self):
        if self.closed:return self.observer.probe.cleanup
        require(self.window.sample is self.wrapper,'SAME_INSTANCE_WRAPPER')
        self.window.sample=self.prior_sample
        try:return self.observer.close()
        finally:
            del self.window._resource_bundle714
            self.closed=True
    def packet(self):
        # Read the original completed guard rows, including later parent/job fields.
        # Shape interning preserves absent keys versus explicit None without loss.
        samples=self.guard.samples
        require(len(samples)==self.calls and len(samples)<=MAX_SAMPLES,'EXACT_ORIGINAL_SAMPLE_COUNT')
        shapes=[];indices={};rows=[]
        for i,row in enumerate(samples):
            require(row['resource_sequence714']==i+1 and row['verification_phase714']in PHASES,'SOURCE_ROW_SEQUENCE')
            keys=tuple(row)
            if keys not in indices:indices[keys]=len(shapes);shapes.append(list(keys))
            rows.append([indices[keys],[row[key]for key in keys]])
        decoded=[dict(zip(shapes[index],values,strict=True))for index,values in rows]
        require(decoded==samples,'LOSSLESS_ROUND_TRIP')
        value=dict(schema_version=SCHEMA,encoding='lossless_row_shapes_v1',shapes=shapes,rows=rows,
            phase_changes=list(self.phases),original_sampler_calls=self.calls,
            original_CPU_RAM_decisions_or_cadence_changed=False,
            additional_system_sample_thread_process_or_WMI=False,
            warning_optional_process_query_policy_changed=False,
            observer=self.observer.summary(),closed=self.closed,
            historical713_spike_phase_duration_or_cause_recovered=False,PC_freeze_resolved=False)
        raw=json.dumps(value,ensure_ascii=True,allow_nan=False,separators=(',',':')).encode()
        require(len(raw)<=MAX_BYTES,'LOSSLESS_OUTPUT_LIMIT')
        return value
