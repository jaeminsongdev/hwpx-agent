# Private candidate worker only. Dot-sourcing never opens documents or creates COM.
Set-StrictMode -Version Latest

function Assert-P09ClickFormatPlan {
    param([Parameter(Mandatory)]$Plan,[Parameter(Mandatory)][string]$InputSha256)
    $keys=@($Plan.PSObject.Properties.Name | Sort-Object)
    $required=@('schema_version','case_id','source_package_sha256','source_package_bytes','source_section_sha256',
        'field_name','native_begin_id','native_field_id','parameters_sha256','source_character_definition_sha256',
        'source_character_style_ref','source_field_text_sha256','new_text','new_text_sha256','character',
        'formatting_policy','source_character_runs_uniform','native_runtime_qualified','render_differential_qualified','p09_complete')
    if (($keys -join '|') -cne (($required | Sort-Object) -join '|') -or
        $Plan.schema_version -cne 'hwpx-agent.private-click-here-format-preservation-plan/v1' -or
        $Plan.case_id -cnotin @('P09-54-C01','P09-54-C02') -or
        $Plan.source_package_sha256 -cne $InputSha256 -or
        $Plan.field_name -cne 'p09-click-field' -or
        $Plan.formatting_policy -cne 'preserve_entire_uniform_source_selected_character_parameter_set' -or
        $Plan.source_character_runs_uniform -isnot [bool] -or -not $Plan.source_character_runs_uniform -or
        $Plan.native_runtime_qualified -isnot [bool] -or $Plan.native_runtime_qualified -or
        $Plan.render_differential_qualified -isnot [bool] -or $Plan.render_differential_qualified -or
        $Plan.p09_complete -isnot [bool] -or $Plan.p09_complete) { throw 'P09_CLICK_FORMAT_PLAN_SCOPE' }
    foreach ($key in @('source_package_sha256','source_section_sha256','parameters_sha256',
        'source_character_definition_sha256','source_field_text_sha256','new_text_sha256')) {
        if ($Plan.$key -isnot [string] -or $Plan.$key -cnotmatch '^[0-9a-f]{64}$') { throw 'P09_CLICK_FORMAT_PLAN_HASH' }
    }
    foreach ($key in @('source_package_bytes','native_begin_id','native_field_id','source_character_style_ref')) {
        if (($Plan.$key -isnot [int] -and $Plan.$key -isnot [long]) -or $Plan.$key -lt 0 -or
            $Plan.$key -gt [int]::MaxValue) { throw 'P09_CLICK_FORMAT_PLAN_INTEGER' }
    }
    if ($Plan.source_package_bytes -lt 1 -or $Plan.source_package_bytes -gt 4194304 -or
        $Plan.native_begin_id -ne 1210042100 -or $Plan.native_field_id -ne 627272811 -or
        $Plan.new_text -isnot [string] -or $Plan.new_text.Length -lt 1 -or
        [Text.Encoding]::UTF8.GetByteCount($Plan.new_text) -gt 65536 -or
        $Plan.new_text -match '[\x00-\x1f\x7f]') { throw 'P09_CLICK_FORMAT_PLAN_PROFILE' }
    if ((Get-P09ClickTextSha $Plan.new_text) -cne $Plan.new_text_sha256) { throw 'P09_CLICK_FORMAT_PLAN_TEXT_HASH' }
    $character=$Plan.character
    if ((@($character.PSObject.Properties.Name | Sort-Object) -join '|') -cne 'bold|face_names|foreground_rgb|height|italic' -or
        ($character.foreground_rgb -isnot [int] -and $character.foreground_rgb -isnot [long]) -or
        $character.foreground_rgb -lt 0 -or $character.foreground_rgb -gt 16777215 -or
        ($character.height -isnot [int] -and $character.height -isnot [long]) -or
        $character.height -lt 1 -or $character.height -gt 1000000 -or
        $character.italic -isnot [bool] -or $character.bold -isnot [bool]) { throw 'P09_CLICK_FORMAT_PLAN_CHARACTER' }
    $faces=$character.face_names
    if ((@($faces.PSObject.Properties.Name | Sort-Object) -join '|') -cne
        'FaceNameHangul|FaceNameHanja|FaceNameJapanese|FaceNameLatin|FaceNameOther|FaceNameSymbol|FaceNameUser') {
        throw 'P09_CLICK_FORMAT_PLAN_FONTS'
    }
    foreach ($value in $faces.PSObject.Properties.Value) {
        if ($value -isnot [string] -or $value.Length -lt 1 -or $value.Length -gt 256 -or $value -match '[\x00-\x1f\x7f]') {
            throw 'P09_CLICK_FORMAT_PLAN_FONTS'
        }
    }
}

function Get-P09ClickTextSha {
    param([AllowEmptyString()][string]$Value)
    $algorithm=[Security.Cryptography.SHA256]::Create()
    try { return (($algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)) | ForEach-Object {$_.ToString('x2')}) -join '') }
    finally {$algorithm.Dispose()}
}

function Assert-P09ClickStyleValues {
    param([Parameter(Mandatory)]$Actual,[Parameter(Mandatory)]$Character,[Parameter(Mandatory)][uint32]$NativeColor)
    if ($Actual.SetID -cne 'CharShape') { throw 'P09_CLICK_FORMAT_NATIVE_PARAMETER_KIND' }
    foreach ($key in @('TextColor','Italic','Bold','Height')+$Character.face_names.PSObject.Properties.Name) {
        if (-not $Actual.ItemExist($key)) { throw 'P09_CLICK_FORMAT_NATIVE_MIXED_OR_MISSING_STYLE' }
    }
    foreach ($pair in @(@('TextColor',[long]$NativeColor),@('Italic',[long][int]$Character.italic),
        @('Bold',[long][int]$Character.bold),@('Height',[long]$Character.height))) {
        $value=$Actual.Item($pair[0])
        if (($value -isnot [int] -and $value -isnot [uint32] -and $value -isnot [uint16] -and $value -isnot [byte]) -or
            [long]$value -ne $pair[1]) { throw 'P09_CLICK_FORMAT_NATIVE_SOURCE_STYLE_MISMATCH' }
    }
    foreach ($property in $Character.face_names.PSObject.Properties) {
        $value=$Actual.Item($property.Name)
        if ($value -isnot [string] -or $value -cne $property.Value) { throw 'P09_CLICK_FORMAT_NATIVE_SOURCE_FONT_MISMATCH' }
    }
}

function Select-P09ClickField {
    param([Parameter(Mandatory)]$Hwp,[Parameter(Mandatory)]$Plan)
    # Official PDF pp14-15/18 and actual installed declarations. Never SelectAll.
    if ($Hwp.MoveToField($Plan.field_name,$true,$true,$true) -ne $true -or
        $Hwp.GetCurFieldName(0) -cne $Plan.field_name -or
        $Hwp.SelectionMode -isnot [int] -or ($Hwp.SelectionMode -band 15) -eq 0 -or
        $Hwp.CurFieldState -isnot [int] -or ($Hwp.CurFieldState -band 15) -ne 2 -or
        ($Hwp.CurFieldState -band 16) -eq 0) { throw 'P09_CLICK_FORMAT_NATIVE_FIELD_SELECTION_REJECTED' }
}

function Invoke-P09ClickFormatPreservation {
    param([Parameter(Mandatory)]$Hwp,[Parameter(Mandatory)]$Plan,[Parameter(Mandatory)][string]$InputSha256)
    Assert-P09ClickFormatPlan $Plan $InputSha256
    # Reuse only pinned detached parameter-copy helpers; no original worker is invoked.
    $library=Join-Path $PSScriptRoot 'native-form-control-binding.ps1'
    $algorithm=[Security.Cryptography.SHA256]::Create()
    try {$hash=(($algorithm.ComputeHash([IO.File]::ReadAllBytes($library)) | ForEach-Object {$_.ToString('x2')}) -join '')}
    finally {$algorithm.Dispose()}
    if ($hash -cne 'c0534e9bfdcb0d4e93cd8535585d462df59813c7d9788f7b55afcf4d23c48183') { throw 'P09_CLICK_FORMAT_COPY_LIBRARY_DRIFT' }
    . $library
    $baseline=$null; $current=$null; $position=$null; $rollback='not_needed'; $modified=$false
    $phase='source_inventory'
    try {
        if ($Hwp.EditMode -isnot [int] -or $Hwp.EditMode -ne 1 -or $Hwp.GetFieldList(0,2) -cne $Plan.field_name -or
            (Get-P09ClickTextSha ($Hwp.GetFieldText($Plan.field_name))) -cne $Plan.source_field_text_sha256) {
            throw 'P09_CLICK_FORMAT_NATIVE_SOURCE_FIELD_MISMATCH'
        }
        $originalText=$Hwp.GetFieldText($Plan.field_name)
        $position=$Hwp.GetPosBySet()
        Select-P09ClickField $Hwp $Plan
        $phase='complete_source_style_clone'
        $current=$Hwp.CharShape
        $baseline=Copy-P09FormParameters $current
        Release-P09FormCom $current; $current=$null
        $rgb=$Plan.character.foreground_rgb
        $nativeColor=$Hwp.RGBColor([byte](($rgb -shr 16) -band 255),[byte](($rgb -shr 8) -band 255),[byte]($rgb -band 255))
        if ($nativeColor -isnot [int] -or $nativeColor -lt 0 -or $nativeColor -gt 16777215) { throw 'P09_CLICK_FORMAT_NATIVE_RGB_REJECTED' }
        Assert-P09ClickStyleValues $baseline $Plan.character ([uint32]$nativeColor)
        $phase='native_text_replacement'
        $modified=$true
        [void]$Hwp.PutFieldText($Plan.field_name,$Plan.new_text)
        if ($Hwp.GetFieldList(0,2) -cne $Plan.field_name -or
            (Get-P09ClickTextSha ($Hwp.GetFieldText($Plan.field_name))) -cne $Plan.new_text_sha256) {
            throw 'P09_CLICK_FORMAT_NATIVE_NEW_TEXT_MISMATCH'
        }
        Select-P09ClickField $Hwp $Plan
        $phase='complete_source_style_application'
        $Hwp.CharShape=$baseline
        Select-P09ClickField $Hwp $Plan
        $current=$Hwp.CharShape
        Assert-P09ClickStyleValues $current $Plan.character ([uint32]$nativeColor)
        if (-not $current.IsEquivalent($baseline)) { throw 'P09_CLICK_FORMAT_NATIVE_COMPLETE_STYLE_MISMATCH' }
        if ((Get-P09ClickTextSha ($Hwp.GetFieldText($Plan.field_name))) -cne $Plan.new_text_sha256 -or
            $Hwp.GetFieldList(0,2) -cne $Plan.field_name) { throw 'P09_CLICK_FORMAT_NATIVE_FIELD_CHANGED_AFTER_STYLE' }
        if ($Hwp.SetPosBySet($position) -ne $true) { throw 'P09_CLICK_FORMAT_NATIVE_CARET_RESTORE_FAILED' }
        return [ordered]@{state='runtime_text_and_complete_selected_style_check_not_saved_package_acceptance';
            source_and_result_text_sha256_checked=$true; entire_selected_parameter_set_equivalent=$true;
            source_style_rgb_italic_bold_height_and_seven_fonts_checked=$true; selection_is_exact_unique_named_field=$true;
            native_ids_are_source_observations_not_runtime_binding=$true; raw_document_values_present=$false;
            native_save_reopen_render_or_differential_qualified=$false; p09_complete=$false}
    }
    catch {
        if ($modified) {
            $rollback='attempted_text_style_restore_not_original_empty_field_or_package_proof'
            try {
                [void]$Hwp.PutFieldText($Plan.field_name,$originalText)
                Select-P09ClickField $Hwp $Plan
                $Hwp.CharShape=$baseline
                $restored=$null
                try {
                    $restored=$Hwp.CharShape
                    if ((Get-P09ClickTextSha ($Hwp.GetFieldText($Plan.field_name))) -cne $Plan.source_field_text_sha256 -or
                        -not $restored.IsEquivalent($baseline)) {throw 'P09_CLICK_FORMAT_NATIVE_ROLLBACK_MISMATCH'}
                    $rollback='text_style_restored_original_empty_field_dirty_state_and_package_unverified'
                } finally {Release-P09FormCom $restored}
            } catch {$rollback='failed_preserve_trace_and_close_owned_session_without_save'}
        }
        $cause=if ($_.Exception.Message -cmatch '^P09_CLICK_FORMAT_[A-Z_]+$') {$_.Exception.Message} else {'P09_CLICK_FORMAT_NATIVE_EXCEPTION_NO_RAW_VALUES'}
        $failure=[Exception]::new('P09_CLICK_FORMAT_NATIVE_FAILED')
        $failure.Data['failed_phase']=$phase; $failure.Data['error_code']=$cause; $failure.Data['rollback_state']=$rollback
        throw $failure
    }
    finally {Release-P09FormCom $current; Release-P09FormCom $baseline; Release-P09FormCom $position}
}
