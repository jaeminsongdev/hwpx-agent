"""Small sole-observer real-PDH access/cost qualification, NOT product PASS."""
import json
from pathlib import Path
import time

import accept_case112_current_epoch as a
import serial_cpu_attribution as p

SELF="tools/p09/probe_serial_cpu_attribution.py"
OUTPUT="implementation/p09/evidence/p09-361-serial-cpu-attribution-probe001.v1.json"


def main():
    destination=a.c.ROOT/OUTPUT
    a.require(not destination.exists(),"IMMUTABLE_PROBE_OUTPUT")
    guard=a.Guard();probe=None;q=None;rows=[];ready=False
    try:
        guard.acquire();q=a.AcceptanceReader(a.c.ROOT,guard.check)
        for name in (SELF,p.SELF,p.TEST,a.SELF):q.pin(name)
        probe=p.Probe(guard.windows.processors)
        for _ in range(4):
            time.sleep(.5);guard.check(force=True)
            row=probe.sample();row['original_resource_sample_time_utc']=guard.samples[-1]['time_utc'];rows.append(row)
        q.finish();guard.check(force=True)
        def valid(row):
            values=row.get('values')
            return row.get('available') is True and type(values) is dict and all(
                type(values.get(name)) is dict and values[name]['pid_stable'] is True
                and values[name]['machine_cpu_percent'] is not None for name in ('MsMpEng','System'))
        ready=sum(valid(row) for row in rows)>=2 and probe.disabled_reason is None
    finally:
        if probe is not None:probe.close()
        guard.close()
    a.require(probe is not None and probe.cleanup and guard.cleanup,'PROBE_CLEANUP')
    row=dict(schema_version='hwpx-agent.p09-serial-cpu-attribution-probe/v1',
        state='PASS_LIGHT_COUNTER_ACCESS_AND_COST_NOT_VERIFIER_CAUSAL_OR_PRODUCT' if ready else 'COUNTER_NOT_READY_NOT_PRODUCT_OR_GATE',
        ready_for_separately_reviewed_original_observer_integration=ready,probe=probe.summary(),observations=rows,
        fresh_input_pins=list(q.snapshots.values()),read_passes=q.read_passes,final_fresh_hashes=q.final_fresh_hashes,
        original_resource_samples=guard.samples,cleanup_confirmed=True,parallel_observer=False,
        product_or_Native_input_frame_executed=False,queue_advance=0,accepted_cases=106,next_case=113,
        P09_gate='OPEN',full249_current_qualified=False,PC_freeze_cause_or_improvement_established=False,
        original_K32_decisions_unchanged=True,extra_PDH_queries_explicit=True,OS_Defender_settings_changed=False)
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,ensure_ascii=True,indent=2)
    print(json.dumps(dict(state=row['state'],ready=ready,maximum_probe_sample_seconds=probe.maximum_latency,
        total_probe_sample_seconds=probe.total_latency,cleanup=True,product=False)))
    return 0 if ready else 2


if __name__=='__main__':raise SystemExit(main())
