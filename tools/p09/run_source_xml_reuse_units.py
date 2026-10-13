"""P161 actual all68 package LIB units, existing isolated target; owned caps."""
import argparse
import json
import subprocess
import sys
from unittest.mock import patch
import source_xml_reuse_binding as b

c=b.p.c
SELF='tools/p09/run_source_xml_reuse_units.py'
TARGET=c.ROOT/'target/p09-156-immutable-graph'
TASK='p161-source-xml-reuse-tests'
ARGS=['test','-p','hwpx-package','--lib',*[v for entry in b.s.profile.CONFIG for v in ('--config',entry)]]

def worker(task):
    b.require(task==TASK,'WORKER_TASK')
    with patch.object(c,'TARGET',TARGET),patch.object(c,'TASKS',{TASK:ARGS}):return c.worker(task)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,required=True,choices=range(1,100));a=parser.parse_args()
    b.require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=b.s.scoped_path(f'implementation/p09/evidence/p09-161-source-xml-reuse.units-run{a.run:02}.v1.json',fresh=True)
    b.require(TARGET.is_dir() and not TARGET.is_symlink() and not TARGET.is_junction(),'EXISTING_TARGET')
    b.require(not list((TARGET/'debug/deps').glob('hwpx_package-*.exe')),'NO_OLD_PACKAGE_LIB_EXE')
    resources=b.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=b.s.LiveSQLReader(resources);expected,names,modules=b.bind(q,resources)
        expected[SELF]=q.pin(SELF);q.finish()
    finally:b.require(b.s.finish_watcher(resources,out),'BINDING_CLEANUP')
    raw_pins=c.pins;raw_admitted=c.admitted_count;dump=json.dump;accepted=False;post_hash=False
    def admitted(row,count):return raw_admitted(row,count) if row['available_ram_percent']>=15 else 0
    def pins(checkpoint=None):
        nonlocal post_hash
        actual=raw_pins(checkpoint);seen={p['path']:p for p in actual}
        b.require(all(seen.get(n)==pin for n,pin in expected.items()),'WHOLE_FRESH_INPUT')
        if not post_hash:
            stable=0;windows=c.Windows()
            for _ in range(6):
                c.time.sleep(.5);row=windows.sample();stable=admitted(row,stable)
                b.require(row['system_cpu_percent']<98,'DEFERRED_ALREADY_SATURATED_SYSTEM')
                if stable>=2:post_hash=True;break
            b.require(post_hash,'DEFERRED_COMPILER_HEADROOM15')
        return actual
    def write(row,stream,**kw):
        nonlocal accepted
        accepted=row['state']=='PASS_SCOPED_NOT_GATE' and row.get('tests_passed')==68
        if row['state']=='PASS_SCOPED_NOT_GATE':
            row['state']='PASS_SOURCE_XML_REUSE_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE' if accepted else 'STOPPED_NOT_ACCEPTED'
            if not accepted:row['stop_reason']='P161_EXACT_LIB68_REQUIRED'
        row.update(current_Rust_input_count=785,original_package_lib_cases=64,new_source_xml_regression_cases=4,
            isolated_target=TARGET.relative_to(c.ROOT).as_posix(),existing_target_cache_reused=True,
            baseline_closing_pin=b.PARENT,baseline_archive=b.ARCHIVE,whole_original_core_inverse_exact=True,
            source_test_names=names,source_module_instances=modules,test_package_profile_config=list(b.s.profile.CONFIG),
            compiler_admission_RAM_percent=15,post_hash_compiler_admission_revalidated=post_hash,
            current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
            PC_freeze_resolved=False,full_product_performance_improvement_measured=False,remaining_non_permission_work_units=76)
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{TASK:ARGS}),patch.object(c,'TARGET',TARGET), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins), \
            patch.object(c,'admitted_count',admitted),patch.object(json,'dump',write):code=c.run(TASK,destination,600)
    return 0 if accepted else code

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=b.prior.full.s.original.closed_error(e))))
        raise SystemExit(2) from None
