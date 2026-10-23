import ast,json,unittest
from pathlib import Path
import crossref_native_worker_io as subject
ROOT=Path(__file__).resolve().parents[3]

def result(**case):
    return dict(state='fixed_eight_callbacks_failed_or_partial',phase='fixed_eight',error_code='P09_XREF_BIND_BATCH_CASE_NOT_RETURNED',
        case_failure=dict(case_index=1,phase='source_bind',error_code='P09_XREF_BIND_SINGLE_DOCUMENT_REQUIRED',**case))

class Tests(unittest.TestCase):
    def test_closed_first_case_error_and_phase_are_in_early_notice(self):
        value=subject.result_notice(result())
        self.assertEqual((value['failed_case_index'],value['failed_case_phase'],value['failed_case_error_code']),
            (1,'source_bind','P09_XREF_BIND_SINGLE_DOCUMENT_REQUIRED'))
        self.assertTrue(value['worker_failed_or_uncertain']);self.assertFalse(value['cleanup_confirmed']);self.assertTrue(value['rerun_forbidden'])
        self.assertFalse(value['native_execution_authorized']);self.assertFalse(value['P09_complete'])

    def test_untrusted_text_types_and_bool_index_do_not_escape(self):
        value=result();value['case_failure'].update(case_index=True,phase='PRIVATE-PATH',error_code='PRIVATE-PATH',untrusted_extra='PRIVATE-PATH')
        out=subject.result_notice(value)
        self.assertIsNone(out['failed_case_index']);self.assertIsNone(out['failed_case_phase']);self.assertIsNone(out['failed_case_error_code'])
        self.assertNotIn('PRIVATE',json.dumps(out))

    def test_case_bounds_and_non_string_values_are_closed(self):
        for index in(0,9,-1,1.0,'1',None):
            value=result();value['case_failure'].update(case_index=index,phase=['source_bind'],error_code={'raw':'PRIVATE'})
            out=subject.result_notice(value)
            self.assertIsNone(out['failed_case_index']);self.assertIsNone(out['failed_case_phase']);self.assertIsNone(out['failed_case_error_code'])

    def test_original_open_guard_and_stop_codes_are_sanitized_but_not_erased(self):
        for code in('P58_OPEN_FAILED','STOP_RAM_PRESSURE','P09_XREF_BIND_OBSERVATION_MISMATCH'):
            value=result();value['case_failure']['error_code']=code
            self.assertEqual(subject.result_notice(value)['failed_case_error_code'],code)

    def test_original_session_and_no_case_notice_bytes_remain_identical(self):
        source=ROOT/'implementation/p09/source-archive/p361-crossref-case-diagnostics483/worker-io.py'
        tree=ast.parse(source.read_text(encoding='utf-8'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='result_notice')
        import re
        scope={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
        for value in[{},dict(state='session_worker_failed_or_uncertain',phase='exact_existing_owner',error_code='P09_XREF_ROT_NO_MATCH'),
            dict(state='session_worker_lifecycle_returned_source_and_native_qualification_pending',phase='host_kernel_close'),
            dict(state='fixed_eight_callbacks_returned_semantics_unqualified',phase='fixed_eight',case_failure=None)]:
            self.assertEqual(subject.result_notice(value),scope['result_notice'](value))

    def test_worker_adds_only_the_closed_projection_without_a_new_native_call(self):
        path='implementation/p09/tools/run-crossref-qualified-fixed-worker.ps1';current=(ROOT/path).read_text(encoding='utf-8')
        old=(ROOT/'implementation/p09/source-archive/p361-crossref-case-diagnostics483/fixed-worker.ps1').read_text(encoding='utf-8')
        line="    $result['case_failure']=Get-P09XrefBatchFailureSummary $batch\n"
        self.assertEqual(current.count(line),1);self.assertEqual(current.replace(line,''),old)

if __name__=='__main__':unittest.main()
