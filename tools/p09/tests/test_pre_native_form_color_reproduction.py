import json
import unittest
from tools.p09 import reproduce_pre_native_form_color as q

class PreColorSourceReproductionTests(unittest.TestCase):
    def test_authentic_complete_source_view_overrides_predecessor_with_original_p46_pins(self):
        copied,manifest,origins=q.select()
        self.assertEqual(len(manifest),1534);self.assertEqual(sum(map(len,copied.values())),50833903)
        self.assertEqual({n for n,o in origins.items() if n!=o},set(q.progress.CHANGED))
        self.assertNotIn('crates/hwpx-package/src/native_form_color.rs',manifest)
        self.assertNotIn('crates/product-cli/src/form_color_preparation.rs',manifest)

    def test_exact_original_cli_protocol_rejects_missing_extra_coerced_failure_and_duplicate(self):
        raw=json.dumps(q.EXPECTED).encode();self.assertEqual(q.protocol(0,raw,b''),q.EXPECTED)
        for value in (dict(q.EXPECTED,state='fail'),dict(q.EXPECTED,green_rows=False),dict(q.EXPECTED,extra=True)):
            with self.assertRaises(ValueError):q.protocol(0,json.dumps(value).encode(),b'')
        with self.assertRaises(ValueError):q.protocol(1,raw,b'')
        with self.assertRaises(ValueError):q.protocol(0,raw,b'error')
        with self.assertRaises(ValueError):q.protocol(0,b'{"state":"pass","state":"pass"}',b'')

    def test_short_source_boundary_rejects_workspace_root_other_parent_and_other_name(self):
        for path in (q.ROOT,q.ROOT/'ordinary-user-directory',q.ROOT.parent/'q1234'):
            with self.assertRaisesRegex(ValueError,'color_original_short_source_boundary'):q.boundary(path)

    def test_original_launch_retains_installed_dependencies_without_environment_or_authority_override(self):
        compile(q.DIAGNOSTIC_CODE,'bounded_original_p46_diagnostic','exec')
        command=q.original_command()
        self.assertEqual(command,[q.sys.executable,'-E','-B','-X','utf8',
            'tools/p09/qualify_stored_product_request.py','--verify',q.ORIGINAL])
        self.assertEqual(q.original_command(True),command[:5]+['-c',q.DIAGNOSTIC_CODE])
        self.assertNotIn('-I',command)

    def test_diagnostic_protocol_is_not_cli_success_and_rejects_duplicate_missing_or_exit_mismatch(self):
        value={'state':'fail','scope':'diagnostic_only_original_p46_body_not_cli_qualification','error_code':'synthetic_protocol_case'}
        raw=json.dumps(value).encode()
        self.assertEqual(q.diagnostic_protocol(2,b'{"diagnostic_codes":[]}\n'+raw+b'\n',b''),value)
        for code,output,stderr in ((0,raw,b''),(2,raw+b'\n'+raw,b''),(2,b'{}',b''),(2,raw,b'error')):
            with self.assertRaises(ValueError):q.diagnostic_protocol(code,output,stderr)
        with self.assertRaises(ValueError):q.protocol(0,raw,b'')

if __name__=="__main__":unittest.main()
