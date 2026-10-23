"""New runtime candidate pure tests; no native process creation or DLL activation."""
import unittest
from unittest.mock import patch
import crossref_python_current555 as subject
def live():return dict(executable=str(subject.fixed.PYTHON),core=str(subject.fixed.PYTHON.parent/'python312.dll'),version='3.12.14',pointer_bits=64)
class Tests(unittest.TestCase):
    def test_exact_two_images_and_observed_paths_do_not_issue_authority(self):
        value=subject.validate(subject.specifications(),live());self.assertFalse(value['native_session_or_execution_authorized']);self.assertFalse(value['loaded_memory_bytes_hashed'])
    def test_historical_exe_is_not_accepted_as_current_build(self):
        pins=subject.specifications();pins['python.exe']['sha256']='dea78bb78043f0d53ef4a475f85fa0312b90fa93c136a0686d17946781c60e16'
        with self.assertRaises(ValueError):subject.validate(pins,live())
    def test_each_image_hash_size_and_name_is_exact(self):
        for name in subject.specifications():
            for field,bad in(('bytes',1),('sha256','a'*64),('path','foreign.dll')):
                with self.subTest(image=name,field=field):
                    pins=subject.specifications();pins[name][field]=bad
                    with self.assertRaises(ValueError):subject.validate(pins,live())
    def test_missing_core_extra_image_or_boolean_size_is_denied(self):
        cases=[{'python.exe':subject.specifications()['python.exe']},{**subject.specifications(),'foreign.dll':{}},
            {**subject.specifications(),'python.exe':{**subject.specifications()['python.exe'],'bytes':True}}]
        for pins in cases:
            with self.assertRaises(ValueError):subject.validate(pins,live())
    def test_foreign_executable_or_core_path_is_denied(self):
        for field in('executable','core'):
            value=live();value[field]='D:\\outside\\python.exe'
            with self.assertRaises(ValueError):subject.validate(subject.specifications(),value)
    def test_same_image_names_cannot_hide_version_or_abi_mismatch(self):
        for field,bad in(('version','3.12.13'),('pointer_bits',32),('pointer_bits',True)):
            value=live();value[field]=bad
            with self.assertRaises(ValueError):subject.validate(subject.specifications(),value)
    def test_returned_pin_maps_cannot_mutate_the_closed_specifications(self):
        pins=subject.specifications();pins.clear();self.assertEqual(len(subject.specifications()),2)
    def test_missing_loaded_core_never_loads_a_replacement(self):
        class Function:
            def __call__(self,*args):return 0
        class Kernel:
            GetModuleHandleW=Function();GetModuleFileNameW=Function()
        with patch.object(subject.ctypes,'WinDLL',return_value=Kernel()):
            with self.assertRaisesRegex(ValueError,'EXISTING_CORE_MODULE_REQUIRED'):subject.observe_loaded_images()
