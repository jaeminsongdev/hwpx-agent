"""New cost-accounting contracts only, not an actual engine/Native verdict."""
import copy
from types import SimpleNamespace as NS
import unittest
import native011_parent_oracle as oracle


class OracleCostContracts(unittest.TestCase):
    def model(self):
        return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,
            predicted_runtime_combined_seconds=570.0,aggregate_envelope_decoder_allowance_seconds=5.0)

    def test_original_budget_binding_and_requests_without_shared_double_charge(self):
        rows={'original':'scope'};checks=[];original=lambda:None;row=self.model();before=copy.deepcopy(row)
        def budget(required,requests,source,checkpoint):
            self.assertIs(required,rows);self.assertEqual(requests,167)
            self.assertIs(source,original);checkpoint();return row
        result=oracle.complete_cost(NS(runtime_budget=budget),rows,original,lambda:checks.append(1))
        self.assertEqual(result['with_preparation15_seconds'],585.0)
        self.assertEqual(row,before);self.assertEqual(checks,[1])
        self.assertFalse(result['readiness_measured_or_qualified'])

    def test_readiness_allowance_must_fit_original600(self):
        for value in (585.0,586.0,float('nan')):
            row=self.model();row['predicted_runtime_combined_seconds']=value
            with self.assertRaisesRegex(ValueError,'ORIGINAL_COMPLETE600_PLUS_PREPARATION15'):
                oracle.complete_cost(NS(runtime_budget=lambda *a:row),{},lambda:None,lambda:None)

    def test_original_limit_and_margin_must_not_change(self):
        for key,value in (('unchanged_lock_deadline_seconds',601),('unallocated_margin_seconds',59)):
            row=self.model();row[key]=value
            with self.assertRaisesRegex(ValueError,'ORIGINAL_COMPLETE600_AND_MARGIN60'):
                oracle.complete_cost(NS(runtime_budget=lambda *a:row),{},lambda:None,lambda:None)

    def test_shared_five_may_not_be_omitted(self):
        row=self.model();row.pop('aggregate_envelope_decoder_allowance_seconds')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_SHARED_DECODER5_INCLUDED'):
            oracle.complete_cost(NS(runtime_budget=lambda *a:row),{},lambda:None,lambda:None)


if __name__=='__main__':unittest.main()
