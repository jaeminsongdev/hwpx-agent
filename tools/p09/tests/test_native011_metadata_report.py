"""New report-schema and original Batch admission models, not byte evidence."""
import copy
from types import SimpleNamespace as NS
import unittest
import batch_verification as batch
import native011_metadata_report as reports
import native011_shared_parent as shared


def pin(name):return dict(path=name,bytes=1,sha256='a'*64)


def fixture(cold_source=False):
    original=[pin('tools/p09/model_original'+str(i)+'.py') for i in range(64)]
    if cold_source:original[0]=pin('implementation/p09/evidence/p09-361-case164-current-runtime-run001.v1.json')
    base=dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
        index=165,cleanup_confirmed=True,fresh_inputs=64,final_fresh_hashes=64,source_pins=original,
        accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,step={'index':165})
    _,names=reports.expected_names(base,batch.scope)
    sources={n:pin(n) for n in names};sources.update({p['path']:dict(p) for p in original})
    sources.update({p['path']:dict(p) for p in (reports.GRAPH,reports.PRIOR,*reports.PACKAGE)})
    return base,sources


class MetadataReportContracts(unittest.TestCase):
    def test_explicit_self_free_report_keeps_all_original_pins_without_mutation(self):
        base,sources=fixture();before=copy.deepcopy((base,sources))
        row=reports.compose(base,sources,batch.scope,1)
        self.assertEqual(reports.validate(row,base,batch.scope,1),sources)
        self.assertNotIn(reports.output_path(1),sources)
        self.assertEqual((base,sources),before)
        self.assertFalse(row['actual_Native_Frame_metadata_or_product_qualified'])

    def test_unknown_input_cannot_expand_runtime_scope(self):
        base,sources=fixture();sources['tools/p09/arbitrary.py']=pin('tools/p09/arbitrary.py')
        with self.assertRaisesRegex(ValueError,'ONLY_NAMED_GRAPH_INPUTS'):
            reports.compose(base,sources,batch.scope,1)

    def test_changed_fixed_failure_or_package_pin_rejected(self):
        for name in (reports.PRIOR['path'],reports.PACKAGE[0]['path']):
            base,sources=fixture();sources[name]['bytes']+=1
            with self.assertRaisesRegex(ValueError,'EXACT_FIXED_REFERENCE_AND_PACKAGE'):
                reports.compose(base,sources,batch.scope,1)

    def test_false_is_not_integer_zero_in_an_external_report(self):
        base,sources=fixture();row=reports.compose(base,sources,batch.scope,1);row['accepted_count_delta']=False
        with self.assertRaisesRegex(ValueError,'ENTIRE_CANONICAL_REPORT'):
            reports.validate(row,base,batch.scope,1)

    def test_generation_or_self_file_not_arbitrary(self):
        for value in (True,0,9,'1'):
            with self.assertRaises(ValueError):reports.output_path(value)

    def test_external_report_cannot_claim_native_or_skip_source_pin(self):
        for mode in ('native','missing'):
            base,sources=fixture();row=reports.compose(base,sources,batch.scope,1)
            if mode=='native':row['actual_Native_Frame_metadata_or_product_qualified']=True
            else:row['source_pins'].pop()
            with self.assertRaises(ValueError):reports.validate(row,base,batch.scope,1)

    def admission(self,cold_source=False):
        base,sources=fixture(cold_source)
        old=batch.scope.pins(base['source_pins']);cold=pin('implementation/p09/evidence/p09-361-case163-current-runtime-run001.v1.json')
        history={cold['path']:cold};current=dict(old)
        if cold_source:
            history[base['source_pins'][0]['path']]=current.pop(base['source_pins'][0]['path'])
        whole={**current,**history}
        owner=batch.Batch(whole,current,history,first_index=165,checkpoint=lambda:None)
        planned=NS(batch=owner,whole=whole,current=current,history=history,logical=copy.deepcopy(whole))
        data=NS(planned=planned,report=base,declared=NS(normalize=batch.scope.pins,to_physical=batch.scope.pins))
        record=reports.compose(base,sources,batch.scope,1);path=reports.output_path(1)
        class Reader:
            checkpoint=staticmethod(lambda:None)
            def __init__(self):self.snapshots={}
            def json(self,name):
                if name!=path:raise ValueError('MODEL_CLOSED_REPORT_PATH')
                self.snapshots[name]=pin(name);return copy.deepcopy(record)
            def pin(self,name):return copy.deepcopy(sources[name])
        return data,Reader()

    def test_original_unopened_batch_extension_keeps_history_and_old_plan(self):
        data,q=self.admission();old=data.planned;before=copy.deepcopy((old.whole,old.current,old.history,old.logical))
        admitted=shared.admit_report(None,q,NS(exact=lambda actual,expected,label:self.assertEqual(actual,expected)),batch,data,1)
        self.assertEqual(data.planned.history,old.history);self.assertIs(type(data.planned.batch),batch.Batch)
        self.assertEqual((old.whole,old.current,old.history,old.logical),before)
        self.assertIn(admitted.pin['path'],data.planned.current)
        self.assertFalse(admitted.proof['actual_full_corpus_byte_boundary_or_runtime_qualified'])

    def test_report_source_cannot_reclassify_a_preservation_receipt(self):
        data,q=self.admission(True);old=data.planned
        with self.assertRaisesRegex(ValueError,'NO_COLD_HISTORY_RECLASSIFICATION'):
            shared.admit_report(None,q,NS(exact=lambda actual,expected,label:self.assertEqual(actual,expected)),batch,data,1)
        self.assertIs(data.planned,old)


if __name__=='__main__':unittest.main()
