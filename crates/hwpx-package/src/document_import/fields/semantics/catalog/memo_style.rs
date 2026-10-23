//! Existing native memoPr style output only; NOT full comment/native metadata or execution.
use super::{ImportedCatalogKind, ImportedDocumentCatalog};
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PatchAttributeValue, PatchIntent, PatchLimits, PatchText, PreservationRuleProfile,
    PreservingPatchEngine, PreservingWriter, WriterError, WriterLimits, XmlAttributeSelector,
    document_import::{
        ImportedSourcePackage, fields::ImportedDocumentFields,
        fields::semantics::ImportedDocumentFieldSemantics, forms::ImportedDocumentForms,
    },
};
use domain_ir::{CommentLineType, CommentLineWidth, CommentMemoType, SourceAnchorHandle};
use serde::Serialize;
use std::{fmt, io::Cursor};
use thiserror::Error;

#[derive(Clone, Copy, Eq, PartialEq)]
pub enum MemoStyleColor {
    None,
    Rgb(u32),
}
impl MemoStyleColor {
    fn native(self) -> Result<String, MemoStyleLoweringError> {
        match self {
            Self::None => Ok("none".into()),
            Self::Rgb(value) if value <= 0xFF_FFFF => Ok(format!("#{value:06X}")),
            Self::Rgb(_) => Err(MemoStyleLoweringError::Values),
        }
    }
}
impl fmt::Debug for MemoStyleColor {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("MemoStyleColor(<redacted>)")
    }
}

/// Explicit seven native style values. Does not supply IDs, XML, metadata, locks or authority.
#[derive(Clone, Eq, PartialEq)]
pub struct MemoStyleValues {
    pub width_native_units: u32,
    pub line_width: CommentLineWidth,
    pub line_type: CommentLineType,
    pub line_color: MemoStyleColor,
    pub fill_color: MemoStyleColor,
    pub active_color: MemoStyleColor,
    pub memo_type: CommentMemoType,
}
impl fmt::Debug for MemoStyleValues {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("MemoStyleValues(<redacted>)")
    }
}
impl MemoStyleValues {
    fn native(&self) -> Result<Vec<(&'static str, String)>, MemoStyleLoweringError> {
        if self.width_native_units == 0 {
            return Err(MemoStyleLoweringError::Values);
        }
        let width = match self.line_width {
            CommentLineWidth::Mm0_1 => 0,
            CommentLineWidth::Mm0_12 => 1,
            CommentLineWidth::Mm0_15 => 2,
            CommentLineWidth::Mm0_2 => 3,
            CommentLineWidth::Mm0_25 => 4,
            CommentLineWidth::Mm0_3 => 5,
            CommentLineWidth::Mm0_4 => 6,
            CommentLineWidth::Mm0_5 => 7,
            CommentLineWidth::Mm0_6 => 8,
            CommentLineWidth::Mm0_7 => 9,
            CommentLineWidth::Mm1_0 => 10,
            CommentLineWidth::Mm1_5 => 11,
            CommentLineWidth::Mm2_0 => 12,
            CommentLineWidth::Mm3_0 => 13,
            CommentLineWidth::Mm4_0 => 14,
            CommentLineWidth::Mm5_0 => 15,
        };
        let line = match self.line_type {
            CommentLineType::None => "NONE",
            CommentLineType::Solid => "SOLID",
            CommentLineType::Dot => "DOT",
            CommentLineType::Dash => "DASH",
            CommentLineType::DashDot => "DASH_DOT",
            CommentLineType::DashDotDot => "DASH_DOT_DOT",
            CommentLineType::LongDash => "LONG_DASH",
            CommentLineType::Circle => "CIRCLE",
            CommentLineType::DoubleSlim => "DOUBLE_SLIM",
            CommentLineType::SlimThick => "SLIM_THICK",
            CommentLineType::ThickSlim => "THICK_SLIM",
            CommentLineType::SlimThickSlim => "SLIM_THICK_SLIM",
            CommentLineType::Wave => "WAVE",
            CommentLineType::DoubleWave => "DOUBLEWAVE",
            CommentLineType::Thick3d => "THICK3D",
            CommentLineType::ThickReverse3d => "THICKREV3D",
            CommentLineType::ThreeDimensional => "3D",
            CommentLineType::Reverse3d => "REV3D",
        };
        let memo = match self.memo_type {
            CommentMemoType::Normal => "NOMAL",
            CommentMemoType::UserInsert => "USER_INSERT",
            CommentMemoType::UserDelete => "USER_DELETE",
            CommentMemoType::UserUpdate => "USER_UPDATE",
        };
        Ok(vec![
            ("width", self.width_native_units.to_string()),
            ("lineWidth", width.to_string()),
            ("lineType", line.into()),
            ("lineColor", self.line_color.native()?),
            ("fillColor", self.fill_color.native()?),
            ("activeColor", self.active_color.native()?),
            ("memoType", memo.into()),
        ])
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct MemoStyleLoweringReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub output_bytes: usize,
    pub changed_attributes: usize,
    pub changed_parts: usize,
    pub unrelated_expanded_parts_exact: bool,
    pub native_author_time_state_binding_verified: bool,
    pub execution_publication_authority: bool,
}
pub struct MemoStyleOutput {
    artifact: PackageArtifact,
    receipt: MemoStyleLoweringReceipt,
}
impl fmt::Debug for MemoStyleOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("MemoStyleOutput(<redacted>)")
    }
}
impl MemoStyleOutput {
    #[must_use]
    pub const fn receipt(&self) -> &MemoStyleLoweringReceipt {
        &self.receipt
    }
    /// Artifact integrity only; stored callers need their original fresh authorization checks.
    /// # Errors
    /// Does not expose bytes if the original package writer rejects the artifact.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}

impl ImportedDocumentCatalog<'_, '_, '_> {
    /// Surgical existing-style output through ORIGINAL source/catalog/patch/writer validation.
    /// Caller anchors must be one of this source's actual memoPr definitions. No new IDs/defaults.
    /// # Errors
    /// Rejects drift, unknown selectors, invalid/no-op values, malformed ID closure or limits.
    /// Does not establish a full comment model, protection policy or product execution route.
    pub fn lower_memo_style(
        &self,
        fresh: &[u8],
        selector: &SourceAnchorHandle,
        values: &MemoStyleValues,
        writer_limits: WriterLimits,
    ) -> Result<MemoStyleOutput, MemoStyleLoweringError> {
        self.verify_source(fresh)
            .map_err(|_| MemoStyleLoweringError::Source)?;
        let source = self.meanings.fields.forms.source();
        let definition = self
            .definitions
            .iter()
            .find(|d| d.kind == ImportedCatalogKind::MemoProperty && &d.source_anchor == selector)
            .ok_or(MemoStyleLoweringError::Selection)?;
        let resolved = source
            .resolve_anchor(selector)
            .map_err(|_| MemoStyleLoweringError::Selection)?;
        let xml = resolved
            .part()
            .xml()
            .ok_or(MemoStyleLoweringError::Selection)?;
        let index = resolved
            .element_index()
            .ok_or(MemoStyleLoweringError::Selection)?;
        let element = resolved
            .element()
            .ok_or(MemoStyleLoweringError::Selection)?;
        let native = values.native()?;
        let mut intents = Vec::new();
        for (name, value) in &native {
            let (attribute_index, attribute) = element
                .attributes()
                .iter()
                .enumerate()
                .find(|(_, a)| {
                    !a.is_namespace_declaration()
                        && a.name().namespace().is_none()
                        && a.name().local_name() == *name
                })
                .ok_or(MemoStyleLoweringError::Selection)?;
            if equivalent(name, attribute.semantic_value(), value) {
                continue;
            }
            intents.push(PatchIntent::ReplaceAttribute {
                target: XmlAttributeSelector::bind(
                    resolved.part().path(),
                    xml,
                    index,
                    attribute_index,
                )
                .map_err(|_| MemoStyleLoweringError::Patch)?,
                value: PatchAttributeValue::Text(
                    PatchText::new(value).map_err(|_| MemoStyleLoweringError::Values)?,
                ),
            });
        }
        if intents.is_empty() {
            return Err(MemoStyleLoweringError::NoChange);
        }
        let limits = source
            .limits
            .zip()
            .map_err(|_| MemoStyleLoweringError::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), limits)
            .map_err(|_| MemoStyleLoweringError::Source)?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader,
            &source.graph,
            PackageGraphLimits::default(),
            IdRuleProfile::current_hancom_2020_formula_v3(),
            IdIndexLimits::default(),
            PatchLimits::default(),
            PreservationRuleProfile::Hangul2020PreviewTextV2,
            &intents,
        )
        .map_err(|_| MemoStyleLoweringError::Patch)?;
        if patch.changed_parts() != 1
            || patch.added_parts() != 0
            || patch.parts().iter().any(|p| {
                p.path() != resolved.part().path() && p.source_sha256() != Some(p.output_sha256())
            })
        {
            return Err(MemoStyleLoweringError::Preservation);
        }
        let artifact = PreservingWriter::build(
            &patch,
            limits,
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            writer_limits,
        )
        .map_err(|_| MemoStyleLoweringError::Writer)?;
        artifact
            .with_verified_bytes(|output| readback(source, output, definition.native_id, &native))
            .map_err(|_| MemoStyleLoweringError::Writer)??;
        self.verify_source(fresh)
            .map_err(|_| MemoStyleLoweringError::Source)?;
        let receipt = style_receipt(source, &artifact, intents.len());
        Ok(MemoStyleOutput { artifact, receipt })
    }
}
fn style_receipt(
    source: &ImportedSourcePackage,
    artifact: &PackageArtifact,
    changed_attributes: usize,
) -> MemoStyleLoweringReceipt {
    MemoStyleLoweringReceipt {
        qualification: "existing_native_memoPr_style_only_NOT_full_comment_metadata_native_acceptance_policy_execution_publication_or_Gate",
        source_package_sha256: source.receipt().source_package_sha256,
        output_package_sha256: artifact.sha256(),
        output_bytes: artifact.size_bytes(),
        changed_attributes,
        changed_parts: 1,
        unrelated_expanded_parts_exact: true,
        native_author_time_state_binding_verified: false,
        execution_publication_authority: false,
    }
}
fn equivalent(name: &str, before: &str, after: &str) -> bool {
    match name {
        "width" | "lineWidth" => before.parse::<u32>().ok() == after.parse::<u32>().ok(),
        "lineColor" | "fillColor" | "activeColor" => before.eq_ignore_ascii_case(after),
        _ => before == after,
    }
}
fn readback(
    source: &ImportedSourcePackage,
    output: &[u8],
    native_id: u32,
    values: &[(&str, String)],
) -> Result<(), MemoStyleLoweringError> {
    let forms = ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            output,
            source.document_id.clone(),
            sha2::Sha256::digest(output).into(),
            source.limits,
        )
        .map_err(|_| MemoStyleLoweringError::Readback)?,
    )
    .map_err(|_| MemoStyleLoweringError::Readback)?;
    let fields =
        ImportedDocumentFields::import(&forms).map_err(|_| MemoStyleLoweringError::Readback)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)
        .map_err(|_| MemoStyleLoweringError::Readback)?;
    let catalog =
        ImportedDocumentCatalog::import(&meanings).map_err(|_| MemoStyleLoweringError::Readback)?;
    let d = catalog
        .definitions()
        .iter()
        .find(|d| d.kind == ImportedCatalogKind::MemoProperty && d.native_id == native_id)
        .ok_or(MemoStyleLoweringError::Readback)?;
    let resolved = forms
        .source()
        .resolve_anchor(&d.source_anchor)
        .map_err(|_| MemoStyleLoweringError::Readback)?;
    let e = resolved.element().ok_or(MemoStyleLoweringError::Readback)?;
    for (name, expected) in values {
        if !e.attributes().iter().any(|a| {
            a.name().namespace().is_none()
                && a.name().local_name() == *name
                && equivalent(name, a.semantic_value(), expected)
        }) {
            return Err(MemoStyleLoweringError::Readback);
        }
    }
    Ok(())
}
use sha2::Digest as _;
#[derive(Debug, Error, Eq, PartialEq)]
pub enum MemoStyleLoweringError {
    #[error("memo_style_source_rejected")]
    Source,
    #[error("memo_style_selector_rejected")]
    Selection,
    #[error("memo_style_values_rejected")]
    Values,
    #[error("memo_style_no_change")]
    NoChange,
    #[error("memo_style_original_patch_rejected")]
    Patch,
    #[error("memo_style_original_writer_rejected")]
    Writer,
    #[error("memo_style_preservation_rejected")]
    Preservation,
    #[error("memo_style_original_readback_rejected")]
    Readback,
}
