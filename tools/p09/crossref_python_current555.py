"""Finite current runtime candidate, NOT an execution permit or replacement of the historic runtime gate."""
import ctypes,struct,sys
from ctypes import wintypes as w
from pathlib import Path
import crossref_preassigned_readonly as fixed
PROFILE='hwpx-agent.crossref-local-python/3.12.14-build-current-v1'
IMAGES=(('python.exe',107312,'7a4102b91959bb234507850ea584e1d31d300a6831b171e4aadc59ff592f0234'),
    ('python312.dll',6985520,'e39aa2da5ea2d310d89994f71bf913a0a137ebaf9f692a565b8c896081512f28'))
def require(ok,code):
    if not ok:raise ValueError('XREF_PYTHON_CURRENT_'+code)
def specifications():return {name:dict(path=name,bytes=size,sha256=sha)for name,size,sha in IMAGES}
def observe_loaded_images():
    # Observe an ALREADY loaded CPython core. Never LoadLibrary, start a process or fall back to another image.
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetModuleHandleW.argtypes,k.GetModuleHandleW.restype=[w.LPCWSTR],w.HMODULE
    k.GetModuleFileNameW.argtypes,k.GetModuleFileNameW.restype=[w.HMODULE,w.LPWSTR,w.DWORD],w.DWORD
    handle=k.GetModuleHandleW('python312.dll');require(bool(handle),'EXISTING_CORE_MODULE_REQUIRED')
    buffer=ctypes.create_unicode_buffer(32768);count=k.GetModuleFileNameW(handle,buffer,len(buffer))
    require(0<count<len(buffer),'EXACT_LOADED_CORE_PATH')
    return dict(executable=str(Path(sys.executable).absolute()),core=buffer.value,version='.'.join(map(str,sys.version_info[:3])),pointer_bits=8*struct.calcsize('P'))
def validate(pins,loaded):
    expected=specifications();require(type(pins)is dict and set(pins)==set(expected),'EXACT_TWO_IMAGE_INVENTORY')
    for name,value in expected.items():
        actual=pins[name];require(type(actual)is dict and type(actual.get('bytes'))is int and actual==value,'CURRENT_EXE_AND_CORE_BYTES')
    require(type(loaded)is dict and set(loaded)=={'executable','core','version','pointer_bits'},'EXACT_LIVE_OBSERVATION')
    require(type(loaded['pointer_bits'])is int and loaded['pointer_bits']==64 and loaded['version']=='3.12.14','LIVE_VERSION_AND_ABI')
    require(type(loaded['executable'])is str and type(loaded['core'])is str
        and loaded['executable'].casefold()==str(fixed.PYTHON).casefold()
        and loaded['core'].casefold()==str(fixed.PYTHON.parent/'python312.dll').casefold(),'FIXED_LOADED_EXE_AND_CORE_PATHS')
    return dict(profile=PROFILE,two_current_disk_images_verified=True,already_loaded_image_paths_verified=True,
        loaded_memory_bytes_hashed=False,native_session_or_execution_authorized=False)
