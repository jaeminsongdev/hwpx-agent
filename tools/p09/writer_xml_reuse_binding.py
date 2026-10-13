"""P168 single Writer Rust delta, exact P167 closure, preserved whole preimages."""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import audit_current_signed_stage_cost as prior

p=prior.p
s=p.s
c=p.c
SELF='tools/p09/writer_xml_reuse_binding.py'
SOURCE='crates/hwpx-package/src/writer.rs'
ARCHIVE='implementation/p09/source-archive/p09-168-pre-writer-xml-reuse-r48/preimages.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
PARENT=dict(path='implementation/p09/evidence/p09-167-current-signed-stage-cost.terminal-audit-run01.v1.json',
    bytes=274673,sha256='84fc2be417a14ffe817fa57b81d9a5bb2bc5a7e4bd8151a1720f30adb1d5085e')
MARKER='\n// P168 writer call-local XML regression oracles; no product authority.\n'
OLD_PRESERVATION='''    let preservation = PreservationReport::build_with_graph_limits_and_profile(
        &mut reader,
        &graph,
        graph_limits,
        preservation_profile,
    )?;'''
NEW_PRESERVATION='''    // One archive validation only. Keep fresh bounded reads, CRC/size/profile
    // and whole-byte comparisons; never retain source or authorization across calls.
    let mut documents = crate::call_local_xml::CallLocalXmlDocuments::default();
    let preservation = PreservationReport::build_with_call_local_xml(
        &mut reader,
        &graph,
        graph_limits,
        preservation_profile,
        &mut documents,
    )?;'''
OLD_INDEX='''    let index =
        IdIndex::build_with_graph_limits(&mut reader, &graph, graph_limits, profile, id_limits)?;'''
NEW_INDEX='''    let index = IdIndex::build_with_call_local_xml(
        &mut reader,
        &graph,
        graph_limits,
        profile,
        id_limits,
        &mut documents,
    )?;'''

def require(ok,code):prior.require(ok,'WRITER_'+code)

def parent_scope(row):
    require(row['state']==prior.PASS and row['source_closing_exact'] and row['contract_tests_passed']==130
        and row['current_Rust_input_count']==785 and row['protected_EXE_inputs_exact']==64
        and row['original_run_state']=='STOPPED_NOT_ACCEPTED'
        and row['original_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU' and not row['selected_body_finished']
        and row['signed_stage_cost']['fully_observed_case_sequences']==3
        and row['current_compiled249_qualified'] and not row['full249_current_qualified']
        and not row['signed16_current_qualified'] and not row['product_complete']
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'P167_STOP_NOT_PASS')
    return s.inputs.inventory(row['bound_input_pins'],1320)

def inverse(current,old):
    current=current.replace('\r\n','\n');old=old.replace('\r\n','\n')
    require(current.count(MARKER)==1,'ONE_TEST_EXTENSION')
    core,tests=current.split(MARKER)
    require(tests.count('#[test]')==3 and 'assert_eq!(count, 36)' in tests
        and 'assert_eq!(*plain_reads.borrow(), *shared_reads.borrow())' in tests
        and 'validate_archive_original' in tests and 'callback_called.get()' in tests,'THREE_REGRESSIONS')
    for added,original in ((NEW_PRESERVATION,OLD_PRESERVATION),(NEW_INDEX,OLD_INDEX),
        ('#[cfg_attr(test, derive(Debug, Eq, PartialEq))]\nstruct ValidationCounts','struct ValidationCounts')):
        require(core.count(added)==1,'ONE_CLOSED_DELTA_PATTERN');core=core.replace(added,original,1)
    require(core==old,'WHOLE_ORIGINAL_CORE_EXACT')
    return True

def preimage(archive,n):
    rows=[item for item in archive['files'] if item['path']==n]
    require(len(rows)==1,'ONE_PREIMAGE')
    item=rows[0];raw=base64.b64decode(item['base64'],validate=True)
    require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'WHOLE_PREIMAGE')
    return item,raw

def bind(q,resources):
    require(q.pin(PARENT['path'])==PARENT,'PARENT_PIN')
    expected=parent_scope(q.json(PARENT['path']))
    archive=q.json(ARCHIVE)
    require(archive['state']=='PASS_P168_WHOLE_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE'
        and archive['baseline_closing_pin']==PARENT and len(archive['files'])==3,'ARCHIVE_SCOPE')
    item,old=preimage(archive,SOURCE)
    require({k:item[k] for k in ('path','bytes','sha256')}==expected[SOURCE],'PARENT_SOURCE_PREIMAGE')
    inverse(q.text(SOURCE),old.decode('utf-8'));expected[SOURCE]=q.pin(SOURCE)
    for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_PARENT_EXCEPT_ONE_WRITER_DELTA')
    rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
    names,modules=p.source_scope(q,expected)
    require(len(names)==249 and len(modules)==59,'ORIGINAL249_59')
    for n in (SELF,ARCHIVE,PARENT['path']):expected[n]=q.pin(n)
    return expected,names,modules

def archive_main():
    require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(ARCHIVE,fresh=True)
    resources=s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',baseline_closing_pin=PARENT,goal_status='active',
        product_complete=False,P09_gate='OPEN',actual_child_or_new_thread_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        with patch('subprocess.Popen',side_effect=AssertionError('P168_ARCHIVE_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P168_ARCHIVE_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P168_ARCHIVE_THREAD_FORBIDDEN')):
            q.pin(SELF);require(q.pin(PARENT['path'])==PARENT,'PARENT_PIN')
            expected=parent_scope(q.json(PARENT['path']));files=[]
            for n in (SOURCE,*DOCS):
                raw=q.text(n).encode();pin=q.reader.snapshots[n]
                require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'SOURCE_BYTES')
                if n==SOURCE:require(pin==expected[SOURCE],'ORIGINAL_WRITER')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
            q.finish();out.update(state='PASS_P168_WHOLE_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=prior.d.original.closed_error(e)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',action='store_true',required=True)
    parser.parse_args();raise SystemExit(archive_main())
