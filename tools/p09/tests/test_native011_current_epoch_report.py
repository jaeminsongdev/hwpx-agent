"""Current805 report models only; no Frame, worker, product or old suites."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import current_stored_runtime_scope as scope
import native011_metadata_report as original
import native011_current_epoch_report as report


def pin(path):return dict(path=path,bytes=1,sha256='a'*64)


def fixture():
    raw=(Path(__file__).resolve().parents[3]/report.SOURCE['path']).read_bytes()
    api,proof=report.connect(raw)
    base=dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
        index=165,cleanup_confirmed=True,fresh_inputs=64,final_fresh_hashes=64,
        source_pins=[pin('tools/p09/original_model_'+str(i)+'.py') for i in range(64)])
    _,names=api.expected_names(base,scope)
    sources={name:pin(name) for name in names}
    sources.update({p['path']:dict(p) for p in (api.GRAPH,api.PRIOR,*api.PACKAGE,*report.DATA)})
    return api,proof,base,sources


class CurrentReportContracts(unittest.TestCase):
    def test_exact_fifteen_named_roles_original64_and_self_free_report(self):
        api,proof,base,sources=fixture();before=copy.deepcopy((base,sources));old=original.EXTRA_CODE
        row=api.compose(base,sources,scope,3)
        self.assertEqual(api.validate(row,base,scope,3),sources)
        self.assertEqual(row['original_producer64_source_pins'],sorted(base['source_pins'],key=lambda p:p['path']))
        self.assertNotIn(api.output_path(3),sources)
        self.assertEqual((base,sources),before);self.assertIs(original.EXTRA_CODE,old)
        self.assertEqual(len(proof['named_current805_roles']),15)
        self.assertFalse(row['actual_Native_Frame_metadata_or_product_qualified'])

    def test_whole_main_and_validator_original_code_retained_in_private_namespace(self):
        api,_,_,_=fixture()
        self.assertEqual(api.main.__code__,original.main.__code__)
        self.assertEqual(api.validate.__code__,original.validate.__code__)
        self.assertIsNot(api.main.__globals__,original.main.__globals__)
        self.assertEqual(original.EXTRA_CODE,api.EXTRA_CODE[:len(original.EXTRA_CODE)])

    def test_missing_unknown_or_changed_provenance_rejected(self):
        for mode in ('missing','unknown','changed'):
            api,_,base,sources=fixture()
            if mode=='missing':del sources[report.SELF]
            if mode=='unknown':sources['tools/p09/arbitrary.py']=pin('tools/p09/arbitrary.py')
            if mode=='changed':sources[report.DATA[0]['path']]['bytes']+=1
            with self.assertRaises(ValueError):api.compose(base,sources,scope,3)

    def test_no_old_generation_or_runtime_promotion(self):
        api,_,base,sources=fixture()
        for generation in (True,1,2,4):
            with self.assertRaisesRegex(ValueError,'ONLY_NEW_GENERATION003'):
                api.compose(base,sources,scope,generation)
        row=api.compose(base,sources,scope,3);row['GO_authorized']=True
        with self.assertRaisesRegex(ValueError,'ENTIRE_CANONICAL_REPORT'):
            api.validate(row,base,scope,3)

    def test_changed_original_source_rejected_before_compilation(self):
        for raw in (b'',b'print("not original")',None):
            with self.assertRaisesRegex(ValueError,'EXACT_ENTIRE_ORIGINAL_PRODUCER_SOURCE'):
                report.connect(raw)
