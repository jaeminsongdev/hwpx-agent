"""Real original fixtures and pure worker checks; no mock is native evidence."""
import copy
import io
import json
import os
import subprocess
import unittest
import zipfile
from tools.p09 import native_form_control_plan as q

LIBRARY = 'implementation/p09/tools/native-form-control-binding.ps1'


def pure_worker(plans, mutation='none', shell='pwsh'):
    # Dot-source only. Deliberately NEVER calls Invoke-P09NativeFormBinding,
    # COM activation, property setters, Open/Save or any user interaction.
    command = r'''
$ErrorActionPreference='Stop'
[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
. ./implementation/p09/tools/native-form-control-binding.ps1
$tokens=$null; $errors=$null
[void][Management.Automation.Language.Parser]::ParseFile(
    (Join-Path (Get-Location).Path 'implementation/p09/tools/run-hancom-2020-native-form-control-binding.ps1'),
    [ref]$tokens,[ref]$errors)
if($errors.Count -ne 0){throw 'WORKER_PARSE_FAILED'}
$before=@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" | Select-Object -ExpandProperty ProcessId | Sort-Object)
$request=[Console]::In.ReadToEnd() | ConvertFrom-Json
$cases=0; $controls=0; $rejected=0; $allNames=[Collections.Generic.List[string]]::new()
foreach($plan in $request.plans) {
    foreach($intent in $plan.controls){$allNames.Add($intent.name)}
    try {
        Assert-P09FormPlan $plan $plan.source_package_sha256
        $observed=@($plan.controls | ForEach-Object {
            $p=$_.runtime_anchor_candidate.Para
            [pscustomobject]@{ctrl_type=$_.native_ctrl_type;
                local_anchor=[pscustomobject]@{List=0;Para=$p;Pos=23};
                top_anchor=[pscustomobject]@{List=0;Para=$p;Pos=23};
                root_anchor=[pscustomobject]@{List=0;Para=$p;Pos=23} }
        })
        [array]::Reverse($observed)
        switch($request.mutation) {
            'wrong_para' { $observed[0].root_anchor.Para+=1 }
            'wrong_list' { $observed[0].root_anchor.List=1 }
            'wrong_pos_scope' { $observed[0].top_anchor.Pos=24 }
            'coerced_pos' { $observed[0].root_anchor.Pos='23' }
            'wrong_type' { $observed[0].ctrl_type='+rbt' }
            'missing_control' { $observed=@() }
            'extra_control' { $observed+= $observed[0] }
            'duplicate_anchor' { $observed=@($observed[0],$observed[0]) }
        }
        $matched=@(Resolve-P09FormTargets $plan $observed)
        foreach($target in $matched) {
            if($target.intent.runtime_anchor_candidate.Para -ne $target.observed.root_anchor.Para -or
               $target.intent.native_ctrl_type -cne $target.observed.ctrl_type) {throw 'WRONG_MATCH'}
        }
        $cases+=1; $controls+=$matched.Count
    } catch {$rejected+=1}
}
$after=@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" | Select-Object -ExpandProperty ProcessId | Sort-Object)
if(($before -join ',') -ne ($after -join ',')){throw 'PROCESS_SET_CHANGED'}
$algorithm=[Security.Cryptography.SHA256]::Create()
try {$namesSha=(($algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes(($allNames -join [char]0))) | ForEach-Object {$_.ToString('x2')}) -join '')}
finally {$algorithm.Dispose()}
@{cases=$cases;controls=$controls;rejected=$rejected;native_execution=$false;intent_names_sha256=$namesSha} | ConvertTo-Json -Compress
'''
    result = subprocess.run([shell, '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', command],
        input=json.dumps({'plans': plans, 'mutation': mutation}, ensure_ascii=False).encode('utf-8'),
        cwd=q.ROOT, capture_output=True, timeout=30, check=False)
    if result.returncode != 0 or result.stderr.strip():
        raise AssertionError('pure_worker_failed_no_native_execution')
    observed=json.loads(result.stdout)
    expected=q.sha('\0'.join(c['name'] for p in plans for c in p['controls']).encode('utf-8'))
    if observed.pop('intent_names_sha256') != expected:
        raise AssertionError('pure_worker_unicode_or_metachar_plan_value_changed')
    return observed


class NativeFormControlPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans = q.original_plans()
        manifest_raw=q.prior.color.history.progress.original.public.checked(q.ROOT/q.MANIFEST,q.MANIFEST_SHA,4194304)
        cls.rows=json.loads(manifest_raw)['cases']

    def raw(self, index=0):
        row=self.rows[index]
        return (q.ROOT/q.MANIFEST).parent.joinpath(row['file']).read_bytes()

    def altered(self, old, new, index=0):
        raw=self.raw(index)
        source=zipfile.ZipFile(io.BytesIO(raw)); output=io.BytesIO()
        with source,zipfile.ZipFile(output,'w') as target:
            for info in source.infolist():
                part=source.read(info.filename)
                if info.filename=='Contents/section0.xml':
                    self.assertIn(old,part);part=part.replace(old,new,1)
                target.writestr(info,part)
        changed=output.getvalue();row=copy.deepcopy(self.rows[index])
        row['package_sha256']=q.sha(changed);row['package_bytes']=len(changed)
        return row,changed

    def test_all_original_fifteen_complete_intents_have_missing_native_ids_and_no_runtime_claim(self):
        self.assertEqual(len(self.plans),15)
        self.assertEqual(sum(len(p['controls']) for p in self.plans),17)
        for index,p in enumerate(self.plans):
            self.assertEqual(p['case_id'],f'P09-35-C{index+1:02}')
            self.assertFalse(p['anchor_mapping_qualified']);self.assertFalse(p['native_runtime_qualified'])
            for c in p['controls']:
                self.assertEqual(c['native_identity_observation'],'missing')
                self.assertNotIn('native_object_id',c);self.assertNotIn('Pos',c['runtime_anchor_candidate'])

    def test_pure_worker_matches_all_original_cases_even_with_reversed_collection(self):
        self.assertEqual(pure_worker(self.plans),{'cases':15,'controls':17,'rejected':0,'native_execution':False})

    def test_actual_x86_windows_powershell_pure_binding_preserves_all_fifteen_unicode_plans(self):
        shell=os.path.join(os.environ['SystemRoot'],'SysWOW64','WindowsPowerShell','v1.0','powershell.exe')
        self.assertEqual(pure_worker(self.plans,shell=shell),
                         {'cases':15,'controls':17,'rejected':0,'native_execution':False})

    def test_worker_rejects_missing_extra_ambiguous_wrong_type_or_anchor_scopes_before_writes(self):
        for mutation in ('wrong_para','wrong_list','wrong_pos_scope','coerced_pos','wrong_type',
                         'missing_control','extra_control','duplicate_anchor'):
            with self.subTest(mutation=mutation):
                self.assertEqual(pure_worker([self.plans[0]],mutation)['rejected'],1)

    def test_worker_rejects_coerced_intents_and_false_runtime_promotions(self):
        changed=[]
        for field,value in [('tab_order',True),('tab_order','0'),('tab_order',0.25),('foreground_rgb',16777216),
                            ('foreground_rgb','0'),('shape_locked','false'),('native_identity_observation','reservation')]:
            p=copy.deepcopy(self.plans[0]);p['controls'][0][field]=value;changed.append(p)
        for field,value in [('anchor_mapping_qualified',True),('native_runtime_qualified','false'),
                            ('public_action_or_p09_gate',True),('source_package_bytes',True)]:
            p=copy.deepcopy(self.plans[0]);p[field]=value;changed.append(p)
        for field,value in [('List',True),('Para','1'),('Para',1.5)]:
            p=copy.deepcopy(self.plans[0]);p['controls'][0]['runtime_anchor_candidate'][field]=value;changed.append(p)
        observed=pure_worker(changed)
        self.assertEqual(observed['rejected'],len(changed));self.assertEqual(observed['cases'],0)

    def test_original_unicode_metachar_names_and_all_colors_are_exact_not_normalized(self):
        for index,name in enumerate(('P09 이름 한글','P09 이름 & 폼','P09 이름 < 폼',
                                   'P09 이름 > 폼','P09 이름 " 폼',"P09 이름 ' 폼")):
            self.assertEqual(self.plans[index+8]['controls'][0]['name'],name)
        self.assertEqual(self.plans[2]['controls'][0]['foreground_rgb'],0xCC1100)
        self.assertEqual(self.plans[3]['controls'][0]['foreground_rgb'],0x2E74B5)
        self.assertEqual([c['tab_order'] for c in self.plans[0]['controls']],[0,1])

    def test_source_substitution_protection_and_invented_native_id_are_rejected(self):
        with self.assertRaises(ValueError):q.compile_case(self.rows[0],self.raw(1))
        for old,new in [(b'<hp:edit ',b'<hp:edit id="90001" ')]:
            with self.subTest(change=new):
                row,raw=self.altered(old,new)
                with self.assertRaises(ValueError):q.compile_case(row,raw)
        raw=self.raw()  # Original bytes are never rewritten by this test.
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            section=archive.read('Contents/section0.xml')
        form=section[section.index(b'<hp:edit '):section.index(b'</hp:edit>')]
        row,changed=self.altered(form,form.replace(b'protect="0"',b'protect="1"',1))
        with self.assertRaises(ValueError):q.compile_case(row,changed)

    def test_global_duplicate_tab_names_and_nested_paragraphs_are_rejected(self):
        for old,new in [(b'tabOrder="0"',b'tabOrder="1"'),
                        (b'</hp:edit>',b'<hp:p/></hp:edit>'),
                        (b'<hp:edit ',b'<hp:edit ' + b'x="'+b'A'*2097152+b'" ')]:
            with self.subTest(change_size=len(new)):
                row,raw=self.altered(old,new)
                with self.assertRaises(ValueError):q.compile_case(row,raw)
        first,second=[c['name'] for c in self.plans[0]['controls']]
        row,raw=self.altered(('name="'+first+'"').encode(),('name="'+second+'"').encode())
        with self.assertRaises(ValueError):q.compile_case(row,raw)

    def test_installed_property_metadata_and_frozen_source_inputs_remain_exact(self):
        old=json.loads(q.prior.io.checked(q.ROOT/q.prior.CAPSULE,'ebd8e94b8826525752f4ce7b0d57ff7a289fa8772bc02e43534b1f3e3d385262'))
        self.assertEqual(q.prior.pins(),old['source_sha256'])
        self.assertEqual(q.prior.preserved_color(),old['preserved_color_source_successor'])
        actual=subprocess.run(['pwsh','-NoLogo','-NoProfile','-NonInteractive','-File',
            'tools/p09/inspect_native_form_binding_typelib.ps1'],cwd=q.ROOT,capture_output=True,timeout=30,check=False)
        self.assertEqual(actual.returncode,0);self.assertFalse(actual.stderr.strip())
        value=json.loads(actual.stdout);self.assertTrue(value['no_com_server_activation'])
        types={t['name']:t for t in value['binaries'][2]['surface']['selected_types']}
        for interface,field,kind,member,return_type,args in [
            ('IDHwpCtrlCode','GetAnchorPos','INVOKE_FUNC',15000,9,[(3,0)]),
            ('IDHwpCtrlCode','Properties','INVOKE_PROPERTYPUT',6,24,[(9,1)]),
            ('IDHwpParameterSet','Clone','INVOKE_FUNC',15000,9,[]),
            ('IDHwpParameterSet','IsEquivalent','INVOKE_FUNC',15004,11,[(9,1)]),
            ('IDHwpParameterSet','ItemExist','INVOKE_FUNC',15006,11,[(8,1)]),
            ('IDHwpParameterSet','SetItem','INVOKE_FUNC',15010,24,[(8,1),(12,1)]),
            ('HShapeObject','ShapeFormCommonAttr','INVOKE_PROPERTYGET',744,9,[]),
            ('HFormCommonAttr','name','INVOKE_PROPERTYPUT',16416,24,[(8,1)]),
            ('HFormCommonAttr','TabOrder','INVOKE_PROPERTYPUT',16421,24,[(3,1)]),
            ('HFormCommonAttr','Color','INVOKE_PROPERTYPUT',16417,24,[(19,1)]),
            ('IHwpObject','RGBColor','INVOKE_FUNC',30007,3,[(17,1),(17,1),(17,1)])]:
            members=[m for m in types[interface]['members'] if m['name']==field and m['invoke_kind']==kind]
            self.assertEqual(members,[{'name':field,'member_id':member,'invoke_kind':kind,'return_variant_type':return_type,
                'parameters':[{'variant_type':v,'flags':f} for v,f in args]}])


if __name__=='__main__':unittest.main()
