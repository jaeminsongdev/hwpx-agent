"""P175 pure parser allocation hint; whole preimages and original-input binding."""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import audit_writer_case_cost as prior

d=prior.d; c=d.c; s=d.s
SELF='tools/p09/xml_initial_capacity_binding.py'
SOURCE='crates/hwpx-package/src/safe_xml.rs'
ARCHIVE='implementation/p09/source-archive/p09-175-pre-xml-capacity-r53/preimages.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
PARENT=dict(path='implementation/p09/evidence/p09-174-writer-case-cost.terminal-audit-run01.v1.json',
    bytes=335042,sha256='1b86f44c399e59204edd8badd3393c87a6da07a4db600b685ff22c509a87ec8f')
MARKER='\n// P175 initial-capacity parity and sparse/dense allocation regression oracles.\n'
OLD_ENTRY='''    pub fn parse(bytes: &[u8], limits: SafeXmlLimits) -> Result<Self, SafeXmlError> {'''
NEW_ENTRY='''    pub fn parse(bytes: &[u8], limits: SafeXmlLimits) -> Result<Self, SafeXmlError> {
        // A reservation hint, not an admission limit. Long text/attributes can
        // have very few events; never reserve the byte-derived event ceiling
        // up front. Original checked growth and every parser guard remain.
        Self::parse_with_capacity_hint(bytes, limits, 256)
    }

    fn parse_with_capacity_hint(
        bytes: &[u8],
        limits: SafeXmlLimits,
        capacity_hint: usize,
    ) -> Result<Self, SafeXmlError> {'''
OLD_CAP='''            .min(bytes.len().saturating_div(2).saturating_add(1));'''
NEW_CAP='''            .min(bytes.len().saturating_div(2).saturating_add(1))
            .min(capacity_hint);'''

def require(ok,code):d.require(ok,'XML_CAPACITY_'+code)

def parent_scope(row):
    require(row['state']==prior.PASS and row['source_closing_exact'] and row['diagnostic_only']
        and row['contract_tests_passed']==58 and row['current_Rust_input_count']==785
        and row['protected_EXE_inputs_exact']==66 and row['completed_case_observations']==50
        and row['original_stop_reason']=='STOP_DURATION_LIMIT' and row['owned_job_final']['active_processes']==0
        and row['current_compiled249_qualified'] and not row['full249_current_qualified']
        and not row['signed16_current_qualified'] and not row['product_complete']
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'PARENT_STOP_NOT_PASS')
    expected=s.inputs.inventory(row['bound_input_pins'])
    require(row['IO']['finished'] and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==len(expected)
        and sum(n.endswith('.exe') for n in expected)==66,'WHOLE_PARENT')
    return expected

def preimage(archive,name):
    rows=[x for x in archive['files'] if x['path']==name];require(len(rows)==1,'ONE_PREIMAGE')
    item=rows[0];raw=base64.b64decode(item['base64'],validate=True)
    require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'RAW_PREIMAGE')
    return item,raw

def inverse(current,old):
    current=current.replace('\r\n','\n');old=old.replace('\r\n','\n')
    require(current.count(MARKER)==1,'ONE_TEST_EXTENSION');core,tests=current.split(MARKER)
    require(tests.count('#[test]')==3 and 'assert_eq!(originals, 36)' in tests
        and 'usize::MAX' in tests and 'assert_eq!(new, old)' in tests
        and '100_000' in tests and '256' in tests and '512' in tests,'THREE_ORACLES')
    for added,original in ((NEW_ENTRY,OLD_ENTRY),(NEW_CAP,OLD_CAP)):
        require(core.count(added)==1,'ONE_DELTA');core=core.replace(added,original,1)
    require(core==old,'WHOLE_ORIGINAL_CORE_AND_TESTS_EXACT');return True

def bind(q,resources):
    require(q.pin(PARENT['path'])==PARENT,'PARENT_PIN');expected=parent_scope(q.json(PARENT['path']))
    archive=q.json(ARCHIVE)
    require(archive['state']=='PASS_P175_WHOLE_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE'
        and archive['baseline_closing_pin']==PARENT and len(archive['files'])==3,'ARCHIVE_SCOPE')
    item,old=preimage(archive,SOURCE)
    require({k:item[k] for k in ('path','bytes','sha256')}==expected[SOURCE],'OLD_SOURCE')
    inverse(q.text(SOURCE),old.decode('utf-8'));expected[SOURCE]=q.pin(SOURCE)
    for name,pin in expected.items():require(q.pin(name)==pin,'WHOLE_PARENT_EXCEPT_ONE_DELTA')
    rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
    names,modules=d.d.p.source_scope(q,expected)
    require(len(names)==249 and len(modules)==59,'ORIGINAL249_59')
    for name in (SELF,ARCHIVE,PARENT['path']):expected[name]=q.pin(name)
    return expected,names,modules

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archive',action='store_true',required=True);parser.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');destination=s.scoped_path(ARCHIVE,fresh=True)
    resources=s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',baseline_closing_pin=PARENT,goal_status='active',product_complete=False,
        P09_gate='OPEN',actual_child_or_new_thread_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        with patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
                patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
                patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')):
            q.pin(SELF);require(q.pin(PARENT['path'])==PARENT,'PARENT_PIN')
            expected=parent_scope(q.json(PARENT['path']));files=[]
            for name in (SOURCE,*DOCS):
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_BYTES')
                if name==SOURCE:require(pin==expected[SOURCE],'CURRENT_SOURCE')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
            q.finish();out.update(state='PASS_P175_WHOLE_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=d.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
