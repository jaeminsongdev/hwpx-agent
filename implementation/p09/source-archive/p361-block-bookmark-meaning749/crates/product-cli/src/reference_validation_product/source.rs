//! Actual package entry for reference validation. Unresolved source semantics
//! remain explicit; a source assessment is never a successful validation report.
use std::{
    ffi::OsString,
    fs::File,
    io::{self, Read as _},
    path::{Component, Path, PathBuf, Prefix},
};

use domain_ir::{
    DocumentId, LogicalId, NoteKind, ReferenceAuxiliaryLimits, ReferenceValidationReport, ValidationTarget,
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportError, SourceImportLimits, SourceImportReceipt,
    fields::{FieldRangeImportError, FieldRangeImportReceipt, ImportedDocumentFields},
    fields::semantics::catalog::security::{ActiveSecurityImportError, SourceActiveSecurityAssessment},
    forms::{FormImportError, FormImportReceipt, ImportedDocumentForms},
    reference_targets::{
        ImportedReferenceObjectTargets, ImportedReferenceTargets, ReferenceObjectTargetImportReceipt,
        ReferenceTargetImportError, ReferenceTargetImportReceipt,
    },
    reference_targets::captions::{ImportedReferenceCaptionEnvelope, ReferenceCaptionImportReceipt},
    reference_targets::caption_source_state::{ImportedCaptionSourceState,CaptionSourceStateReceipt,
        CaptionStateOwnerLink,CaptionNumberingSourceEvent},
    reference_targets::numbering::{CaptionNumberingImportReceipt,
        CaptionNumberingImportError, NativeNumberControlObservation, NativeSectionStartObservation},
    reference_targets::numbering::context::{NumberingContextImportReceipt, NativeDocumentNumberingStart,
        NativeNumberingOwnerObservation, OrderedNumberingControl},
    reference_targets::caption_object_state::{CaptionObjectStateReceipt, CaptionObjectStateProjection},
    reference_targets::caption_frames::{CaptionFrameImportReceipt, CaptionSourceFrame},
    reference_targets::headings::{ImportedReferenceHeadingTargets,ReferenceHeadingTargetReceipt},
    reference_targets::headings::declarations702::SourceHeadingDeclarationInventory,
    structure::{ImportedDocumentStructure, ImportedSectionFlowObservation, StructureImportReceipt},
};
use serde::Serialize;
use thiserror::Error;

use super::ReferenceValidationProductOperation;
use super::source_field_semantics::ReferenceSourceFieldMeaningAssessment;
use hwpx_package::document_import::fields::semantics::{FieldSemanticImportError,
    source_index::SourceFieldMeaningIndex};
use hwpx_package::document_import::fields::cached_source::{SourceFieldCachedInlines,FieldCachedSourceError};

pub const REFERENCE_SOURCE_RESULT_SCHEMA: &str =
    "hwpx-agent.product.reference-source-assessment/v15";
pub const REFERENCE_SOURCE_CONDITIONAL_HEADING_SCHEMA: &str =
    "hwpx-agent.product.reference-source-assessment/v16";
pub const REFERENCE_SOURCE_MAX_ARCHIVE_BYTES: u64 = 32 * 1024 * 1024;
pub const REFERENCE_SOURCE_INCOMPLETE_EXIT: u8 = 3;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReferenceSourceStatus {
    Incomplete,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnresolvedReferenceStage {
    OtherTargetFamilies,
    ReferenceEdgeSemantics,
    CompleteAuxiliaryState,
    DocumentFlow,
    ConditionalHeadingDeclarations,
}

/// Minimal source-backed selectors for typed note-kind requests. Never exposes
/// raw note text, attributes, marker characters, body XML or native instance IDs.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReferenceSourceNoteSelection {
    note_id: LogicalId,
    source_note_sha256: [u8; 32],
    kind: NoteKind,
}
impl ReferenceSourceNoteSelection {
    #[must_use]
    pub const fn note_id(&self) -> &LogicalId { &self.note_id }
    #[must_use]
    pub const fn source_note_sha256(&self) -> [u8; 32] { self.source_note_sha256 }
    #[must_use]
    pub const fn kind(&self) -> NoteKind { self.kind }

    fn from_source(forms: &ImportedDocumentForms, limits: ReferenceAuxiliaryLimits)
        -> Result<Vec<Self>, ReferenceSourceError>
    {
        let source = forms.notes();
        if source.len() > limits.config().items_per_kind { return Err(ReferenceSourceError::InputLimit); }
        let mut selections = Vec::new();
        selections.try_reserve_exact(source.len()).map_err(|_| ReferenceSourceError::InputLimit)?;
        for note in source {
            let kind = match note.native_kind.as_str() {
                "footNote" => NoteKind::Footnote,
                "endNote" => NoteKind::Endnote,
                _ => return Err(ReferenceSourceError::Binding),
            };
            selections.push(Self { note_id: note.note_id.clone(),
                source_note_sha256: note.source_anchor.fingerprint_sha256, kind });
        }
        Ok(selections)
    }
}

/// Body-spine style selectors only, not effective style values or protection.
/// No note text, raw XML, prefix/suffix/user characters or native numeric IDs.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReferenceSourceNoteStyleSelection {
    style_id: LogicalId,
    source_style_sha256: [u8; 32],
    kind: NoteKind,
}
impl ReferenceSourceNoteStyleSelection {
    #[must_use]
    pub const fn style_id(&self) -> &LogicalId { &self.style_id }
    #[must_use]
    pub const fn source_style_sha256(&self) -> [u8; 32] { self.source_style_sha256 }
    #[must_use]
    pub const fn kind(&self) -> NoteKind { self.kind }

    fn from_source(structure: &ImportedDocumentStructure, limits: ReferenceAuxiliaryLimits)
        -> Result<Vec<Self>, ReferenceSourceError>
    {
        use hwpx_package::{NoteHwpxLimitConfig, NoteHwpxLimits,
            document_import::structure::note_style::NoteStyleError};
        let defaults = NoteHwpxLimitConfig::default();
        let style_limits = NoteHwpxLimits::new(NoteHwpxLimitConfig {
            notes: defaults.notes.min(limits.config().items_per_kind),
            text_bytes: defaults.text_bytes.min(limits.config().text_bytes),
            ..defaults
        }).map_err(|_| ReferenceSourceError::InputLimit)?;
        // Existing token documents only; no ZIP/XML/Form reconstruction here.
        // Malformed observed styles must not become an apparently absent array.
        let source = structure.import_note_styles(style_limits).map_err(|error| match error {
            NoteStyleError::Limit => ReferenceSourceError::InputLimit,
            _ => ReferenceSourceError::NoteStyles,
        })?;
        let mut selections = Vec::new();
        selections.try_reserve_exact(source.len()).map_err(|_| ReferenceSourceError::InputLimit)?;
        for style in source {
            selections.push(Self { style_id: style.style_id().clone(),
                source_style_sha256: style.source_anchor().fingerprint_sha256, kind: style.kind() });
        }
        Ok(selections)
    }
}

/// No raw bookmark names, field parameters, paths, text or external URIs.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReferenceSourceAssessment {
    schema_version: &'static str,
    status: ReferenceSourceStatus,
    source: SourceImportReceipt,
    structure: StructureImportReceipt,
    target_import: ReferenceTargetImportReceipt,
    object_target_import: ReferenceObjectTargetImportReceipt,
    // None is an unobserved header declaration model, not a confirmed empty heading inventory.
    heading_target_import: Option<ReferenceHeadingTargetReceipt>,
    // Original alternatives, never a selected branch or an empty-target proof.
    // Omitted for legacy v15 to preserve its exact serialized shape.
    #[serde(skip_serializing_if="Option::is_none")]
    conditional_heading_declarations: Option<SourceHeadingDeclarationInventory>,
    caption_import: ReferenceCaptionImportReceipt,
    caption_envelopes: Vec<ImportedReferenceCaptionEnvelope>,
    numbering_import: CaptionNumberingImportReceipt,
    numbering_controls: Vec<NativeNumberControlObservation>,
    numbering_section_starts: Vec<NativeSectionStartObservation>,
    numbering_context_import: NumberingContextImportReceipt,
    document_numbering_start: Option<NativeDocumentNumberingStart>,
    numbering_owners: Vec<NativeNumberingOwnerObservation>,
    numbering_control_order: Vec<OrderedNumberingControl>,
    caption_object_state_import: CaptionObjectStateReceipt,
    caption_object_states: Vec<CaptionObjectStateProjection>,
    caption_frame_import: CaptionFrameImportReceipt,
    caption_frames: Vec<CaptionSourceFrame>,
    caption_source_state_import: CaptionSourceStateReceipt,
    caption_owner_links: Vec<CaptionStateOwnerLink>,
    caption_source_events: Vec<CaptionNumberingSourceEvent>,
    form_import: FormImportReceipt,
    field_range_import: FieldRangeImportReceipt,
    field_meanings: ReferenceSourceFieldMeaningAssessment,
    field_cached_source: SourceFieldCachedInlines,
    section_flows: Vec<ImportedSectionFlowObservation>,
    note_selections: Vec<ReferenceSourceNoteSelection>,
    note_style_selections: Vec<ReferenceSourceNoteStyleSelection>,
    active_security: SourceActiveSecurityAssessment,
    targets: Vec<ValidationTarget>,
    unresolved: Vec<UnresolvedReferenceStage>,
    // None means NOT RUN, not a fabricated zero-reference success.
    validation_report: Option<ReferenceValidationReport>,
}

impl ReferenceSourceAssessment {
    #[must_use]
    pub const fn field_meanings(&self) -> &ReferenceSourceFieldMeaningAssessment { &self.field_meanings }
    #[must_use]
    pub const fn field_cached_source(&self) -> &SourceFieldCachedInlines { &self.field_cached_source }
    #[must_use]
    pub const fn status(&self) -> ReferenceSourceStatus {
        self.status
    }
    #[must_use]
    pub fn targets(&self) -> &[ValidationTarget] {
        &self.targets
    }
    #[must_use]
    pub const fn target_receipt(&self) -> &ReferenceTargetImportReceipt {
        &self.target_import
    }
    #[must_use]
    pub const fn object_target_receipt(&self) -> &ReferenceObjectTargetImportReceipt {
        &self.object_target_import
    }
    #[must_use]
    pub const fn heading_target_receipt(&self) -> Option<&ReferenceHeadingTargetReceipt> { self.heading_target_import.as_ref() }
    #[must_use]
    pub const fn conditional_heading_declarations(&self) -> Option<&SourceHeadingDeclarationInventory> { self.conditional_heading_declarations.as_ref() }
    #[must_use]
    pub const fn caption_receipt(&self) -> &ReferenceCaptionImportReceipt { &self.caption_import }
    #[must_use]
    pub fn caption_envelopes(&self) -> &[ImportedReferenceCaptionEnvelope] { &self.caption_envelopes }
    #[must_use]
    pub const fn numbering_receipt(&self) -> &CaptionNumberingImportReceipt { &self.numbering_import }
    #[must_use]
    pub fn numbering_controls(&self) -> &[NativeNumberControlObservation] { &self.numbering_controls }
    #[must_use]
    pub fn numbering_section_starts(&self) -> &[NativeSectionStartObservation] { &self.numbering_section_starts }
    #[must_use]
    pub const fn numbering_context_receipt(&self) -> &NumberingContextImportReceipt { &self.numbering_context_import }
    #[must_use]
    pub const fn document_numbering_start(&self) -> Option<&NativeDocumentNumberingStart> { self.document_numbering_start.as_ref() }
    #[must_use]
    pub fn numbering_owners(&self) -> &[NativeNumberingOwnerObservation] { &self.numbering_owners }
    #[must_use]
    pub fn numbering_control_order(&self) -> &[OrderedNumberingControl] { &self.numbering_control_order }
    #[must_use]
    pub const fn caption_object_state_receipt(&self) -> &CaptionObjectStateReceipt { &self.caption_object_state_import }
    #[must_use]
    pub fn caption_object_states(&self) -> &[CaptionObjectStateProjection] { &self.caption_object_states }
    #[must_use]
    pub const fn caption_frame_receipt(&self) -> &CaptionFrameImportReceipt { &self.caption_frame_import }
    #[must_use]
    pub fn caption_frames(&self) -> &[CaptionSourceFrame] { &self.caption_frames }
    /// Exact original join for typed request construction, never access authority
    /// or a claim of complete auxiliary state or Native counter interpretation.
    #[must_use]
    pub const fn caption_source_state_receipt(&self) -> &CaptionSourceStateReceipt { &self.caption_source_state_import }
    #[must_use]
    pub fn caption_owner_links(&self) -> &[CaptionStateOwnerLink] { &self.caption_owner_links }
    /// XML source order only, not Native/rendered document order.
    #[must_use]
    pub fn caption_source_events(&self) -> &[CaptionNumberingSourceEvent] { &self.caption_source_events }
    #[must_use]
    pub const fn form_receipt(&self) -> &FormImportReceipt {
        &self.form_import
    }
    #[must_use]
    pub const fn field_range_receipt(&self) -> &FieldRangeImportReceipt {
        &self.field_range_import
    }
    #[must_use]
    pub fn section_flows(&self) -> &[ImportedSectionFlowObservation] {
        &self.section_flows
    }
    /// Exact source-local request selectors, not Native/global identity, resolved
    /// numbering, access authority or a completed reference validation.
    #[must_use]
    pub fn note_selections(&self) -> &[ReferenceSourceNoteSelection] {
        &self.note_selections
    }
    /// Actual body-spine style declarations in XML order, not effective style,
    /// global/native identity, numbering/layout or complete protection authority.
    #[must_use]
    pub fn note_style_selections(&self) -> &[ReferenceSourceNoteStyleSelection] {
        &self.note_style_selections
    }
    #[must_use]
    pub const fn active_security(&self) -> &SourceActiveSecurityAssessment {
        &self.active_security
    }
    #[must_use]
    pub const fn validation_report(&self) -> Option<&ReferenceValidationReport> {
        self.validation_report.as_ref()
    }

    /// # Errors
    /// Rejects an oversized response rather than truncating source evidence.
    pub fn canonical_json(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Vec<u8>, ReferenceSourceError> {
        let mut writer = BoundedOutput {
            bytes: Vec::new(),
            maximum: limits.config().output_bytes,
        };
        serde_json::to_writer(&mut writer, self).map_err(|_| ReferenceSourceError::Output)?;
        Ok(writer.bytes)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum ReferenceSourceError {
    #[error("REFERENCE_SOURCE_REQUEST_REJECTED")]
    Request,
    #[error("REFERENCE_SOURCE_FILE_REJECTED")]
    File,
    #[error("REFERENCE_SOURCE_INPUT_LIMIT")]
    InputLimit,
    #[error("REFERENCE_SOURCE_BINDING_REJECTED")]
    Binding,
    #[error("REFERENCE_SOURCE_PACKAGE_REJECTED")]
    Package,
    #[error("REFERENCE_SOURCE_STRUCTURE_REJECTED")]
    Structure,
    #[error("REFERENCE_SOURCE_FORMS_REJECTED")]
    Forms,
    #[error("REFERENCE_SOURCE_FIELD_RANGES_REJECTED")]
    FieldRanges,
    #[error("REFERENCE_SOURCE_ACTIVE_SECURITY_REJECTED")]
    ActiveSecurity,
    #[error("REFERENCE_SOURCE_CAPTION_REJECTED")]
    Caption,
    #[error("REFERENCE_SOURCE_NUMBERING_REJECTED")]
    Numbering,
    #[error("REFERENCE_SOURCE_NOTE_STYLES_REJECTED")]
    NoteStyles,
    #[error("REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED")]
    Coverage,
    #[error("REFERENCE_SOURCE_OUTPUT_LIMIT")]
    Output,
}

impl ReferenceValidationProductOperation {
    /// Starts from actual admitted package bytes, never caller-supplied typed state.
    ///
    /// # Errors
    /// Rejects archive drift, unsupported packages, structure/coverage failures and
    /// finite limits. No native access, repair, update, authorization or writes occur.
    pub fn assess_package_source(
        bytes: &[u8],
        document_id: DocumentId,
        expected_package_sha256: [u8; 32],
        source_limits: SourceImportLimits,
        reference_limits: ReferenceAuxiliaryLimits,
    ) -> Result<ReferenceSourceAssessment, ReferenceSourceError> {
        let package = ImportedSourcePackage::import(
            bytes,
            document_id,
            expected_package_sha256,
            source_limits,
        )
        .map_err(|e| match e {
            SourceImportError::SourceChanged => ReferenceSourceError::Binding,
            SourceImportError::Limit => ReferenceSourceError::InputLimit,
            _ => ReferenceSourceError::Package,
        })?;
        let source_receipt = package.receipt().clone();
        let forms = ImportedDocumentForms::import(package).map_err(|error| match error {
            FormImportError::Body(_) => ReferenceSourceError::Structure,
            _ => ReferenceSourceError::Forms,
        })?;
        // Borrow the original body; no second ZIP/XML/structure import for targets.
        let structure = forms.body_structure();
        let note_selections = ReferenceSourceNoteSelection::from_source(&forms, reference_limits)?;
        if structure.section_flows().len() > reference_limits.config().sections {
            return Err(ReferenceSourceError::InputLimit);
        }
        let note_style_selections = ReferenceSourceNoteStyleSelection::from_source(structure, reference_limits)?;
        let imported = ImportedReferenceTargets::import(structure, reference_limits).map_err(
            |e| match e {
                ReferenceTargetImportError::Limit => ReferenceSourceError::InputLimit,
                ReferenceTargetImportError::Coverage => ReferenceSourceError::Coverage,
                _ => ReferenceSourceError::Binding,
            },
        )?;
        if imported.receipt().observed_native_fields > reference_limits.config().items_per_kind {
            return Err(ReferenceSourceError::InputLimit);
        }
        let fields = ImportedDocumentFields::import(&forms).map_err(|error| match error {
            FieldRangeImportError::Limit => ReferenceSourceError::InputLimit,
            _ => ReferenceSourceError::FieldRanges,
        })?;
        check_whole_source_field_coverage(structure, &fields, reference_limits)?;
        // Reuse this original-bound inventory and limits; no second package,
        // form, field or target import and no additional DocumentGraph clone.
        let meanings=SourceFieldMeaningIndex::import_using_targets(&fields,reference_limits,&imported)
            .map_err(|error|match error{FieldSemanticImportError::Limit=>ReferenceSourceError::InputLimit,
                _=>ReferenceSourceError::FieldRanges})?;
        let field_meanings=ReferenceSourceFieldMeaningAssessment::from_index(&fields,&meanings,reference_limits)?;
        let field_cached_source=SourceFieldCachedInlines::import(&fields,reference_limits).map_err(|error|match error{
            FieldCachedSourceError::Limit=>ReferenceSourceError::InputLimit,FieldCachedSourceError::Binding=>ReferenceSourceError::FieldRanges})?;
        let objects = ImportedReferenceObjectTargets::import(structure, reference_limits).map_err(|error| match error {
            ReferenceTargetImportError::Limit => ReferenceSourceError::InputLimit,
            ReferenceTargetImportError::Coverage => ReferenceSourceError::Coverage,
            _ => ReferenceSourceError::Binding,
        })?;
        let mut targets = imported.targets().to_vec();
        targets.try_reserve(objects.targets().len()).map_err(|_| ReferenceSourceError::InputLimit)?;
        targets.extend_from_slice(objects.targets());
        let heading_error=|error|match error{
            ReferenceTargetImportError::Limit=>ReferenceSourceError::InputLimit,
            ReferenceTargetImportError::Coverage=>ReferenceSourceError::Coverage,
            _=>ReferenceSourceError::Binding,
        };
        let conditional_heading_declarations=SourceHeadingDeclarationInventory::observe_conditional(structure,reference_limits).map_err(heading_error)?;
        let headings=if conditional_heading_declarations.is_some(){None}else{
            ImportedReferenceHeadingTargets::for_partial_source_assessment(structure,reference_limits).map_err(heading_error)?
        };
        if let Some(heading)=&headings{
            targets.try_reserve(heading.targets().len()).map_err(|_|ReferenceSourceError::InputLimit)?;
            targets.extend_from_slice(heading.targets());
        }
        let source_numbering_error = |error| match error {
            CaptionNumberingImportError::Limit => ReferenceSourceError::InputLimit,
            CaptionNumberingImportError::Coverage => ReferenceSourceError::Coverage,
            CaptionNumberingImportError::Binding => ReferenceSourceError::Binding,
            CaptionNumberingImportError::CaptionEnvelope => ReferenceSourceError::Caption,
            CaptionNumberingImportError::Value => ReferenceSourceError::Numbering,
        };
        let caption_state = ImportedCaptionSourceState::import(structure, reference_limits).map_err(source_numbering_error)?;
        // One exact original-bound assembly shared by the existing constituent
        // models and request bindings. XML order is not resolved native sequence.
        let numbering = caption_state.numbering();
        let numbering_context = caption_state.context();
        let caption_object_states = caption_state.object_states();
        let caption_frames = caption_state.frames();
        let captions = numbering.caption_import();
        targets.try_reserve(captions.targets().len()).map_err(|_| ReferenceSourceError::InputLimit)?;
        targets.extend_from_slice(captions.targets());
        let original_limits = hwpx_package::ActiveContentLimits::default().config();
        let active_limits = hwpx_package::ActiveContentLimits::new(hwpx_package::ActiveContentLimitConfig {
            max_inventory_items: original_limits.max_inventory_items.min(reference_limits.config().items_per_kind),
            max_json_bytes: original_limits.max_json_bytes.min(reference_limits.config().output_bytes),
            ..original_limits
        }).map_err(|_| ReferenceSourceError::InputLimit)?;
        let active_security = forms.source().assess_active_content(active_limits).map_err(|error| match error {
            ActiveSecurityImportError::Inventory(hwpx_package::ActiveContentError::InventoryLimit
                | hwpx_package::ActiveContentError::OutputLimit) => ReferenceSourceError::InputLimit,
            _ => ReferenceSourceError::ActiveSecurity,
        })?;
        let mut unresolved=vec![UnresolvedReferenceStage::OtherTargetFamilies,
            UnresolvedReferenceStage::ReferenceEdgeSemantics,UnresolvedReferenceStage::CompleteAuxiliaryState,
            UnresolvedReferenceStage::DocumentFlow];
        if conditional_heading_declarations.is_some(){unresolved.push(UnresolvedReferenceStage::ConditionalHeadingDeclarations);}
        Ok(ReferenceSourceAssessment {
            schema_version: if conditional_heading_declarations.is_some(){REFERENCE_SOURCE_CONDITIONAL_HEADING_SCHEMA}else{REFERENCE_SOURCE_RESULT_SCHEMA},
            status: ReferenceSourceStatus::Incomplete,
            source: source_receipt,
            structure: structure.receipt().clone(),
            target_import: imported.receipt().clone(),
            object_target_import: objects.receipt().clone(),
            heading_target_import: headings.as_ref().map(|h|h.receipt().clone()),
            conditional_heading_declarations,
            caption_import: captions.receipt().clone(),
            caption_envelopes: captions.envelopes().to_vec(),
            numbering_import: numbering.receipt().clone(),
            numbering_controls: numbering.controls().to_vec(),
            numbering_section_starts: numbering.section_starts().to_vec(),
            numbering_context_import: numbering_context.receipt().clone(),
            document_numbering_start: numbering_context.document_start().cloned(),
            numbering_owners: numbering_context.owners().to_vec(),
            numbering_control_order: numbering_context.ordered_controls().to_vec(),
            caption_object_state_import: caption_object_states.receipt().clone(),
            caption_object_states: caption_object_states.objects().to_vec(),
            caption_frame_import: caption_frames.receipt().clone(),
            caption_frames: caption_frames.frames().to_vec(),
            caption_source_state_import: caption_state.receipt().clone(),
            caption_owner_links: caption_state.owner_links().to_vec(),
            caption_source_events: caption_state.source_events().to_vec(),
            form_import: forms.receipt().clone(),
            field_range_import: fields.receipt().clone(),
            field_meanings,
            field_cached_source,
            section_flows: structure.section_flows().to_vec(),
            note_selections,
            note_style_selections,
            active_security,
            targets,
            unresolved,
            validation_report: None,
        })
        // Do not label an assessment as a completed reference operation merely
        // because no field was observed. The complete state/flow is still absent.
    }
}

// The original range importer covers represented section bodies. The reference
// assessment must also reject an extra begin OR end in header/nonspine/opaque
// XML, rather than attaching a partial field inventory to a whole-source result.
pub(super) fn check_whole_source_field_coverage(
    structure: &ImportedDocumentStructure,
    fields: &ImportedDocumentFields<'_>,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceSourceError> {
    let mut counts = [0usize; 2];
    for part in structure.source().parts() {
        let Some(xml) = part.xml() else { continue };
        for element in xml.elements() {
            if element.name().namespace() != Some(hwpx_package::HANCOM_2020_PARAGRAPH_NAMESPACE) {
                continue;
            }
            let index = match element.name().local_name() {
                "fieldBegin" => 0,
                "fieldEnd" => 1,
                _ => continue,
            };
            counts[index] = counts[index]
                .checked_add(1)
                .filter(|count| *count <= limits.config().items_per_kind)
                .ok_or(ReferenceSourceError::InputLimit)?;
        }
    }
    if counts != [fields.receipt().field_ranges; 2] {
        return Err(ReferenceSourceError::Coverage);
    }
    Ok(())
}

struct BoundedOutput {
    bytes: Vec<u8>,
    maximum: usize,
}
impl io::Write for BoundedOutput {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.bytes
            .len()
            .checked_add(bytes.len())
            .filter(|size| *size <= self.maximum)
            .ok_or_else(|| io::Error::other("REFERENCE_SOURCE_OUTPUT_LIMIT"))?;
        self.bytes
            .try_reserve(bytes.len())
            .map_err(|_| io::Error::other("REFERENCE_SOURCE_OUTPUT_LIMIT"))?;
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

/// Closed read-only CLI: reference-source DOCUMENT_ID SHA256 ABSOLUTE_LOCAL_FILE.
///
/// # Errors
/// Rejects ambiguous arguments, non-local/device paths, symlinks, non-files,
/// excessive archive bytes, source drift, or original package/coverage failures.
pub fn assess_cli_arguments(
    args: impl IntoIterator<Item = OsString>,
) -> Result<ReferenceSourceAssessment, ReferenceSourceError> {
    let mut args = args.into_iter();
    let document = args.next().ok_or(ReferenceSourceError::Request)?;
    let digest = args.next().ok_or(ReferenceSourceError::Request)?;
    let path = args.next().ok_or(ReferenceSourceError::Request)?;
    if args.next().is_some() {
        return Err(ReferenceSourceError::Request);
    }
    let document = DocumentId::parse(document.to_str().ok_or(ReferenceSourceError::Request)?)
        .map_err(|_| ReferenceSourceError::Request)?;
    let digest = digest
        .to_str()
        .filter(|s| s.len() == 64)
        .ok_or(ReferenceSourceError::Request)?;
    let expected: [u8; 32] = hex::decode(digest)
        .map_err(|_| ReferenceSourceError::Request)?
        .try_into()
        .map_err(|_| ReferenceSourceError::Request)?;
    let path = PathBuf::from(path);
    let bytes = read_local_archive(&path)?;
    let limits = ReferenceAuxiliaryLimits::new(Default::default())
        .map_err(|_| ReferenceSourceError::Request)?;
    ReferenceValidationProductOperation::assess_package_source(
        &bytes,
        document,
        expected,
        SourceImportLimits::default(),
        limits,
    )
}

fn read_local_archive(path: &Path) -> Result<Vec<u8>, ReferenceSourceError> {
    if !path.is_absolute()
        || path.components().any(|c| match c {
            Component::Prefix(p) => !matches!(p.kind(), Prefix::Disk(_) | Prefix::VerbatimDisk(_)),
            Component::ParentDir => true,
            _ => false,
        })
    {
        return Err(ReferenceSourceError::File);
    }
    let ancestors: Vec<_> = path.ancestors().collect();
    if ancestors.len() > 256 {
        return Err(ReferenceSourceError::File);
    }
    let mut length = None;
    // Check roots BEFORE descendants, so an already-present junction ancestor
    // is rejected before a leaf metadata request traverses it. This is not an
    // adversarial rename-race sandbox or service authorization boundary.
    for ancestor in ancestors.into_iter().rev() {
        let metadata = ancestor
            .symlink_metadata()
            .map_err(|_| ReferenceSourceError::File)?;
        if metadata.file_type().is_symlink() {
            return Err(ReferenceSourceError::File);
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err(ReferenceSourceError::File);
            }
        }
        if ancestor == path {
            if !metadata.is_file() {
                return Err(ReferenceSourceError::File);
            }
            length = Some(metadata.len());
        } else if !metadata.is_dir() {
            return Err(ReferenceSourceError::File);
        }
    }
    if length.ok_or(ReferenceSourceError::File)? > REFERENCE_SOURCE_MAX_ARCHIVE_BYTES {
        return Err(ReferenceSourceError::InputLimit);
    }
    let file = File::open(path).map_err(|_| ReferenceSourceError::File)?;
    if !file
        .metadata()
        .map_err(|_| ReferenceSourceError::File)?
        .is_file()
    {
        return Err(ReferenceSourceError::File);
    }
    let mut bytes = Vec::new();
    file.take(REFERENCE_SOURCE_MAX_ARCHIVE_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| ReferenceSourceError::File)?;
    if u64::try_from(bytes.len()).map_err(|_| ReferenceSourceError::InputLimit)?
        > REFERENCE_SOURCE_MAX_ARCHIVE_BYTES
    {
        return Err(ReferenceSourceError::InputLimit);
    }
    Ok(bytes)
}
