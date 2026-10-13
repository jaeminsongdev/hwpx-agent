import copy
import unittest
from tools.p09 import record_native_form_property_surface as q

class NativeFormPropertySurfaceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.actual=q.read_surface()

    def test_source_inventory_and_predecessor_scope_remain_exact(self):
        self.assertEqual(len(q.pins()),9)
        self.assertFalse(q.preserved_color()['color_full_workflow_reexecuted_here'])

    def test_actual_installed_typelib_has_exact_native_name_and_tab_setters(self):
        observed=q.validate(self.actual);self.assertEqual(set(observed),set(q.FORMS))
        for properties in observed.values():
            self.assertEqual(set(properties),{'name','TabOrder'})
            self.assertEqual(properties['name'][1]['parameters'],[{'variant_type':8,'flags':1}])
            self.assertEqual(properties['TabOrder'][1]['parameters'],[{'variant_type':3,'flags':1}])

    def test_surface_rejects_changed_target_missing_coerced_or_nonwritable_metadata(self):
        for key,value in (('exact_build','different'),('registered_typelib_bytes',True),('registered_typelib_sha256','0'*64)):
            changed=copy.deepcopy(self.actual);changed[key]=value
            with self.assertRaises(ValueError):q.validate(changed)
        for edit in ('missing_put','wrong_type','wrong_member_id','coerced_type'):
            changed=copy.deepcopy(self.actual)
            types=changed['binaries'][2]['surface']['selected_types'];target=next(t for t in types if t['name']=='IXHwpFormEdit')
            row=next(m for m in target['members'] if m['name']=='name' and m['invoke_kind']=='INVOKE_PROPERTYPUT')
            if edit=='missing_put':target['members'].remove(row)
            elif edit=='wrong_type':row['parameters'][0]['variant_type']=3
            elif edit=='coerced_type':row['member_id']=True
            else:row['member_id']=99
            with self.assertRaises(ValueError):q.validate(changed)

    def test_surface_requires_document_owned_collection_getters(self):
        changed=copy.deepcopy(self.actual);types=changed['binaries'][2]['surface']['selected_types']
        target=next(t for t in types if t['name']=='IXHwpDocument')
        target['members']=[m for m in target['members'] if m['name']!='XHwpFormEdits']
        with self.assertRaises(ValueError):q.validate(changed)

    def test_receipt_boundary_excludes_original_private_alias_and_traversal(self):
        self.assertEqual(q.evidence_path(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (q.ROOT/q.color.CAPSULE,q.ROOT/'implementation/p09/evidence/private/result.json',
            q.ROOT/'implementation/p09/evidence/../evidence/p09-49-native-form-property-surface.v1.json'):
            with self.assertRaises(ValueError):q.evidence_path(path)

    def test_no_activation_write_or_runtime_claim_can_be_substituted(self):
        for key,value in (('no_com_server_activation',False),('registry_read_only',False),
            ('type_library_registration_requested',True),('native_property_set_or_save_reopen_qualified',True),('p09_complete',True)):
            changed=copy.deepcopy(self.actual);changed[key]=value
            with self.assertRaises(ValueError):q.validate(changed)

if __name__=='__main__':unittest.main()
