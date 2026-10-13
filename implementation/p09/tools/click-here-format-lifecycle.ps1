# Functions only. Caller hash-checks and dot-sources the frozen P54/P50 helpers.
Set-StrictMode -Version Latest

function Get-P55SourceCharacterBaseline {
    param([Parameter(Mandatory)]$Hwp,[Parameter(Mandatory)]$Plan)
    Assert-P09ClickFormatPlan $Plan $Plan.source_package_sha256
    if ($Hwp.GetFieldList(0,2) -cne $Plan.field_name -or
        (Get-P09ClickTextSha ($Hwp.GetFieldText($Plan.field_name))) -cne $Plan.source_field_text_sha256) {
        throw 'P55_SOURCE_FIELD_MISMATCH'
    }
    $position=$null; $current=$null; $copy=$null; $handedOff=$false
    try {
        $position=$Hwp.GetPosBySet()
        Select-P09ClickField $Hwp $Plan
        $current=$Hwp.CharShape
        $copy=Copy-P09FormParameters $current
        $rgb=$Plan.character.foreground_rgb
        $color=$Hwp.RGBColor([byte](($rgb -shr 16) -band 255),[byte](($rgb -shr 8) -band 255),[byte]($rgb -band 255))
        if ($color -isnot [int] -or $color -lt 0 -or $color -gt 16777215) {throw 'P55_NATIVE_COLOR_TYPE'}
        Assert-P09ClickStyleValues $copy $Plan.character ([uint32]$color)
        if ($Hwp.SetPosBySet($position) -ne $true) {throw 'P55_SOURCE_POSITION_RESTORE'}
        $handedOff=$true
        return [ordered]@{parameters=$copy; native_color=[uint32]$color}
    }
    finally {
        Release-P09FormCom $position; Release-P09FormCom $current
        if (-not $handedOff) {Release-P09FormCom $copy}
    }
}

function Confirm-P55ResultCharacterBaseline {
    param([Parameter(Mandatory)]$Hwp,[Parameter(Mandatory)]$Plan,[Parameter(Mandatory)]$Baseline)
    Assert-P09ClickFormatPlan $Plan $Plan.source_package_sha256
    if ($Hwp.GetFieldList(0,2) -cne $Plan.field_name -or
        (Get-P09ClickTextSha ($Hwp.GetFieldText($Plan.field_name))) -cne $Plan.new_text_sha256) {
        throw 'P55_RESULT_FIELD_MISMATCH'
    }
    $position=$null; $current=$null
    try {
        $position=$Hwp.GetPosBySet()
        Select-P09ClickField $Hwp $Plan
        $current=$Hwp.CharShape
        Assert-P09ClickStyleValues $current $Plan.character $Baseline.native_color
        if (-not $current.IsEquivalent($Baseline.parameters)) {throw 'P55_RESULT_ENTIRE_SOURCE_STYLE_MISMATCH'}
        if ((Get-P09ClickTextSha ($Hwp.GetFieldText($Plan.field_name))) -cne $Plan.new_text_sha256 -or
            $Hwp.GetFieldList(0,2) -cne $Plan.field_name) {throw 'P55_RESULT_FIELD_DRIFT'}
        if ($Hwp.SetPosBySet($position) -ne $true) {throw 'P55_RESULT_POSITION_RESTORE'}
        return [ordered]@{state='runtime_result_matches_entire_original_selected_style';
            text_sha256_checked=$true; complete_selected_parameter_set_equivalent=$true;
            source_style_and_seven_fonts_checked=$true; document_style_or_text_write_invoked=$false;
            saved_package_or_render_or_native_rollback_qualified=$false; raw_document_values_present=$false;
            p09_complete=$false}
    }
    finally {Release-P09FormCom $position; Release-P09FormCom $current}
}
