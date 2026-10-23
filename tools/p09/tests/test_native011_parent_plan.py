"""Only the new declaration adapter: no past suites or product execution."""
import copy
import unittest
import current_stored_runtime_scope as scope
import native011_parent_plan as parent


def pin(name):return dict(path='implementation/p09/evidence/'+name+'.json',bytes=1,sha256='a'*64)


class ParentDeclarationContracts(unittest.TestCase):
    def fixture(self):
        semantic=[pin('original'+str(i)) for i in range(162)]+[pin('raw-control')]
        physical=[pin('carrier'+str(i)) for i in range(162)]+[pin('raw-control')]
        descriptors=[dict(schema_version='hwpx-agent.p09-lossless-runtime-source-projection/v1',
            next_case=165,semantic_original_pin=copy.deepcopy(a),physical_envelope_pin=copy.deepcopy(b))
            for a,b in zip(semantic[:162],physical[:162])]
        return dict(semantic_source_freeze=semantic,physical_source_freeze=physical,descriptors=descriptors)

    def test_complete_projection_is_exact_and_does_not_mutate_input(self):
        row=self.fixture();before=copy.deepcopy(row)
        logical,physical=parent.declared_current(row,scope)
        self.assertEqual(len(logical),163);self.assertEqual(len(physical),163)
        self.assertEqual(row,before)

    def test_unmapped_extra_physical_input_rejected(self):
        row=self.fixture();row['physical_source_freeze'].append(pin('undeclared'))
        with self.assertRaisesRegex(ValueError,'COMPLETE_PRIOR_LOGICAL_PHYSICAL_DECLARATION'):
            parent.declared_current(row,scope)

    def test_wrong_alias_pin_rejected_even_when_path_exists(self):
        row=self.fixture();row['descriptors'][0]['physical_envelope_pin']['bytes']=2
        with self.assertRaisesRegex(ValueError,'BOTH_DECLARED_ALIAS_ENDPOINTS_PRESENT'):
            parent.declared_current(row,scope)

    def test_duplicate_alias_never_silently_overwrites(self):
        row=self.fixture();row['descriptors'][-1]=copy.deepcopy(row['descriptors'][0])
        with self.assertRaisesRegex(ValueError,'UNIQUE_PRIOR_DECLARATION_ALIASES'):
            parent.declared_current(row,scope)

    def test_raw_path_cannot_collide_with_a_projected_carrier(self):
        row=self.fixture();row['semantic_source_freeze'].append(pin('carrier0'))
        with self.assertRaisesRegex(ValueError,'NO_PRIOR_PHYSICAL_COLLISION'):
            parent.declared_current(row,scope)

    def test_incomplete_or_wrong_case_descriptor_table_rejected(self):
        for mode in ('missing','wrong_case'):
            row=self.fixture()
            if mode=='missing':row['descriptors'].pop()
            else:row['descriptors'][0]['next_case']=164
            with self.assertRaises(ValueError):parent.declared_current(row,scope)


if __name__=='__main__':unittest.main()
