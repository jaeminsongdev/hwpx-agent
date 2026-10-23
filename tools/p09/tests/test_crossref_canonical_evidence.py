"""Only new in-memory canonical evidence contracts; no native files/suite replay."""
import ast
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import crossref_canonical_evidence as canonical
from test_crossref_producer_records import model_case,owners_for


def fixture(index,owners=None):
    trace,parent,pins=model_case(index,owners)
    evidence=[];identities=[]
    for offset,session in enumerate(trace['sessions']):
        compat=copy.deepcopy(session['process'])
        identity=dict(compat,created_at_utc=compat['created_at_utc'][:-2]+str(6+offset)+'Z')
        identities.append(identity)
        observation=dict(schema_version='hwpx-agent.private.crossref-dual-owner-identity/v1',
            compatibility_kind='original_p58_identity',compatibility_identity=compat,kernel_identity=identity,
            kernel_creation_filetime_100ns=str(canonical.dual.native.creation_ticks(identity['created_at_utc'])),
            kernel_process_image=canonical.dual.native.EXECUTABLE,kernel_window_verified=True,
            kernel_before_after_same_handle_equal=True,compatibility_fresh_check_returned=True,
            kernel_creation_not_derived_from_cim=True,native_provenance_qualified=False,
            native_execution_authorized=False,p09_complete=False)
        evidence.append(dict(session_label=session['label'],evidence=dict(observation=observation,
            channel_message_attempted=True,channel_message_returned=True,error_code=None,
            native_provenance_qualified=False,native_execution_authorized=False,p09_complete=False)))
        parent['owner_admissions'][offset]['identity']=copy.deepcopy(identity)
    for offset,event in enumerate(parent['artifacts']):
        event['identity']=copy.deepcopy(identities[1 if event['stage']=='reopened' else 0])
    raw=json.dumps(trace,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    sidecar=dict(schema_version=canonical.SCHEMA,case_id=canonical.original.case_id(index),
        state='owner_identity_sidecar_unqualified',original_trace=canonical.raw_pin(index,raw),admissions=evidence,
        native_provenance_qualified=False,native_execution_authorized=False,p09_complete=False)
    return raw,sidecar,parent,pins


class MemoryReader:
    def __init__(self,values):self.values=values;self.snapshots={};self.calls=[];self.maximum_parse_bytes=2097152
    def _read(self,path,parse=False):
        self.calls.append((path,self.maximum_parse_bytes))
        value=self.values[path]
        if len(value)>self.maximum_parse_bytes:raise ValueError('MODEL_PARSE_BUDGET')
        import hashlib
        return dict(path=path,bytes=len(value),sha256=hashlib.sha256(value).hexdigest()),bytearray(value)
    def _bind(self,path,pin):self.snapshots[path]=pin


class CanonicalEvidenceContracts(unittest.TestCase):
    def test_01_all_eight_models_keep_raw_trace_and_original_checks_once(self):
        cases=[fixture(i) for i in range(1,9)];original=copy.deepcopy(cases)
        with patch.object(canonical.original,'compare_completed_case',wraps=canonical.original.compare_completed_case) as check:
            result=canonical.compare_whole_batch(*[list(v) for v in zip(*cases,strict=True)])
            self.assertEqual(check.call_count,8)
        self.assertEqual(cases,original);self.assertEqual(len(result['cases']),8)
        self.assertFalse(result['native_provenance_qualified'] or result['canonical_native_admission_qualified'])
        self.assertFalse(result['original_traces_rewritten'])
        self.assertTrue(all(r['projected_identity_fields']==7 for r in result['cases']))

    def test_02_exact_raw_bytes_hash_path_and_case_binding(self):
        for kind in ('bytes','hash','path','case'):
            raw,sidecar,parent,pins=fixture(1)
            if kind=='bytes':raw+=b' '
            elif kind=='hash':sidecar['original_trace']['sha256']='0'*64
            elif kind=='path':sidecar['original_trace']['path']=canonical.trace_path(2)
            else:sidecar['case_id']=canonical.original.case_id(2)
            with self.assertRaises(ValueError):canonical.compare_case_bytes(1,raw,sidecar,parent,pins)

    def test_03_compatibility_identity_changes_never_silently_project(self):
        for location in ('sessions','cleanup_events','producer_events'):
            raw,sidecar,parent,pins=fixture(1);trace=json.loads(raw)
            key={'sessions':'process','cleanup_events':'session_identity','producer_events':'observed_owner_identity'}[location]
            trace[location][0][key]['created_at_utc']='2026-10-17T00:00:02.0000001Z'
            raw=json.dumps(trace,separators=(',',':')).encode();sidecar['original_trace']=canonical.raw_pin(1,raw)
            with self.assertRaisesRegex(ValueError,'EXACT_UNMODIFIED_'):canonical.compare_case_bytes(1,raw,sidecar,parent,pins)

    def test_04_missing_failed_reordered_or_promoted_admissions_reject(self):
        for kind in ('missing','failed','order','promote'):
            raw,sidecar,parent,pins=fixture(1)
            if kind=='missing':sidecar['admissions'].pop()
            elif kind=='failed':sidecar['admissions'][0]['evidence']['channel_message_returned']=False
            elif kind=='order':sidecar['admissions'].reverse()
            else:sidecar['native_provenance_qualified']=True
            with self.assertRaises(ValueError):canonical.compare_case_bytes(1,raw,sidecar,parent,pins)

    def test_05_parent_one_tick_drift_artifact_or_cleanup_failure_still_reject(self):
        for kind in ('parent','artifact','cleanup'):
            raw,sidecar,parent,pins=fixture(1)
            if kind=='parent':parent['owner_admissions'][0]['identity']['created_at_utc']='2026-10-17T00:00:02.0000007Z'
            elif kind=='artifact':parent['artifacts'][0]['pin']['sha256']='0'*64
            else:parent['cleanup_profiles'][0]['cleanup_confirmed']=False
            with self.assertRaises(ValueError):canonical.compare_case_bytes(1,raw,sidecar,parent,pins)

    def test_06_full_eight_scope_and_unique_canonical_lifetimes(self):
        cases=[fixture(i) for i in range(1,9)]
        with self.assertRaisesRegex(ValueError,'WHOLE_EIGHT_REQUIRED'):
            canonical.compare_whole_batch(*[list(v)[:7] for v in zip(*cases,strict=True)])
        cases[1]=fixture(2,owners_for(1))
        with self.assertRaisesRegex(ValueError,'PRODUCER_LIFETIME_REUSED_ACROSS_CASES'):
            canonical.compare_whole_batch(*[list(v) for v in zip(*cases,strict=True)])

    def test_07_original_paced_reader_bytes_and_parse_cap_restored_on_failure(self):
        raw,sidecar,parent,pins=fixture(1)
        values={canonical.trace_path(1):raw,canonical.sidecar_path(1):json.dumps(sidecar).encode()}
        reader=MemoryReader(values);result=canonical.read_case(reader,1,parent,pins)
        self.assertEqual(len(reader.calls),2);self.assertEqual(len(reader.snapshots),2)
        self.assertEqual(reader.maximum_parse_bytes,2097152);self.assertEqual(result['projected_identity_fields'],7)
        values[canonical.sidecar_path(1)]=b' '*65537
        with self.assertRaisesRegex(ValueError,'MODEL_PARSE_BUDGET'):canonical.read_case(reader,1,parent,pins)
        self.assertEqual(reader.maximum_parse_bytes,2097152)

    def test_08_duplicate_keys_invalid_bytes_and_no_native_writer(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_JSON_KEY'):
            canonical.parse_bytes(b'{"case_id":1,"case_id":2}',65536)
        for value in (b'',b'\xff',b'[',bytearray(b'{}')):
            with self.assertRaises(ValueError):canonical.parse_bytes(value,65536)
        tree=ast.parse((ROOT/'tools/p09/crossref_canonical_evidence.py').read_text(encoding='utf-8'))
        calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))]
        self.assertFalse(set(calls)&{'open','write','write_text','write_bytes','Popen','run','kill','unlink'})


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CanonicalEvidenceContracts))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='eight_canonical_evidence_contracts_pass_models_only_not_native' if result.wasSuccessful()
        else 'canonical_evidence_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),declared=result.testsRun,
        failures=failures,model_only=True,raw_native_traces_written=False,prior_suites_reexecuted=False,
        native_execution_authorized=False,native_provenance_qualified=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
