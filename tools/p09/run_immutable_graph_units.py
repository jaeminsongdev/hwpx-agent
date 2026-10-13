"""Current domain graph15 unit tests in NEW target, original owned resource caps."""
import argparse
import json
import subprocess
import sys
from unittest.mock import patch
import conservative_maintenance as c

SELF='tools/p09/run_immutable_graph_units.py'
TARGET=c.ROOT/'target/p09-156-immutable-graph'
TASK='p156-immutable-graph-tests'
ARGS=['test','-p','domain-ir','--test','document_graph']


def worker():
    with patch.object(c,'TASKS',{TASK:ARGS}),patch.object(c,'TARGET',TARGET):return c.worker(TASK)


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=int,choices=range(1,100),required=True);args=p.parse_args()
    c.require(c.Path.cwd().resolve()==c.ROOT,'P156_REPOSITORY_CWD')
    destination=c.ROOT/f'implementation/p09/evidence/p09-156-immutable-graph.units-run{args.run:02}.v1.json'
    c.require(not destination.exists(),'P156_FRESH_RECEIPT')
    # Separate target prevents overwriting any old canonical test/runtime EXE.
    sources=list(c.SOURCES)+[SELF,'implementation/p09/source-archive/p09-156-pre-immutable-graph-digest-r37/source-preimages.v1.json']
    sources.extend(p.relative_to(c.ROOT).as_posix() for p in (c.ROOT/'crates/domain-ir').rglob('*.rs'))
    dump=json.dump;accepted=False
    def write(row,stream,**kw):
        nonlocal accepted
        accepted=row['state']=='PASS_SCOPED_NOT_GATE' and row.get('tests_passed')==15
        if row['state']=='PASS_SCOPED_NOT_GATE':
            row['state']='PASS_CURRENT_IMMUTABLE_GRAPH_UNITS15_ONLY_NOT_FULL249_OR_GATE' if accepted else 'STOPPED_NOT_ACCEPTED'
            if not accepted:row['stop_reason']='P156_EXACT_DOMAIN15_REQUIRED'
        row.update(schema_version='hwpx-agent.p09-immutable-graph-digest-units/v1',isolated_target=str(TARGET.relative_to(c.ROOT)),
            original_domain_cases=10,new_cache_regression_cases=5,full249_current_qualified=False,signed16_current_qualified=False,
            PC_freeze_resolved=False,old_full_EXEs_not_selected=True,full_product_performance_improvement_measured=False,
            baseline_archive='implementation/p09/source-archive/p09-156-pre-immutable-graph-digest-r37/source-preimages.v1.json')
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{TASK:ARGS}),patch.object(c,'TARGET',TARGET), \
            patch.object(c,'SOURCES',list(dict.fromkeys(sources))),patch.object(json,'dump',write):code=c.run(TASK,destination,180)
    return 0 if accepted else code


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:
            c.require(sys.argv[3]==TASK,'P156_CLOSED_WORKER_TASK');raise SystemExit(worker())
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError):
        print('P156_CLOSED_FAILURE');raise SystemExit(2) from None
