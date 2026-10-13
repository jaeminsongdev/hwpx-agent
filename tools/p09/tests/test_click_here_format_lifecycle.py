"""P55 offline/actual preflight checks only. ExecuteNative is never passed."""
import base64
import copy
import io
import json
import subprocess
import unittest
import zipfile
from tools.p09 import click_here_format_lifecycle as p


def repack(raw, transform=lambda name, content: content, extra=None):
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as target:
        for item in source.infolist():
            target.writestr(item.filename, transform(item.filename, source.read(item)))
        if extra:
            target.writestr(extra, b'x')
    return output.getvalue()


class ClickHereFormatLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.plans = p.original_inputs()

    def test_exact_original_two_inputs_and_frozen_worker_plans(self):
        self.assertEqual([r['case_id'] for r in self.rows], ['P09-55-C01','P09-55-C02'])
        self.assertEqual([r['worker_plan_case_id'] for r in self.rows], ['P09-54-C01','P09-54-C02'])
        for row, plan in zip(self.rows, self.plans):
            self.assertEqual(p.sha(p.canonical(plan)), row['plan_sha256'])
            self.assertFalse(row['native_runtime_qualified'])

    def test_complete_actual_sdk_packages_pass_source_comparison_only(self):
        for row in self.rows:
            raw = p.m.prior.candidate.bounded(p.ROOT/row['sdk_expected_file'])
            result = p.compare_saved_package(row['case_id'],raw)
            self.assertTrue(result['whole_expanded_bytes_exact'])
            self.assertTrue(result['complete_click_here_observed_section_state_exact'])
            self.assertFalse(result['native_runtime_rollback_or_render_differential_qualified'] or result['p09_complete'])

    def test_archive_storage_change_is_not_document_change_or_native_proof(self):
        for row in self.rows:
            raw = p.m.prior.candidate.bounded(p.ROOT/row['sdk_expected_file'])
            rewritten = repack(raw)
            self.assertNotEqual(raw, rewritten)
            result = p.compare_saved_package(row['case_id'],rewritten)
            self.assertTrue(result['whole_expanded_bytes_exact'] and result['archive_recompression_only'])
            self.assertFalse(result['native_runtime_rollback_or_render_differential_qualified'])

    def test_unmanaged_header_change_rejects_even_when_field_state_exact(self):
        row = self.rows[0]; raw = p.m.prior.candidate.bounded(p.ROOT/row['sdk_expected_file'])
        changed = repack(raw,lambda name,b: b+b' ' if name == 'Contents/header.xml' else b)
        result = p.compare_saved_package(row['case_id'],changed)
        self.assertTrue(result['complete_click_here_observed_section_state_exact'])
        self.assertFalse(result['whole_expanded_bytes_exact'])
        self.assertEqual(result['changed_parts_count'],1)

    def test_extra_part_and_actual_original_source_cannot_be_accepted_as_result(self):
        row = self.rows[0]; raw = p.m.prior.candidate.bounded(p.ROOT/row['sdk_expected_file'])
        extra = p.compare_saved_package(row['case_id'],repack(raw,extra='Unmapped/extra.bin'))
        self.assertEqual(extra['extra_parts_count'],1)
        self.assertFalse(extra['whole_expanded_bytes_exact'])
        source = p.m.prior.candidate.bounded(p.ROOT/row['source_file'])
        self.assertFalse(p.compare_saved_package(row['case_id'],source)['whole_expanded_bytes_exact'])

    def test_bad_zip_or_foreign_case_rejects_without_raw_values(self):
        for raw in (b'not-a-package', repack(p.m.prior.candidate.bounded(p.ROOT/self.rows[0]['sdk_expected_file']),extra='../alias')):
            with self.assertRaises((ValueError, zipfile.BadZipFile)):
                p.compare_saved_package('P09-55-C01',raw)
        self.assertRaises(ValueError,p.compare_saved_package,'P09-55-C03',b'x')

    def test_fixed_full_preflight_commands_cannot_be_native_or_foreign(self):
        for row in self.rows:
            command = p.preflight_command(row)
            self.assertEqual(command[-1],'-PreflightOnly')
            self.assertNotIn('-ExecuteNative',command)
        changed = copy.deepcopy(self.rows[0]); changed['source_file']='alias'
        self.assertRaises(ValueError,p.preflight_command,changed)

    def test_read_only_result_checker_pure_fixture_detects_whole_style_mismatch(self):
        script = r"""
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. 'D:/개발/hwpx-agent/implementation/p09/tools/native-form-control-binding.ps1'
. 'D:/개발/hwpx-agent/implementation/p09/tools/click-here-format-preservation.ps1'
. 'D:/개발/hwpx-agent/implementation/p09/tools/click-here-format-lifecycle.ps1'
$plan=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:P55_PURE_PLAN))|ConvertFrom-Json
$values=@{TextColor=[uint32]255;Italic=[uint16]1;Bold=[uint16]0;Height=[int]1000}
foreach($font in $plan.character.face_names.PSObject.Properties){$values[$font.Name]=$font.Value}
$style=[pscustomobject]@{SetID='CharShape';Values=$values;Unmanaged='original'}
$style|Add-Member ScriptMethod ItemExist {param($key) $this.Values.ContainsKey($key)}
$style|Add-Member ScriptMethod Item {param($key) $this.Values[$key]}
$style|Add-Member ScriptMethod IsEquivalent {param($other) $this.Unmanaged -ceq $other.Unmanaged}
$original=[pscustomobject]@{Unmanaged='original'}
$hwp=[pscustomobject]@{SelectionMode=[int]1;CurFieldState=[int]18;CharShape=$style;Plan=$plan;PositionRestores=0;Text=$plan.new_text}
$hwp|Add-Member ScriptMethod GetFieldList {param($a,$b) $this.Plan.field_name}
$hwp|Add-Member ScriptMethod GetFieldText {param($n) $this.Text}
$hwp|Add-Member ScriptMethod GetCurFieldName {param($n) $this.Plan.field_name}
$hwp|Add-Member ScriptMethod GetPosBySet {[pscustomobject]@{List=0;Para=0;Pos=0}}
$hwp|Add-Member ScriptMethod SetPosBySet {param($p) $this.PositionRestores++;return $true}
$hwp|Add-Member ScriptMethod MoveToField {param($name,$text,$start,$select) return $true}
$hwp|Add-Member ScriptMethod PutFieldText {throw 'PURE_RESULT_CHECKER_MUST_NOT_WRITE'}
$baseline=[pscustomobject]@{parameters=$original;native_color=[uint32]255}
$positive=Confirm-P55ResultCharacterBaseline $hwp $plan $baseline
if(-not $positive.complete_selected_parameter_set_equivalent -or $positive.document_style_or_text_write_invoked){throw 'PURE_POSITIVE_SCOPE'}
$style.Unmanaged='changed';$rejected=$false
try{Confirm-P55ResultCharacterBaseline $hwp $plan $baseline|Out-Null}catch{$rejected=$true}
if(-not $rejected){throw 'PURE_UNMANAGED_ACCEPTED'}
$style.Unmanaged='original';$hwp.Text='wrong';$rejected=$false
try{Confirm-P55ResultCharacterBaseline $hwp $plan $baseline|Out-Null}catch{$rejected=$true}
if(-not $rejected){throw 'PURE_WRONG_TEXT_ACCEPTED'}
@{pure_fixture=$true;positive=1;negative=2;restores=$hwp.PositionRestores;native_worker_invoked=$false}|ConvertTo-Json -Compress
"""
        env = p.m.prior.environment.child_environment()
        env['P55_PURE_PLAN'] = base64.b64encode(p.canonical(self.plans[0])).decode('ascii')
        result = subprocess.run([p.m.prior.environment.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-EncodedCommand',
            base64.b64encode(script.encode('utf-16-le')).decode('ascii')],env=env,cwd=p.ROOT,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,'pure read-only style fixture failed')
        observed = json.loads(result.stdout.decode('utf-8-sig'))
        self.assertTrue(observed['pure_fixture'])
        self.assertEqual(observed['negative'],2)
        self.assertFalse(observed['native_worker_invoked'])

    def test_runner_ast_and_exact_preflight_exit_precede_every_native_action(self):
        runner = (p.ROOT/p.HARNESS).read_text(encoding='utf-8')
        prefix, native = runner.split('# P55_NATIVE_BOUNDARY:',1)
        self.assertIn('if ($PreflightOnly)',prefix)
        for forbidden in ('-ComObject','New-Item','RegisterModule(','.Open(','.SaveAs(','.Quit('):
            self.assertNotIn(forbidden,prefix)
        self.assertIn('if ([bool]$PreflightOnly -eq [bool]$ExecuteNative)',prefix)
        self.assertIn('$owner.window.WindowHandle',native)
        self.assertIn('$Owner.documents.Close($false)',native)
        self.assertIn('Test-P55Owner $Owner',native)
        self.assertIn('Get-P55SourceCharacterBaseline $owner.hwp $plan',native)
        self.assertEqual(native.count('Get-P55SourceCharacterBaseline $owner.hwp $plan'),2)
        self.assertNotIn('Stop-Process',runner)
        self.assertNotIn('Set-ItemProperty',runner)
        library = (p.ROOT/p.LIBRARY).read_text(encoding='utf-8')
        self.assertNotIn('PutFieldText(',library)
        self.assertNotRegex(library,r'\$Hwp\.CharShape\s*=')

    def test_actual_preflight_for_both_cases_and_wrong_hash_rejections(self):
        p.inspect_bundle()
        for row in self.rows:
            result = subprocess.run(p.preflight_command(row),cwd=p.ROOT,env=p.m.prior.environment.child_environment(),
                capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,'actual x86 STA no-COM preflight failed')
            value = json.loads(result.stdout.decode('utf-8-sig'))
            self.assertEqual(value['state'],'preflight_pass_no_com_no_run_directory')
            self.assertTrue(value['no_com_server_activation'])
            self.assertFalse(value['native_run_directory_created'])
            self.assertFalse((p.ROOT/row['run_directory']).exists())
        for keyword in ('plan_sha','harness_sha'):
            result = subprocess.run(p.preflight_command(self.rows[0],**{keyword:'0'*64}),cwd=p.ROOT,
                env=p.m.prior.environment.child_environment(),capture_output=True,timeout=30)
            self.assertNotEqual(result.returncode,0)
            self.assertIn(b'P55_PLAN_SCOPE' if keyword == 'plan_sha' else b'P55_FILE_IDENTITY',result.stderr)
        command=p.preflight_command(self.rows[0]);command[command.index('-ExpectedLifecycleLibrarySha256')+1]='0'*64
        result=subprocess.run(command,cwd=p.ROOT,env=p.m.prior.environment.child_environment(),capture_output=True,timeout=30)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'P55_FILE_IDENTITY',result.stderr)
        p.m.prior.hwp_zero()

    def test_actual_cleanup_and_window_api_declarations_only_not_runtime(self):
        result = subprocess.run(['pwsh','-NoLogo','-NoProfile','-NonInteractive','-File',str(p.ROOT/p.INSPECTOR)],
            cwd=p.ROOT,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,'static lifecycle declarations failed')
        value = json.loads(result.stdout.decode('utf-8-sig'))
        self.assertTrue(value['no_com_server_activation'] and value['hwp_process_set_unchanged'])
        libraries = [b['surface'] for b in value['binaries'] if b['state']=='type_library_read']
        self.assertEqual(len(libraries),1)
        types = {t['name']:t for t in libraries[0]['selected_types']}
        for typename,name,member_id,kind,returns,parameters in [
            ('IXHwpWindow','WindowHandle',10,'INVOKE_PROPERTYGET',3,[]),
            ('IXHwpDocument','Close',15000,'INVOKE_FUNC',11,[('isDirty',11)]),
            ('IXHwpDocuments','Close',15001,'INVOKE_FUNC',24,[('isDirty',11)]),
            ('IHwpObject','Quit',30000,'INVOKE_FUNC',24,[]),
            ('IXHwpDocument','SaveAs',15002,'INVOKE_FUNC',11,[('Path',8),('Format',12),('arg',12)])]:
            rows = [r for r in types[typename]['members'] if r['name']==name and r['invoke_kind']==kind]
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0],{'name':name,'member_id':member_id,'invoke_kind':kind,'return_variant_type':returns,
                'parameters':[{'name':n,'variant_type':vt,'flags':1} for n,vt in parameters]})


if __name__ == '__main__':
    unittest.main()
