"""P195 independent fresh closing + explicit alias, without repeating case004.

과거 실패파일은 덮어쓰지 않는다. 원 whole/terminal/cleanup 검사를 유지하며
binary 읽기만 2.5->1.5MiB/s로 낮춘다. 600초 scope와 포화 STOP은 그대로다.
"""
import argparse
import io
import json
import math
import sys
import unittest
from unittest.mock import patch

import review_pending_r07_closing as pending
import observe_shared_metadata_recheck as observation
import weighted_audit_io as weighted

b=pending.batch;c=b.c;v=b.v;core=b.core
SELF='tools/p09/recover_r07_case004_closing.py'
TEST='tools/p09/tests/test_r07_independent_closing.py'
SOURCES=(SELF,TEST,observation.SELF,observation.TEST,pending.SELF,pending.TEST)
CASE=pending.CASE;STOP=pending.STOP
REVIEW=dict(path=pending.DEST,bytes=16265,
    sha256='a0789196efcba9e241ec77f2deff0227b427a17a3d601a462a732dfc8dcf5dd9')
BINARY_RATE=3*1024*1024//2
RAW_READER=b.run.pressure.PressureReader
RAW_RESOURCES=b.run.pressure.observation.ObservedResources
RAW_SCOPE=b.s.scoped_path
RAW_PROGRESS=core.progress
RAW_CONTRACTS=b.contracts
RAW_DUMP=json.dump
RAW_ERROR=b.run.original.closed_error


def require(ok,code):c.require(ok,'P195_'+code)


def paths(mode,number):
    require(mode in ('light','recover','plan') and type(number) is int and 1<=number<=99,'MODE_RUN')
    name='independent-case004-recovery-closing' if mode=='recover' else 'case004-recovery-'+mode
    return f'implementation/p09/evidence/p09-195-{name}-run{number:02d}.v1.json'


def estimate(expected):
    binary=sum(p['bytes'] for n,p in expected.items() if n.endswith('.exe'))
    other=sum(p['bytes'] for n,p in expected.items() if not n.endswith('.exe'))
    floor=2*binary/BINARY_RATE+2*other/weighted.OTHER_RATE
    with_margin=floor+32*1024*1024/weighted.OTHER_RATE+40
    require(math.isfinite(with_margin) and with_margin<600,'RATE_CANNOT_FIT_ORIGINAL_SCOPE')
    return dict(binary_bytes_per_whole_pass=binary,other_bytes_per_whole_pass=other,
        predicted_two_pass_rate_lower_bound_seconds=floor,
        estimated_seconds_with_metadata_allowance_and_margin=with_margin,
        unchanged_maximum_scope_seconds=600,prediction_is_not_completion_guarantee=True)


class Pacer(weighted.WeightedPacer):
    def select(self,name):
        super().select(name)
        if self.kind=='binary':self.rate=BINARY_RATE


class Reader(RAW_READER):
    def __init__(self,resources,context):
        self.context=context;super().__init__(resources);context.reader=self.reader
        self.reader.pacer=Pacer()
        for name in SOURCES:self.pin(name)
        for pin in (CASE,STOP,REVIEW,b.BASE_PREP):require(self.pin(pin['path'])==pin,'IMMUTABLE_INPUT')
        review=self.json(REVIEW['path']);inputs=v.pins(review['bound_input_pins'])
        require(review['state']=='PASS_PENDING_CASE004_AND_PRESERVED_STOP_PLAN_ONLY_NOT_CLOSING_OR_GATE'
            and review['contract_tests_passed']==154 and review['pending_review_contract_tests_passed']==4
            and review['resource_stop_reason'] is None and review['resource_watcher_cleanup_confirmed']
            and review['IO']['finished'],'PRIOR_REVIEW')
        for name in (pending.SELF,pending.TEST):require(self.pin(name)==inputs[name],'PRIOR_REVIEW_SOURCE')
        self.budget=estimate(v.pins(self.json(b.BASE_PREP['path'])['whole_inputs']))
    def pin(self,name):
        with self.context.scope('metadata_hash'):return super().pin(name)
    def json(self,name):
        with self.context.scope('metadata_read_parse'):return super().json(name)
    def text(self,name):
        with self.context.scope('document_read'):return super().text(name)
    def finish(self):
        with self.context.scope('final_fresh_hash'):return super().finish()
    def summary(self):
        row=super().summary()
        row.update(read_rate_policy='P195_binary1p5_other4_MiB_per_second',
            read_rates_by_kind=dict(binary=BINARY_RATE,other=weighted.OTHER_RATE),
            existing_pressure_and_guards_and_deadline_preserved=True,rate_budget=self.budget)
        return row


def factory(owner,context,registry,readers,*args,**kw):
    if registry and owner is registry[0]:
        require(not args and not kw and not readers,'ONE_ACTUAL_READER')
        reader=Reader(owner,context);readers.append(reader);return reader
    return RAW_READER(owner,*args,**kw)


def new_contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_r07_independent_closing')
    with patch('subprocess.Popen',side_effect=AssertionError('P195_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P195_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P195_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==12 and not checked.skipped,'CONTRACT12')
    return dict(independent_closing_contract_tests_passed=12)


def contracts(context):
    with context.scope('contract_tests'):
        out=RAW_CONTRACTS();out.update(observation.new_contracts());out.update(new_contracts());return out


def redirect(name,actual_destination,**kw):
    if name==STOP['path'] and kw.get('fresh') is True:return RAW_SCOPE(actual_destination,**kw)
    return RAW_SCOPE(name,**kw)


def attach(out,owners,readers):
    if out['state']==v.CLOSING_PASS:require(len(owners)==len(readers)==1,'RECOVERY_OWNER_READER')
    # Reader 생성/입력검사 실패도 원 실패 receipt에 남긴다. 관측 누락은 0이 아니다.
    out.update(recovery_publisher='P195_independent_closing',original_failed_closing_reference=STOP['path'],
        original_failed_closing_pin=STOP,candidate_case_pin=CASE,
        recovery_controller_input_pins=[readers[0].reader.snapshots[n] for n in SOURCES] if readers else [],
        recovery_metadata_observation=observation.summary(owners[0]) if owners else None,
        candidate_body_reexecuted=False,additional_product_child_executed=False,
        original_failed_file_not_replaced=True)


def recover(number):
    destination=paths('recover',number);RAW_SCOPE(destination,fresh=True)
    context=observation.Context();owners=[];readers=[];diagnostic={}
    def resources():
        require(not owners,'ONE_ACTUAL_OWNER');owner=observation.Resources(context);owners.append(owner);return owner
    def dump(out,stream,**kw):
        if isinstance(out,dict) and out.get('schema_version')==v.CLOSING_SCHEMA and str(getattr(stream,'name',''))==str(c.ROOT/destination):
            attach(out,owners,readers)
            if diagnostic:out['closed_error_diagnostic']=diagnostic
        return RAW_DUMP(out,stream,**kw)
    def error_code(error):
        import traceback
        allowed={c.Path(n).name for n in (*SOURCES,b.SELF,'tools/p09/weighted_audit_io.py')}
        diagnostic.update(exception_type=type(error).__name__,exception_values_or_locals_saved=False,
            public_code_frames=[dict(module=c.Path(f.filename).name,function=f.name,line=f.lineno)
                for f in traceback.extract_tb(error.__traceback__)[-8:] if c.Path(f.filename).name in allowed])
        return RAW_ERROR(error)
    with patch.object(b.s,'scoped_path',lambda name,**kw:redirect(name,destination,**kw)), \
            patch.object(b.run.pressure.observation,'ObservedResources',resources), \
            patch.object(b.run.pressure,'PressureReader',lambda owner,*a,**kw:factory(owner,context,owners,readers,*a,**kw)), \
            patch.object(b,'contracts',lambda:contracts(context)),patch.object(json,'dump',dump), \
            patch.object(b.run.original,'closed_error',error_code):
        return b.close(5)


def validate_recovery(doc,case,expected,names,exe):
    require(doc.get('recovery_publisher')=='P195_independent_closing'
        and doc['original_failed_closing_reference']==STOP['path']
        and doc['original_failed_closing_pin']==STOP and doc['candidate_case_pin']==CASE
        and doc['candidate_body_reexecuted'] is False and doc['additional_product_child_executed'] is False
        and doc['original_failed_file_not_replaced'] is True,'EXPLICIT_ORIGINAL_ALIAS')
    require(doc['IO']['finished'] and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
        and doc['IO']['maximum_scope_seconds']==600
        and doc['IO']['read_rates_by_kind']==dict(binary=BINARY_RATE,other=weighted.OTHER_RATE)
        and doc['accepted_new_case_count']==1 and doc['whole_original68_EXE_and_Rust785_closed'] is True,
        'COMPLETE_FRESH_RECOVERY')
    require(set(v.pins(doc['recovery_controller_input_pins']))==set(SOURCES),'CONTROLLER_BINDING')
    v.accept_case(case,names[3],v.identity(names,expected,exe),doc,expected,CASE)
    engine=v.pins(doc['supplemental_scheduler_before'])
    require(doc['supplemental_scheduler_before']==doc['supplemental_scheduler_after'],'SUPPLEMENTAL_BOUNDARY')
    b.validate_supplement(case,expected,engine)


def progress(q,names,expected,exe,recovery_path,extra=()):
    require(all(key!=STOP['path'] for key,_ in extra),'NO_ALIAS_OVERRIDE')
    require(q.pin(CASE['path'])==CASE and q.pin(STOP['path'])==STOP,'PRESERVED_ORIGINAL_BYTES')
    doc=q.json(recovery_path);case=q.json(CASE['path']);validate_recovery(doc,case,expected,names,exe)
    for name,pin in v.pins(doc['recovery_controller_input_pins']).items():
        require(q.pin(name)==pin,'LIVE_RECOVERY_CONTROLLER')
    return RAW_PROGRESS(q,names,expected,exe,extra=(*extra,(STOP['path'],doc)))


def review_mode(mode,number,recovery_number):
    destination=RAW_SCOPE(paths(mode,number),fresh=True);context=observation.Context()
    owner=observation.Resources(context);q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**core.flags(),actual_product_child_executed=False,
        new_whole_source_audit_executed=False,original_failed_closing_not_overwritten=True)
    try:
        owner.admit();q=Reader(owner,context);out.update(contracts(context))
        expected,names,exe=b.baseline(q)
        if mode=='light':
            status=RAW_PROGRESS(q,names,expected,exe)
            pending.validate_pending(q.json(CASE['path']),q.json(STOP['path']),status)
        else:
            path=paths('recover',recovery_number);status=progress(q,names,expected,exe,path)
            require(status['accepted_individual_cases']==4 and status['remaining_individual_cases']==245
                and status['successful_candidates_requiring_separate_closing']==0
                and status['next_index']==5,'RECOVERED_SKIP4_NEXT5')
            out['independent_recovery_closing_pin']=q.reader.snapshots[path]
        q.finish();out.update(state='PASS_P195_CONTRACTS_AND_PENDING_PLAN_ONLY_NOT_RECOVERY' if mode=='light'
            else 'PASS_P195_INDEPENDENT_CLOSING_ALIAS_AND_SKIP4_NEXT5_PLAN_ONLY_NOT_RUNTIME_OR_GATE',plan=status)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:RAW_DUMP(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','independent_closing_contract_tests_passed',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','recover','plan'),required=True)
    ap.add_argument('--run',type=int,required=True);ap.add_argument('--recovery-run',type=int,default=1)
    args=ap.parse_args();require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    return recover(args.run) if args.mode=='recover' else review_mode(args.mode,args.run,args.recovery_run)


if __name__=='__main__':raise SystemExit(main())
