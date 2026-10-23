//! Actual candidate/receipt coverage; original503 failed on unclosed font binary references.
//! No new test executable, Native action, file writer or product-route authority.
use super::*;
use std::io::{Cursor,Write};
use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
use hwpx_package::document_import::{fields::semantics::catalog::fonts::{
    ImportedFontLanguage, names::FontNameReplacementQuery},search::{
    reviews::selector::styles::SourceReviewStyleFilter as ReviewFilter,
    replacement::{SourceReplacementRunPolicy as Run,atoms::{
        case::{SourceCaseMode,SourceCasePolicy},width::{SourceWidthMode,SourceWidthPolicy},
        whitespace::{SourceWhitespacePolicy,SourceWhitespaceTextPolicy,SourceWhitespaceSequencePolicy,SourceWhitespaceOutput},
        unicode::SourceUnicodeNormalizationForm,
        styles::{fonts::SourceFontStyleAxis,paragraphs::{SourceParagraphStyleTarget,SourceParagraphStyleExtent,
            named::{SourceNamedParagraphStyleQuery,SourceStyleNameAxis}}}}}}};

fn filter()->Result<ReviewFilter,serde_json::Error> {
    serde_json::from_value(json!({"kind":"definition","filter":{"character_source":"run_property","font_details":{"hangul":{
        "face":{"query":"P09.Hangul.Font","regex":false,"case_sensitive":true,"whole_word":false},
        "binary_item_id_ref":{"kind":"present","value":"declared-font-Hangul"},
        "substitute":{"kind":"present","filter":{"face":{"query":"P09.Hangul.Substitute","regex":false,"case_sensitive":true,"whole_word":false}}},
        "type_info":{"kind":"present","filter":{"serif_style":{"kind":"present","value":"declared-serif"}}}}}}}))
}
fn receipt(label:&str,value:&impl serde::Serialize)->TestResult {
    let text=serde_json::to_string(value)?;
    for secret in["P09.Hangul.Font","declared-font-Hangul","P09.Hangul.Substitute","declared-serif"] {
        assert!(!text.contains(secret),"{label}: source query leaked");
    }
    assert!(text.contains("hwpx-agent.source-font-definition-filter-binding/v1"),"{label}: predicate binding missing");Ok(())
}
struct StageError {stage:&'static str,error:Box<dyn std::error::Error>}
impl std::fmt::Debug for StageError {
    fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result {
        f.debug_struct(&format!("FONT_CANDIDATE_{}",self.stage.replace('-',"_").to_ascii_uppercase())).field("error",&self.error).finish()
    }
}
impl std::fmt::Display for StageError {
    fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result {write!(f,"font candidate {} failed",self.stage)}
}
impl std::error::Error for StageError {
    fn source(&self)->Option<&(dyn std::error::Error+'static)>{Some(self.error.as_ref())}
}
fn declared_resources(raw:&[u8])->Result<Vec<u8>,Box<dyn std::error::Error>> {
    // Opaque fixture bytes close only package/ID edges, never actual font validity or activation.
    let mut resources=Vec::new();let mut items=String::new();
    for language in["Hangul","Latin","Hanja","Japanese","Other","Symbol","User"] {
        for kind in["font","substitute"] {
            let id=format!("declared-{kind}-{language}");let path=format!("BinData/{id}.bin");
            items.push_str(&format!("<o:item id='{id}' href='{path}' media-type='application/octet-stream'/>"));resources.push(path);
        }
    }
    let mut reader=hwpx_package::BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let mut writer=ZipWriter::new(Cursor::new(Vec::new()));
    for index in 0..reader.entries().len() {
        let path=reader.entries()[index].path.as_str().to_owned();let mut bytes=reader.read_entry(index)?;
        if path=="Contents/content.hpf" {
            let original=String::from_utf8(bytes)?;assert_eq!(original.matches("</o:manifest>").count(),1);
            bytes=original.replace("</o:manifest>",&format!("{items}</o:manifest>")).into_bytes();
        }
        writer.start_file(path,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;writer.write_all(&bytes)?;
    }
    for path in resources {
        writer.start_file(path,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        writer.write_all(b"opaque non-font fixture resource")?;
    }Ok(writer.finish()?.into_inner())
}
pub(super) fn verify()->TestResult {
    // Each operation starts from the same fresh original, never from another operation's output.
    let missing=fixture::package(&fixture::p(1,"K K  à",0))?;let f=forms(&missing)?;
    assert!(matches!(f.lower_review_selector_case_candidate(&missing,q("K"),Scope::Document,Policy::default(),Some(filter()?),
        SourceCaseMode::Lowercase,SourceCasePolicy::UnicodeDefaultEachMatchedTextGroup,Default::default(),Default::default()),
        Err(hwpx_package::document_import::search::replacement::SourceLiteralReplacementError::Patch("id_index_validation_failed"))));
    let raw=declared_resources(&missing)?;let original=raw.clone();let f=forms(&raw)?;
    let run=Run::FirstOriginalRunRetainAllRuns;
    macro_rules! check {
        ($label:literal,$candidate:expr)=>{{
            let candidate=$candidate.map_err(|error|StageError {stage:$label,error:Box::new(error)})?;receipt($label,candidate.receipt())?;
            let after=candidate.with_verified_bytes(<[u8]>::to_vec).map_err(|error|StageError {stage:$label,error:Box::new(error)})?;
            assert_ne!(after,raw,"{}: no actual output change",$label);let _parsed=forms(&after).map_err(|error|StageError {stage:$label,error})?;
            assert_eq!(raw,original,"{}: original bytes changed",$label);
        }};
    }
    check!("case",f.lower_review_selector_case_candidate(&raw,q("K"),Scope::Document,Policy::default(),Some(filter()?),
        SourceCaseMode::Lowercase,SourceCasePolicy::UnicodeDefaultEachMatchedTextGroup,Default::default(),Default::default()));
    check!("width",f.lower_review_selector_width_candidate(&raw,q("K"),Scope::Document,Policy::default(),Some(filter()?),
        SourceWidthMode::Fullwidth,SourceWidthPolicy::Unicode17WidthPairsWithKanaPairs,run,Default::default(),Default::default()));
    let spaces=SourceWhitespacePolicy {text:SourceWhitespaceTextPolicy::AsciiSpace,tabs:false,line_breaks:false,
        sequence:SourceWhitespaceSequencePolicy::CollapseEachMatchedSequence,output:SourceWhitespaceOutput::Spaces {count:1}};
    check!("whitespace",f.lower_review_selector_whitespace_candidate(&raw,q("  "),Scope::Document,Policy::default(),Some(filter()?),
        spaces,run,Default::default(),Default::default()));
    check!("unicode",f.lower_review_selector_unicode_matches(&raw,q("à"),Scope::Document,Policy::default(),Some(filter()?),
        SourceUnicodeNormalizationForm::Nfd,run,Default::default(),Default::default()));
    check!("run-style",f.lower_review_selector_style_candidate(&raw,q("K"),Scope::Document,Policy::default(),filter()?,1,
        Default::default(),Default::default()));
    check!("text-style",f.lower_review_selector_text_style_candidate(&raw,q("K"),Scope::Document,Policy::default(),filter()?,1,
        Default::default(),Default::default()));
    check!("paragraph-style",f.lower_review_selector_paragraph_style_candidate(&raw,q("K"),Scope::Document,Policy::default(),filter()?,
        SourceParagraphStyleTarget::ParagraphProperty(1),SourceParagraphStyleExtent::WholeMatchedParagraphWithinScope,Default::default(),Default::default()));
    let font_query=FontNameReplacementQuery {query:"P09.Hangul.Font",replacement:"Other.Hangul.Font",regex:false,
        case_sensitive:true,whole_word:false,languages:&[ImportedFontLanguage::Hangul]};
    check!("font",f.lower_scoped_font_filtered_candidate(&raw,font_query,Scope::Document,Policy::default(),SourceFontStyleAxis::RunProperty,
        filter()?,Default::default(),Default::default()));
    let style_query=SourceNamedParagraphStyleQuery {query:"Normal",replacement:"Body",regex:false,case_sensitive:true,whole_word:false,
        name_axis:SourceStyleNameAxis::EnglishName};
    check!("named-style",f.lower_filtered_named_paragraph_style_candidate(&raw,style_query,Scope::Document,Policy::default(),filter()?,
        Default::default(),Default::default()));
    Ok(())
}
