"""Fixed one-document/eight-block Native SOURCE capture plan, not an executor.

The exact output XML/name mapping remains unobserved. No caller input, COM object,
process API, file mutation, direct HWPX writer or Native permit is exposed here.
"""
import hashlib
import json

PLAN_SCHEMA='hwpx-agent.p09.block-bookmark-source-plan643/v1'
DIRECTORY='implementation/p09/evidence/private/p09-361-block-bookmark643-source-document001'


def require(ok,code):
    if not ok:raise ValueError('P643_'+code)


def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()


def cases():
    seeds=(('', 'B643_ALPHA',' right'),('left ','two words',''),('head ','한글내용',' tail'),
        ('','A&B<C>',''),('prefix:','0123456789',':suffix'),('before ','Mixed_한글_123',' after'),
        ('123456 ','RANGE',' 789'),('!','끝','?'))
    rows=[]
    for index,(prefix,target,suffix)in enumerate(seeds,1):
        seed=prefix+target+suffix
        require(all(0x20<=ord(c)<=0xffff for c in seed),'BMP_SINGLE_PARAGRAPH_TEXT')
        rows.append(dict(case_index=index,paragraph_index=index-1,bookmark_name=f'p09_block643_{index:02}',
            seed_text=seed,seed_text_sha256=digest(seed),selected_text=target,selected_text_sha256=digest(target),
            selection=dict(spara=index-1,spos=len(prefix),epara=index-1,epos=len(prefix)+len(target))))
    return rows


def member(types,type_name,name,kind,return_type,parameter_types):
    rows=[m for t in types if t['name']==type_name for m in t['members']if m['name']==name and m['invoke_kind']==kind]
    require(len(rows)==1,'DECLARATION_SINGLE_MEMBER')
    row=rows[0]
    require(row['return_variant_type']==return_type and [p['variant_type']for p in row['parameters']]==parameter_types
        and all(p['flags']==1 for p in row['parameters']),'DECLARATION_SIGNATURE')
    return row['member_id']


def declarations(value):
    require(value['state']=='OBSERVED642_INSTALLED_BLOCK_CAPTURE_DECLARATIONS_NOT_NATIVE'
        and value['exact_build']=='11.0.0.9136' and value['typelib_sha256']=='abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9'
        and value['no_com_server_activation'] is True and value['registry_read_only'] is True
        and value['hwp_process_set_unchanged'] is True and value['native_execution_authorized'] is False
        and value['native_GetDefault_Execute_SetItem_or_SelectText_invoked'] is False,'READONLY_DECLARATIONS_NOT_AUTHORITY')
    types=value['selected_types']
    result={}
    for t,n,k,v,args in (
        ('IHwpObject','HAction','INVOKE_PROPERTYGET',9,[]),('IHwpObject','HParameterSet','INVOKE_PROPERTYGET',9,[]),
        ('IHwpObject','SelectText','INVOKE_FUNC',11,[3,3,3,3]),('IHwpObject','SelectionMode','INVOKE_PROPERTYGET',3,[]),
        ('IHwpObject','SetPos','INVOKE_FUNC',11,[3,3,3]),
        ('HParameterSet','HBookMark','INVOKE_PROPERTYGET',9,[]),('HParameterSet','HInsertText','INVOKE_PROPERTYGET',9,[]),
        ('HBookMark','HSet','INVOKE_PROPERTYGET',9,[]),('HBookMark','Command','INVOKE_PROPERTYPUT',24,[19]),
        ('HInsertText','HSet','INVOKE_PROPERTYGET',9,[]),('HInsertText','Text','INVOKE_PROPERTYPUT',24,[8]),
        ('IDHwpParameterSet','SetItem','INVOKE_FUNC',24,[8,12]),('IDHwpParameterSet','Item','INVOKE_FUNC',12,[8]),
        ('HAction','GetDefault','INVOKE_FUNC',11,[8,9]),('HAction','Execute','INVOKE_FUNC',11,[8,9])):
        result[t+'.'+n+'.'+k]=member(types,t,n,k,v,args)
    # Do not invent SDK Name/Type shortcuts that the installed projection did
    # not declare. Generic HSet.SetItem is the declared path; its return is VOID.
    require(not any(t['name']=='HBookMark' and m['name']in('Name','Type')and m['invoke_kind']=='INVOKE_PROPERTYPUT'
        for t in types for m in t['members']),'UNREVIEWED_TYPED_SHORTCUT')
    return result


def build(value):
    bindings=declarations(value)
    rows=cases()
    return dict(schema_version=PLAN_SCHEMA,purpose='Native_source_provenance_only_not_crossref_insertion_or_product_acceptance',
        source_document_count=1,block_bookmark_count=8,fresh_creation_sessions=1,independent_reopen_sessions=1,
        cases=rows,whole_seed_text='\r\n'.join(r['seed_text']for r in rows),
        output_directory=DIRECTORY,artifact_names=['created.hwpx','reopened.hwpx','created-page-001.bmp','reopened-page-001.bmp','case-trace.json'],
        SDK_Bookmark=dict(action_id='Bookmark',parameter_set_id='BookMark',Name_item_type='PIT_BSTR',Type_item_type='PIT_UI',
            block_type_value=1,create_command_value=0,Name_and_Type_access='HBookMark.HSet.SetItem',Command_access='HBookMark.Command_UINT32'),
        declared_members=bindings,
        per_bookmark_order=['GetDefault_Bookmark','SetItem_Name','SetItem_Type_UINT32_1','Command_UINT32_0',
            'SelectText_exact_fixed_range','verify_owner_selection_and_parameter_readback','Execute_Bookmark_once_no_retry'],
        required_owner_boundaries=['fresh_owned_empty_document','original_current_session_and_exact_PID_creation_identity',
            'guarded_private_SaveAs','independent_reopen_and_owner_cleanup','fresh_artifact_hashes'],
        HWPX_range_and_name_parameter_mapping='UNOBSERVED_CAPTURE_FIRST_DO_NOT_GUESS',
        caller_selected_type_or_paths_allowed=False,raw_SDK_discovery_is_not_product_admission=True,
        CPU_RAM_policy='existing_single_logical_CPU_BelowNormal_CPU_and_RAM_commit95_guards_unchanged',
        native_entry_implemented=False,native_execution_authorized=False,block_content_support_qualified=False,P09_complete=False)


def validate(plan,value):
    require(type(plan)is dict and plan==build(value),'EXACT_FIXED_PLAN_NO_AUTHORITY_OR_INPUT_INJECTION')
    require(len({r['bookmark_name']for r in plan['cases']})==8,'UNIQUE_NAMES')
    for row in plan['cases']:
        s=row['selection'];seed=row['seed_text']
        require(all(type(v)is int for v in s.values())and s['spara']==s['epara']==row['paragraph_index']
            and 0<=s['spos']<s['epos']<=len(seed)and seed[s['spos']:s['epos']]==row['selected_text'],
            'EXACT_NONEMPTY_SAME_PARAGRAPH_BMP_RANGE')
        require(digest(row['selected_text'])==row['selected_text_sha256']and digest(seed)==row['seed_text_sha256'],'EXACT_SYNTHETIC_HASHES')
    require(plan['native_entry_implemented'] is False and plan['native_execution_authorized'] is False,'NO_EXECUTION_ENTRY')
    return True
