//! Actual source-only blank table insertion using the original native renderer and package writer.
//! No full comment compiler, stored execution lease or native visual acceptance is implied.
use super::{
    ImportedDocumentReviewBodies, ReviewTableContextError, ReviewTableCreationContext, header,
    named, select_paragraph, template_binding,
};
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PackagePath, PatchIntent, PatchLimits, PreservationRuleProfile, PreservingPatchEngine,
    PreservingWriter, PreservingXmlDocument, ValidatedXmlFragment, WriterError, WriterLimits,
    XmlElementSelector,
    document_import::{ImportedSourcePackage, forms::ImportedDocumentForms},
    table_ruling_hwpx::{
        ReviewCreateContextInput, ReviewNativeTableOutput, ReviewTableRenderInput,
        render_review_table,
    },
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeMap, fmt, io::Cursor};
use thiserror::Error;

/// Requested new geometry, not observations of an existing native table.
/// Identities/style/frame are never caller-provided; native template inheritance stays explicit.
#[derive(Clone, Eq, PartialEq)]
pub struct ReviewTableDimensions {
    row_heights_hwpunit: Vec<u32>,
    column_widths_hwpunit: Vec<u32>,
}
impl fmt::Debug for ReviewTableDimensions {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ReviewTableDimensions")
            .field("rows", &self.row_heights_hwpunit.len())
            .field("columns", &self.column_widths_hwpunit.len())
            .finish_non_exhaustive()
    }
}
impl ReviewTableDimensions {
    /// # Errors
    /// Rejects empty/zero/overflowing/over-profile tracks and cell counts before native allocation.
    /// Tighter context limits are rechecked by the original grid/ruling/layout/pagination readers.
    pub fn new(rows: Vec<u32>, columns: Vec<u32>) -> Result<Self, ReviewTableOutputError> {
        let limits = domain_ir::TableGridLimits::default().config();
        let count = rows
            .len()
            .checked_mul(columns.len())
            .ok_or(ReviewTableOutputError::Values)?;
        if rows.is_empty()
            || columns.is_empty()
            || rows.len() > limits.rows as usize
            || columns.len() > limits.columns as usize
            || count > limits.slots
            || count > limits.master_cells
            || rows.iter().chain(&columns).any(|n| *n == 0)
            || rows
                .iter()
                .try_fold(0_u32, |a, b| a.checked_add(*b))
                .is_none()
            || columns
                .iter()
                .try_fold(0_u32, |a, b| a.checked_add(*b))
                .is_none()
        {
            return Err(ReviewTableOutputError::Values);
        }
        Ok(Self {
            row_heights_hwpunit: rows,
            column_widths_hwpunit: columns,
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewTableOutputAuthority {
    SourceArtifactIntegrityOnly,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewTablePreservation {
    OtherPartsAndOutsideParagraphExactHeaderNativeCoordinated,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewTableOutputReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub template_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub output_bytes: usize,
    pub target_grid_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub target_rows: u32,
    pub target_columns: u32,
    pub created_cells: usize,
    pub before_table_count_in_selected_part: usize,
    pub after_table_count_in_selected_part: usize,
    pub added_border_fills: usize,
    pub changed_parts: usize,
    pub preservation: ReviewTablePreservation,
    pub authority: ReviewTableOutputAuthority,
    pub new_table_inserted: bool,
    pub full_document_flow_bound: bool,
    pub full_comment_product_acceptance: bool,
}
pub struct ReviewTableOutput {
    artifact: PackageArtifact,
    receipt: ReviewTableOutputReceipt,
}
impl fmt::Debug for ReviewTableOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewTableOutput(<redacted>)")
    }
}
impl ReviewTableOutput {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewTableOutputReceipt {
        &self.receipt
    }
    /// Source artifact integrity only, never stored access/issuer/execution/publication authority.
    /// # Errors
    /// Rejects artifact integrity failure before exposing any package bytes.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}

impl ReviewTableCreationContext<'_, '_> {
    /// Replace the actual empty review paragraph with one original-template native blank table.
    /// Both source archives and all original template/protection guards are replayed first.
    /// Requested geometry is explicit; frame/style/native identity are inherited, not guessed.
    /// # Errors
    /// Rejects source drift, unsafe/over-limit geometry, actual whole-package native table-ID
    /// collision, original rendering/patch/ID/writer/readback or outside preservation failure.
    pub fn lower_table(
        &self,
        fresh: &[u8],
        fresh_template: &[u8],
        dimensions: &ReviewTableDimensions,
        writer_limits: WriterLimits,
    ) -> Result<ReviewTableOutput, ReviewTableOutputError> {
        self.verify_source(fresh, fresh_template)?;
        let source = self.review.forms.source();
        let (xml, body, paragraph) = select_paragraph(self.review, &self.marker, &self.paragraph)?;
        let part = source
            .resolve_anchor(&self.paragraph)
            .map_err(|_| ReviewTableOutputError::Readback)?;
        let header = header(self.review.forms)?;
        let (template_xml, ordinal, binding) = template_binding(self.template_forms, &self.table)?;
        require_native_identity_available(
            source,
            template_xml,
            self.template_forms
                .source()
                .resolve_anchor(&self.table)
                .map_err(|_| ReviewTableOutputError::Readback)?
                .element_index()
                .ok_or(ReviewTableOutputError::Readback)?,
        )?;
        let native = xml
            .with_source_bytes(|section| {
                template_xml.with_source_bytes(|template_section| {
                    render_review_table(&ReviewTableRenderInput {
                        context: ReviewCreateContextInput {
                            header: &header,
                            section,
                            body,
                            paragraph,
                            template_section,
                            template_table_ordinal: ordinal,
                            template_binding: &binding,
                            limits: self.limits,
                        },
                        expected: &self.native,
                        row_heights: &dimensions.row_heights_hwpunit,
                        column_widths: &dimensions.column_widths_hwpunit,
                    })
                })
            })
            .map_err(ReviewTableOutputError::Native)?;
        let mut intents = vec![replace_root(part.part().path(), xml, &native.section)?];
        let header_part = source
            .parts()
            .iter()
            .find(|p| p.path().as_str() == "Contents/header.xml")
            .ok_or(ReviewTableOutputError::Readback)?;
        if header != native.header {
            intents.push(replace_root(
                header_part.path(),
                header_part.xml().ok_or(ReviewTableOutputError::Readback)?,
                &native.header,
            )?);
        }
        let changed_parts = intents.len();
        let zip_limits = source
            .limits
            .zip()
            .map_err(|_| ReviewTableOutputError::Readback)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), zip_limits)
            .map_err(|_| ReviewTableOutputError::Patch)?;
        let transaction = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader,
            &source.graph,
            PackageGraphLimits::default(),
            IdRuleProfile::current_hancom_2020_formula_v3(),
            IdIndexLimits::default(),
            PatchLimits::default(),
            PreservationRuleProfile::Hangul2020PreviewTextV2,
            &intents,
        )
        .map_err(|e| ReviewTableOutputError::PatchRejected { code: e.code() })?;
        let artifact = PreservingWriter::build(
            &transaction,
            zip_limits,
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            writer_limits,
        )
        .map_err(|_| ReviewTableOutputError::Writer)?;
        artifact
            .with_verified_bytes(|bytes| {
                verify_package(self, fresh, bytes, part.part().path(), &native)
            })
            .map_err(|_| ReviewTableOutputError::Writer)??;
        self.verify_source(fresh, fresh_template)?;
        let receipt = output_receipt(self, &native, &artifact, changed_parts)?;
        Ok(ReviewTableOutput { artifact, receipt })
    }
}

fn replace_root(
    path: &PackagePath,
    original: &PreservingXmlDocument,
    output: &[u8],
) -> Result<PatchIntent, ReviewTableOutputError> {
    let xml = PreservingXmlDocument::parse(output).map_err(|_| ReviewTableOutputError::Patch)?;
    let span = xml.elements()[xml.root_element()]
        .outer_span()
        .ok_or(ReviewTableOutputError::Patch)?;
    Ok(PatchIntent::ReplaceSubtree {
        target: XmlElementSelector::bind(path, original, original.root_element())
            .map_err(|_| ReviewTableOutputError::Patch)?,
        fragment: ValidatedXmlFragment::parse(
            &output[span.start()..span.end()],
            PatchLimits::default(),
        )
        .map_err(|_| ReviewTableOutputError::Patch)?,
    })
}
fn require_native_identity_available(
    source: &ImportedSourcePackage,
    template: &PreservingXmlDocument,
    index: usize,
) -> Result<(), ReviewTableOutputError> {
    let native_id = template.elements()[index]
        .attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == "id")
        .ok_or(ReviewTableOutputError::Readback)?
        .semantic_value();
    for part in source.parts() {
        let Some(xml) = part.xml() else { continue };
        if xml.elements().iter().filter(|e| named(e, "tbl")).any(|e| {
            e.attributes().iter().any(|a| {
                a.name().namespace().is_none()
                    && a.name().local_name() == "id"
                    && a.semantic_value() == native_id
            })
        }) {
            return Err(ReviewTableOutputError::NativeIdentityCollision);
        }
    }
    Ok(())
}
fn expanded(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, ReviewTableOutputError> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), crate::PackageLimits::default())
        .map_err(|_| ReviewTableOutputError::Readback)?;
    let entries = reader.entries().to_vec();
    entries
        .into_iter()
        .map(|e| {
            Ok((
                e.path.as_str().to_owned(),
                reader
                    .read_entry(e.index)
                    .map_err(|_| ReviewTableOutputError::Readback)?,
            ))
        })
        .collect()
}
fn verify_package(
    context: &ReviewTableCreationContext<'_, '_>,
    fresh: &[u8],
    bytes: &[u8],
    path: &PackagePath,
    native: &ReviewNativeTableOutput,
) -> Result<(), ReviewTableOutputError> {
    let mut expected = expanded(fresh)?;
    expected
        .get_mut(path.as_str())
        .ok_or(ReviewTableOutputError::Readback)?
        .clone_from(&native.section);
    expected
        .get_mut("Contents/header.xml")
        .ok_or(ReviewTableOutputError::Readback)?
        .clone_from(&native.header);
    if expanded(bytes)? != expected {
        return Err(ReviewTableOutputError::Preservation);
    }
    let source = context.review.forms.source();
    let forms = ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            source.document_id.clone(),
            Sha256::digest(bytes).into(),
            source.limits,
        )
        .map_err(|_| ReviewTableOutputError::Readback)?,
    )
    .map_err(|_| ReviewTableOutputError::Readback)?;
    let after = ImportedDocumentReviewBodies::import(&forms)
        .map_err(|_| ReviewTableOutputError::Readback)?;
    let ordinal = context
        .review
        .observations
        .iter()
        .position(|o| o.marker_anchor == context.marker)
        .ok_or(ReviewTableOutputError::Readback)?;
    let old = &context.review.observations[ordinal];
    let new = after
        .observations
        .get(ordinal)
        .ok_or(ReviewTableOutputError::Readback)?;
    if after.observations.len() != context.review.observations.len()
        || new.kind != old.kind
        || new.native_attributes != old.native_attributes
        || new.body_attributes != old.body_attributes
    {
        return Err(ReviewTableOutputError::Readback);
    }
    let actual_header = header(&forms)?;
    let xml = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path() == path)
        .and_then(|p| p.xml())
        .ok_or(ReviewTableOutputError::Readback)?;
    let readback = xml
        .with_source_bytes(|section| {
            crate::TableRulingHwpxReader::read_existing(
                &actual_header,
                section,
                native.table_ordinal,
                &native.binding,
                context.limits.ruling,
            )
        })
        .map_err(|_| ReviewTableOutputError::Readback)?;
    if readback != native.reopened {
        return Err(ReviewTableOutputError::Readback);
    }
    // Selection cannot silently move to the main body/another review after replacement.
    let selected_body = forms
        .source()
        .resolve_anchor(
            new.body_anchor
                .as_ref()
                .ok_or(ReviewTableOutputError::Readback)?,
        )
        .map_err(|_| ReviewTableOutputError::Readback)?;
    let body_index = selected_body
        .element_index()
        .ok_or(ReviewTableOutputError::Readback)?;
    let table_index = xml
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, e)| named(e, "tbl"))
        .nth(native.table_ordinal)
        .map(|(i, _)| i)
        .ok_or(ReviewTableOutputError::Readback)?;
    if selected_body.part().path() != path
        || super::descendant_path(xml, body_index, table_index).is_err()
    {
        return Err(ReviewTableOutputError::Readback);
    }
    Ok(())
}

#[derive(Debug, Error)]
pub enum ReviewTableOutputError {
    #[error(transparent)]
    Context(#[from] ReviewTableContextError),
    #[error(transparent)]
    Native(crate::TableCreateHwpxError),
    #[error("review table output geometry is invalid or over limit")]
    Values,
    #[error("review table output native table identity collides in the source package")]
    NativeIdentityCollision,
    #[error("review table output original patch rejected")]
    Patch,
    /// Closed original error code only; never private XML, identities or document contents.
    #[error("review table output original patch rejected: {code}")]
    PatchRejected { code: &'static str },
    #[error("review table output original writer rejected")]
    Writer,
    #[error("review table output full original reimport or table readback rejected")]
    Readback,
    #[error("review table output outside preservation rejected")]
    Preservation,
}

fn output_receipt(
    context: &ReviewTableCreationContext<'_, '_>,
    native: &ReviewNativeTableOutput,
    artifact: &PackageArtifact,
    changed_parts: usize,
) -> Result<ReviewTableOutputReceipt, ReviewTableOutputError> {
    let receipt = ReviewTableOutputReceipt {
        qualification: "actual_source_review_blank_table_HWPX_output_original_native_geometry_style_and_package_reimport_NOT_full_comment_compiler_native_save_reopen_render_execution_or_Gate",
        source_package_sha256: context.receipt.source_package_sha256,
        template_package_sha256: context.receipt.template_package_sha256,
        output_package_sha256: artifact.sha256(),
        output_bytes: artifact.size_bytes(),
        target_grid_sha256: native
            .grid
            .canonical_sha256()
            .map_err(|_| ReviewTableOutputError::Readback)?,
        target_state_sha256: native
            .state
            .canonical_sha256(context.limits.ruling.ruling)
            .map_err(|_| ReviewTableOutputError::Readback)?,
        target_rows: native.grid.rows(),
        target_columns: native.grid.columns(),
        created_cells: native.grid.master_cell_count(),
        before_table_count_in_selected_part: context.native.source_table_count,
        after_table_count_in_selected_part: native.target_table_count,
        added_border_fills: native.added_border_fills,
        changed_parts,
        preservation:
            ReviewTablePreservation::OtherPartsAndOutsideParagraphExactHeaderNativeCoordinated,
        authority: ReviewTableOutputAuthority::SourceArtifactIntegrityOnly,
        new_table_inserted: true,
        full_document_flow_bound: false,
        full_comment_product_acceptance: false,
    };
    Ok(receipt)
}
