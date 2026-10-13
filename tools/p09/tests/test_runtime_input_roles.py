import copy
import unittest
import audit_runtime_input_roles as a


class InputRoleTests(unittest.TestCase):
    def setup_inputs(self):
        self.source='crates/example/src/lib.rs'
        self.manifest='implementation/p09/evidence/fixture-input.json'
        self.history='implementation/p09/evidence/old-verification.json'
        self.archive='implementation/p09/source-archive/old.json'
        self.worker='implementation/p09/evidence/compiled-inventory.json'
        self.exe='target/current.exe';self.old='target/historical.exe'
        paths=(self.source,self.manifest,self.history,self.archive,self.worker,self.exe,self.old)
        self.expected={n:dict(path=n,bytes=i+1,sha256='a'*64) for i,n in enumerate(paths)}

    def setUp(self):self.setup_inputs()

    def audit(self,text='',sources=None,worker=None,expected=None,exe=None):
        return a.classify(self.expected if expected is None else expected,
            self.expected[self.exe] if exe is None else exe,
            {self.source:text} if sources is None else sources,
            {self.worker} if worker is None else worker)

    def role(self,result,name):
        return next(row for row in result['manifest_roles'] if row['pin']['path']==name)['role']

    def test_evidence_actually_referenced_by_source_retained(self):
        result=self.audit('read("'+self.manifest+'")')
        self.assertEqual(self.role(result,self.manifest),'RUST_REFERENCED_EVIDENCE_RETAINED')

    def test_filename_only_reference_is_conservatively_retained(self):
        self.assertEqual(self.role(self.audit('join("fixture-input.json")'),self.manifest),
            'RUST_REFERENCED_EVIDENCE_RETAINED')

    def test_worker_direct_manifest_never_eligible_for_exclusion(self):
        self.assertEqual(self.role(self.audit(),self.worker),'DIRECT_WORKER_INPUT_REQUIRED')

    def test_no_literal_reference_does_not_prove_nonusage(self):
        result=self.audit();self.assertEqual(self.role(result,self.history),'HISTORICAL_CANDIDATE_USAGE_UNPROVEN_RETAINED')
        self.assertEqual(result['safe_runtime_exclusions'],[])
        self.assertFalse(result['lack_of_literal_reference_used_as_nonusage_proof'])

    def test_archive_name_alone_is_not_excluded(self):
        self.assertEqual(self.role(self.audit(),self.archive),'HISTORICAL_CANDIDATE_USAGE_UNPROVEN_RETAINED')

    def test_current_executable_and_historical_boundary_distinct(self):
        result=self.audit();self.assertEqual(self.role(result,self.exe),'CURRENT_EXECUTABLE_REQUIRED')
        self.assertEqual(self.role(result,self.old),'HISTORICAL_EXECUTABLE_WHOLE_RECONCILIATION_REQUIRED')

    def test_every_original_pin_and_byte_total_preserved(self):
        before=copy.deepcopy(self.expected);result=self.audit(self.manifest)
        self.assertEqual(a.v.pins([row['pin'] for row in result['manifest_roles']]),before)
        self.assertEqual(sum(result['role_bytes'].values()),sum(p['bytes'] for p in before.values()))
        self.assertEqual(self.expected,before)

    def test_unknown_scanned_source_rejected(self):
        with self.assertRaises(ValueError):self.audit(sources={'unbound.rs':''})

    def test_unknown_or_empty_worker_inputs_rejected(self):
        for worker in (set(),{'unbound.json'}):
            with self.assertRaises(ValueError):self.audit(worker=worker)

    def test_changed_current_executable_pin_rejected(self):
        with self.assertRaises(ValueError):self.audit(exe=dict(self.expected[self.exe],sha256='b'*64))

    def test_malformed_or_path_escape_pin_rejected(self):
        expected=dict(self.expected);expected[self.manifest]=dict(expected[self.manifest],path='../escape.json')
        with self.assertRaises(ValueError):self.audit(expected=expected)

    def test_static_audit_never_authorizes_runtime_or_gate(self):
        result=self.audit();self.assertFalse(result['runtime_input_exclusions_authorized'])
        self.assertFalse(result['reduced_scope_runtime_qualified'])
        self.assertFalse(result['dynamic_fixture_dependency_closure_complete'])
        self.assertFalse(result['product_complete']);self.assertEqual(result['P09_gate'],'OPEN')


if __name__=='__main__':unittest.main()
