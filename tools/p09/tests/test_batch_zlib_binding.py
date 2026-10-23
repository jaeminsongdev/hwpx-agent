"""Binding contracts with real original generic classes; no Native evidence."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import batch_zlib_binding as module
import batch_zlib_mapping as mapping
import batch_engine_connection as entry
import current_queue_successor_binding as bindings
import current_stored_runtime_scope as scope

CHECKPOINT=lambda:None


class BindingContracts(unittest.TestCase):
    def fixture(self):
        root=Path(module.__file__).resolve().parents[2];loader=entry.bootstrap_loader(root)
        old_module,_=bindings.connect(root,loader,scope,165,{})
        rows=[]
        for index in range(1,163):
            semantic=dict(path=f'implementation/p09/evidence/p09-361-case114-current-runtime-run{index:03}.v1.json',
                bytes=1,sha256='0'*64)
            physical=dict(path=mapping.PREFIX+f'case114-runtime-run{index:03}.envelope.v1.json',bytes=2,sha256='1'*64)
            rows.append(old_module.source.descriptor(semantic,physical,next_case=165))
        old_pin=dict(path=module.PREFIX+'successor-reference.v1.json',bytes=1,sha256='3'*64)
        original_represent=old_module.Binding.representation
        roles={key:dict(schema_version=key) for key in module.HISTORY_KEYS}
        roles['native009_post_body_shared720_failure_provenance'].update(
            actual_failed_product_child_executed=True,original_failure_promoted=False)
        def represented(self,projection):
            row=original_represent(self,projection)
            return dict(row,**copy.deepcopy(roles))
        old_module.Binding.representation=represented
        old=old_module.Binding(rows,old_pin,next_case=165);reference=NS(binding_module=old_module,binding=old)
        newrows=[dict(schema_version=mapping.SCHEMA,next_case=165,semantic_original_pin=copy.deepcopy(r['semantic_original_pin']),
            physical_envelope_pin=dict(path=mapping.PREFIX+f'case165-zlib-g001-{i:03}.envelope.v1.json',bytes=3,sha256='2'*64))
            for i,r in enumerate(rows,1)]
        declaration=NS(OLD_TABLE_SHA256=module.digest(rows),NEW_TABLE_SHA256=module.digest(newrows),
            ENCODED=tuple((3,'2'*64) for _ in rows),CODEC2=bindings.PINS[1],QUALIFICATION=old_pin,
            REFERENCE_MANIFEST=old_pin)
        return root,loader,reference,declaration,roles

    def connected(self):
        root,loader,reference,declaration,roles=self.fixture()
        result=module.connect(root,loader,scope,reference,declaration,mapping,bindings,CHECKPOINT)
        return result,reference,declaration,roles

    def required(self,result):
        rows={n:dict(p) for n,p in result.binding.originals.items()}
        rows[result.manifest_pin['path']]=dict(result.manifest_pin)
        return rows

    def test_new_full_constructor_and_unchanged_reference(self):
        result,reference,_,_=self.connected()
        self.assertEqual(result.state.constructor_calls,1)
        self.assertNotEqual(result.binding.descriptors(),reference.binding.descriptors())
        self.assertEqual(list(result.binding.originals),list(reference.binding.originals))
        self.assertTrue(result.proof['all_other_original_scope_byte_resource_oracles_retained'])
        self.assertIsNot(result.binding_module,reference.binding_module)

    def test_old_table_subset_and_wrong_manifest_denied(self):
        result,reference,_,_=self.connected()
        for rows,pin in ((reference.binding.descriptors(),result.manifest_pin),
            (result.binding.descriptors()[:-1],result.manifest_pin),
            (result.binding.descriptors(),dict(reference.binding.manifest_pin))):
            with self.assertRaises(ValueError):result.binding_module.Binding(rows,pin,next_case=165)
        self.assertEqual(result.state.constructor_calls,1)

    def test_old_and_new_aliases_collapse_only_to_same_exact_semantics(self):
        result,reference,_,_=self.connected();required=self.required(result)
        old=reference.binding.descriptors()[0];new=result.binding.descriptors()[0]
        for descriptor in (old,new):
            p=descriptor['physical_envelope_pin'];required[p['path']]=p
        normalized,_=result.binding.semantic_union(required,CHECKPOINT)
        self.assertEqual(normalized,self.required(result))

    def test_changed_old_or_new_alias_hash_rejected(self):
        result,reference,_,_=self.connected()
        for descriptor in (reference.binding.descriptors()[0],result.binding.descriptors()[0]):
            required=self.required(result);p=dict(descriptor['physical_envelope_pin'],sha256='4'*64)
            required[p['path']]=p
            with self.assertRaises(ValueError):result.binding.semantic_union(required,CHECKPOINT)

    def test_all_historical_failure_roles_preserved_without_acceptance(self):
        result,reference,_,roles=self.connected();projection,_=result.binding.project(self.required(result),CHECKPOINT)
        row=result.binding.representation(projection)
        for name,value in roles.items():self.assertEqual(row[name],value)
        failure=row['native009_post_body_shared720_failure_provenance']
        self.assertTrue(failure['actual_failed_product_child_executed'])
        self.assertFalse(failure['original_failure_promoted'])
        failure['actual_failed_product_child_executed']=False
        self.assertTrue(result.binding.representation(projection)['native009_post_body_shared720_failure_provenance']['actual_failed_product_child_executed'])

    def test_all_eight_original_history_roles_required_including_legacy149_and154(self):
        root,loader,reference,declaration,_=self.fixture()
        self.assertEqual(len(module.HISTORY_KEYS),8)
        self.assertTrue({'legacy149_validation_failures_provenance','legacy154_validation_failure_provenance'}<=module.HISTORY_KEYS)
        original=reference.binding_module.Binding.representation
        for missing in module.HISTORY_KEYS:
            def represented(self,projection):
                row=original(self,projection);row.pop(missing);return row
            reference.binding_module.Binding.representation=represented
            with self.assertRaisesRegex(ValueError,'EXACT_ALL_HISTORICAL_ROLES'):
                module.connect(root,loader,scope,reference,declaration,mapping,bindings,CHECKPOINT)

    def test_ordinary_inputs_and_original_semantic_scope_not_removed(self):
        result,_,_,_=self.connected();required=self.required(result)
        p=dict(path='target/ordinary.exe',bytes=1,sha256='5'*64);required[p['path']]=p
        projection,_=result.binding.project(required,CHECKPOINT)
        self.assertEqual(dict(projection.semantic_pins),required)
        self.assertEqual(dict(projection.physical_pins[p['path']]),p)
        self.assertEqual(len(projection.physical_pins),len(required))

    def test_wrong_old_or_new_digest_rejected_before_generic_constructor(self):
        root,loader,reference,declaration,_=self.fixture()
        declaration.OLD_TABLE_SHA256='6'*64
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_CONSTRUCTOR_TABLE'):
            module.connect(root,loader,scope,reference,declaration,mapping,bindings,CHECKPOINT)
        declaration.OLD_TABLE_SHA256=module.digest(reference.binding.descriptors());declaration.NEW_TABLE_SHA256='6'*64
        with self.assertRaisesRegex(ValueError,'EXACT_FRESH_FILE_QUALIFIED_NEW_TABLE'):
            module.connect(root,loader,scope,reference,declaration,mapping,bindings,CHECKPOINT)

    def test_entry_projection_changes_only_new_data_paths(self):
        import current_queue_successor_connections as metadata
        def original(*args):
            return ('implementation/p09/evidence/p09-361-case165-successor-worker-bootstrap010.v1.json',
                'implementation/p09/evidence/p09-361-case165-successor-worker-capsule010.compact.v1.json')
        before=original.__code__
        revised=module.entry_reconstructor(NS(reconstruct=original),metadata)
        self.assertEqual(revised(),(module.BOOTSTRAP,module.WIRE))
        self.assertIs(original.__code__,before)

    def previous_hint(self):
        return dict(schema_version='original-worker-schema',index=165,run=9,
            step=dict(index=165,before=158),capsule_pin={'old':'wire'},manifest_pin={'old':'manifest'},
            first_descriptor={'old':'descriptor'},historical_pairs=[],historical_provenance={'original':'history'},
            native009_post_body_shared720_failure_provenance={'actual_failed_product_child_executed':True})

    def test_new_hint_has_closed_execution_fields_and_keeps_original_context(self):
        result,_,_,_=self.connected();prior=self.previous_hint();unchanged=copy.deepcopy(prior)
        wire=dict(bytes=100,sha256='8'*64);hint=module.preparation_hint(prior,result,wire)
        self.assertEqual(set(hint),{'schema_version','index','run','step','capsule_pin','manifest_pin',
            'first_descriptor','historical_pairs','historical_provenance'})
        self.assertEqual((hint['index'],hint['run']),(165,10))
        self.assertEqual(hint['capsule_pin'],dict(path=module.WIRE,**wire))
        self.assertEqual(hint['manifest_pin'],result.manifest_pin)
        self.assertEqual(hint['first_descriptor'],result.binding.descriptors()[0])
        self.assertEqual(prior,unchanged)
        hint['step']['before']=0;hint['historical_provenance']['original']='mutated'
        self.assertEqual(prior,unchanged)

    def test_hint_rejects_other_run_case_or_queue_cursor(self):
        result,_,_,_=self.connected();wire=dict(bytes=100,sha256='8'*64)
        for change in ({'run':10},{'run':True},{'index':164},{'step':dict(index=165,before=159)}):
            prior=dict(self.previous_hint(),**change)
            with self.assertRaises(ValueError):module.preparation_hint(prior,result,wire)

    def test_hint_rejects_non_integer_or_oversize_wire_before_publication(self):
        result,_,_,_=self.connected()
        for size in (0,True,16385):
            with self.assertRaises(ValueError):
                module.preparation_hint(self.previous_hint(),result,dict(bytes=size,sha256='8'*64))


if __name__=='__main__':unittest.main()
