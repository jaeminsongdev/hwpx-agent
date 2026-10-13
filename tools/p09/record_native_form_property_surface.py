#!/usr/bin/env python3
"""Actual installed typelib source evidence only; no COM activation or native writes."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_color_preparation as color

ROOT,io=color.ROOT,color.io
CAPSULE='implementation/p09/evidence/p09-49-native-form-property-surface.v1.json'
SCRIPT='tools/p09/inspect_native_form_typelib.ps1'
POLICY='implementation/p09/P09-49_NATIVE_FORM_PROPERTY_SURFACE_POLICY.md'
COLOR_SHA='d68d07c05a13422d58b35fda228e4ab6766418a8c10f70954871a37747b95d44'
TYPE_SHA='abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9'
PDFS={
 'implementation/p00/source-archive/original/automation/HwpAutomation_2504.pdf':('917142de2704ae037b0132f5a344ce5331b1fd96cc19dd574666aaacfbf0268c',[47,48,54,57,58]),
 'implementation/p00/source-archive/original/automation/ParameterSetTable_2504.pdf':('6fa10e0ae69711af99a03e54c321c6c922796bd943badf8c21b2c7dfb780ad6e',[129]),
 'implementation/p00/source-archive/original/automation/ActionTable_2504.pdf':('bb876a95ea4e0f4b052c94188a1390b5f981161223759f59f52fc324c8130a87',[11])}
SOURCES=(SCRIPT,'tools/p09/record_native_form_property_surface.py','tools/p09/tests/test_native_form_property_surface.py',
    POLICY,'implementation/p00/source-lock.json',color.CAPSULE,*PDFS)
FORMS=('IXHwpFormEdit','IXHwpFormRadioButton')
GUARDS={'test_source_inventory_and_predecessor_scope_remain_exact','test_actual_installed_typelib_has_exact_native_name_and_tab_setters',
    'test_surface_rejects_changed_target_missing_coerced_or_nonwritable_metadata','test_surface_requires_document_owned_collection_getters',
    'test_receipt_boundary_excludes_original_private_alias_and_traversal','test_no_activation_write_or_runtime_claim_can_be_substituted'}

def require(value,code):io.require(value,code)

def pins():
    require(len(SOURCES)==len(set(SOURCES))==9,'form_surface_source_inventory')
    return {name:io.sha(color.history.progress.original.public.bounded_bytes(ROOT/name,4*1024*1024)) for name in SOURCES}

def preserved_color():
    raw=io.checked(ROOT/color.CAPSULE,COLOR_SHA)
    require(len(raw)==418689,'form_surface_color_receipt_bytes')
    value=json.loads(raw,object_pairs_hook=io.duplicate_guard)
    require(color.pins()==value['source_sha256'] and color.current_graph()==value['complete_current_source_graph']
        and color.progress.preserve()==value['original_local_preservation'],'form_surface_color_inputs_changed')
    for name,(digest,_) in PDFS.items():color.history.progress.original.public.checked(ROOT/name,digest,4*1024*1024)
    return {'color_capsule_sha256':COLOR_SHA,'color_capsule_bytes':418689,'all_23_color_sources_and_1551_current_inputs_exact':True,
            'original_receipts_native_files_and_archives_exact':True,'color_full_workflow_reexecuted_here':False}

def read_surface():
    actual=subprocess.run(['pwsh','-NoLogo','-NoProfile','-NonInteractive','-File',SCRIPT],cwd=ROOT,capture_output=True,check=False)
    require(actual.returncode==0 and not actual.stderr.strip() and 0<len(actual.stdout)<=131072,'form_surface_actual_reader_failed')
    return json.loads(actual.stdout,object_pairs_hook=io.duplicate_guard)

def validate(value):
    expected={'schema_version':'hwpx-agent.native-form-installed-type-surface/v1',
        'state':'read_only_inspection_complete_not_native_qualification','exact_build':'11.0.0.9136',
        'executable_sha256':'7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
        'automation_dll_sha256':'edbc7140f1f09025a34c5ffc2a07c47f90b6a1cdcb2a452b2969b53cd47e1151',
        'registered_typelib_sha256':TYPE_SHA,'registered_typelib_bytes':473120,
        'no_com_server_activation':True,'registry_read_only':True,'type_library_registration_requested':False,
        'hwp_process_set_unchanged':True,'raw_document_values_or_absolute_paths_present':False,
        'native_property_set_or_save_reopen_qualified':False,'p09_complete':False}
    require(type(value) is dict and value.keys()==(expected.keys()|{'binaries'})
        and all(type(value[k]) is type(v) and value[k]==v for k,v in expected.items()),'form_surface_target_or_claims_changed')
    binaries=value['binaries'];require(type(binaries) is list and len(binaries)==3,'form_surface_binary_inventory')
    require([b.get('binary_name') for b in binaries]==['hwp.exe','HwpAutomation.dll','HwpObject.tlb'],'form_surface_binary_inventory')
    for b in binaries[:2]:
        require(b=={'binary_name':b['binary_name'],'state':'type_library_unavailable','error_type':'COMException','hresult':-2147312566},'form_surface_original_binary_failure_changed')
    b=binaries[2];require(b.get('state')=='type_library_read' and type(b.get('surface')) is dict,'form_surface_registered_library_missing')
    surface=b['surface']
    require(surface.get('library_guid')=='7d2b6f3c-1d95-4e0c-bf5a-5ee564186fbc' and surface.get('system_kind')=='SYS_WIN32'
        and type(surface.get('major_version')) is int and surface['major_version']==1
        and type(surface.get('minor_version')) is int and surface['minor_version']==0
        and type(surface.get('type_count')) is int and surface['type_count']==255,'form_surface_registered_library_identity')
    types=surface['selected_types'];require(type(types) is list and len({t['name'] for t in types})==len(types),'form_surface_type_alias')
    by_name={t['name']:t for t in types};verified={}
    for name in FORMS:
        require(name in by_name,'form_surface_native_interface_missing');rows=by_name[name]['members'];fields={}
        for field,member,variant in (('name',3,8),('TabOrder',8,3)):
            actual=[m for m in rows if m['name']==field]
            expected_rows=[{'name':field,'member_id':member,'invoke_kind':'INVOKE_PROPERTYGET','return_variant_type':variant,'parameters':[]},
                {'name':field,'member_id':member,'invoke_kind':'INVOKE_PROPERTYPUT','return_variant_type':24,'parameters':[{'variant_type':variant,'flags':1}]}]
            require(io.canonical(actual)==io.canonical(expected_rows),'form_surface_native_setter_signature_changed');fields[field]=actual
        verified[name]=fields
    for type_name,member,member_id,parameters in (('IHwpObject','XHwpDocuments',20002,[]),
        ('IXHwpDocuments','Item',11,[{'variant_type':3,'flags':1}]),('IXHwpDocuments','Count',12,[]),
        ('IXHwpDocument','XHwpFormEdits',18,[]),('IXHwpDocument','XHwpFormRadioButtons',16,[]),
        ('IXHwpFormEdits','Item',10,[{'variant_type':3,'flags':1}]),('IXHwpFormEdits','Count',11,[]),
        ('IXHwpFormRadioButtons','Item',10,[{'variant_type':3,'flags':1}]),('IXHwpFormRadioButtons','Count',11,[])):
        require(type_name in by_name,'form_surface_document_collection_missing')
        rows=[m for m in by_name[type_name]['members'] if m['name']==member and m['invoke_kind']=='INVOKE_PROPERTYGET']
        require(len(rows)==1 and type(rows[0]['member_id']) is int and rows[0]['member_id']==member_id
            and io.canonical(rows[0]['parameters'])==io.canonical(parameters),'form_surface_document_collection_signature_changed')
    return verified

def evidence_path(path):
    target=path.absolute();require(target==ROOT/CAPSULE and '..' not in path.parts,'form_surface_output_boundary')
    io.read(ROOT/color.CAPSULE)
    if target.exists():io.read(target)
    return target

def guards():
    actual=subprocess.run([sys.executable,'-E','-B','-X','utf8','-m','unittest','-v','tools.p09.tests.test_native_form_property_surface'],
        cwd=ROOT,capture_output=True,check=False)
    text=actual.stderr.decode('utf-8',errors='strict');names=[]
    pattern=r'(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_native_form_property_surface\.NativeFormPropertySurfaceGuards\.([a-z0-9_]+)\) \.\.\. ok'
    for line in text.splitlines():
        if match:=re.fullmatch(pattern,line):require(match[1]==match[2],'form_surface_guard_identity');names.append(match[1])
    require(actual.returncode==0 and not actual.stdout.strip() and len(names)==6 and set(names)==GUARDS and text.count(' ... ')==6
        and re.search(r'\nRan 6 tests in [0-9.]+s\s+OK\s*$',text) and 'skipped' not in text,'form_surface_guards_failed')
    return {'passed':6,'failed':0,'errors':0,'skipped':0,'names':sorted(names),'actually_invoked':True}

def record():
    before=pins();prior=preserved_color();surface=read_surface();verified=validate(surface);actual_guards=guards()
    require(before==pins() and prior==preserved_color(),'form_surface_inputs_changed')
    return {'schema_version':'hwpx-agent.p09-49-native-form-property-source-surface/v1',
        'state':'actual_exact_installed_typelib_property_surface_verified_not_native_write_qualification',
        'source_sha256':before,'preserved_color_source_successor':prior,'actual_installed_typelib_inspection':surface,
        'exact_native_property_get_and_put_signatures':verified,'actual_python_guards':actual_guards,
        'reviewed_official_manuals':{n:{'sha256':s,'complete_pages_read_and_visually_reviewed':pages} for n,(s,pages) in PDFS.items()},
        'claims':{'installed_2020_native_name_and_tab_setters_declared':True,'literal_native_name_member':'name',
            'name_bstr_and_tab_order_i4_declarations_verified':True,'live_collection_to_source_identity_binding':'not_run',
            'setter_values_or_save_reopen_preservation':'not_run','native_color_name_tab_fix_qualified':False,
            'scripts_use_public_raw_actions_or_native_names_as_user_input':False,'new_native_session_started':False,
            'render_or_direct_automation_differential':'not_run','signed_form_publication_or_p09_gate':False,'green_rows':0},
        'privacy':{'raw_private_document_values_or_absolute_machine_paths_present':False,'original_inputs_or_registry_trust_settings_changed':False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output',type=Path);mode.add_argument('--verify',type=Path);args=parser.parse_args()
    try:
        path=evidence_path(args.output or args.verify);require(not args.output or not path.exists(),'form_surface_receipt_exists')
        value=record();raw=io.canonical(value)
        if args.output:
            with path.open('xb') as stream:stream.write(raw)
        else:require(io.read(path)==raw,'form_surface_fresh_whole_result_changed')
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch('[a-z_]+',str(error)) else type(error).__name__
        print(json.dumps({'state':'fail','error_code':code}));return 2
    print(json.dumps({'state':'pass','scope':'installed_typelib_declarations_not_native_execution',
        'sha256':io.sha(raw),'bytes':len(raw),'source_pins':9,'actual_guards':6,'interfaces':2,
        'native_session_started':False,'green_rows':0}));return 0

if __name__=='__main__':raise SystemExit(main())
