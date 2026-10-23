use std::fs;
use std::path::Path;

use domain_ir::{
    AppearanceOperation, AppearanceTargetKind, FillAppearance, LogicalId,
    OBJECT_SPECIAL_SCHEMA_VERSION, ObjectAnchor, ObjectCaption, ObjectCaptionNumbering,
    ObjectCaptionSide, ObjectGeometryOperation, ObjectHeightReference, ObjectHorizontalAlignment,
    ObjectHorizontalReference, ObjectIdentity, ObjectKind, ObjectOuterMargins, ObjectPosition,
    ObjectSize, ObjectSpecialBuilder, ObjectSpecialDocumentState, ObjectSpecialDocumentStateDraft,
    ObjectSpecialLimitConfig, ObjectSpecialLimits, ObjectSpecialOperation, ObjectSpecialRequest,
    ObjectSpecialRequestDraft, ObjectTextFlow, ObjectTextWrap, ObjectVerticalAlignment,
    ObjectVerticalReference, ObjectWidthReference, ObjectWrap, ParagraphBandPayload,
    ParagraphBandPlacement, SpecialObjectKind, SpecialObjectPayload, SpecialObjectState,
    StaticFormControlKind, StaticFormPayload,
};
use hwpx_package::{
    OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256, ObjectCaptionInsertHwpxBuilder,
    ObjectCaptionInsertHwpxLimits, ObjectCaptionInsertHwpxLowerer,
    ObjectCaptionInsertHwpxLoweringReceipt, ObjectFormInsertHwpxBuilder,
    ObjectFormInsertHwpxLimits, ObjectFormInsertHwpxLowerer, ObjectFormInsertHwpxLoweringReceipt,
};

use super::common::{
    AnyError, FLOW_AFTER, FLOW_BEFORE, LoweringEvidence, PreparedCase, hex, prepared_from_section,
    section_from_package, sha256,
};
use super::{appearance, geometry};

const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const DRAWING_GALLERY_TEMPLATE_PATH: &str = r"C:\Program Files (x86)\HNC\Office 2020\HOffice110\Shared\HwpTemplate\Draw\FG_Basic_Shapes\Rectangle.drt";
const DRAWING_GALLERY_TEMPLATE_BYTES: usize = 12_288;
const DRAWING_GALLERY_TEMPLATE_SHA256: &str =
    "97263ccadb83c470550354abf6bf8fdfd57e8ba4f3b294f479c7bab80f36753b";
const COMPOUND_FILE_MAGIC: &[u8; 8] = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1";
const PARAGRAPH_BAND_WIDTH: u32 = 39_600;
const PARAGRAPH_BAND_HEIGHT: u32 = 1_200;

pub fn cases(shape_package: &[u8]) -> Result<Vec<PreparedCase>, AnyError> {
    Ok(vec![
        caption_insert_case(shape_package)?,
        form_insert_case(shape_package)?,
        drawing_gallery_case(shape_package)?,
        paragraph_band_case(shape_package)?,
    ])
}

fn drawing_gallery_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let template = qualified_drawing_gallery_template()?;
    let source = section_from_package(shape_package)?;
    let output = replace_fixture_marker(
        &source,
        "OBJ-001 obj.shape_insert",
        "OBJ-003 obj.drawing_gallery",
    )?;
    let readback = geometry::read(&output)?;
    if readback.state.object_kind() != ObjectKind::Rectangle
        || readback.state.native_object_id() != 8_101
        || readback.state.native_instance_id() != 18_101
    {
        return Err("drawing-gallery compiled rectangle identity drifted".into());
    }
    let source_sha256 = sha256(&source);
    let output_sha256 = sha256(&output);
    let plan_sha256 = sha256(
        format!(
            "hwpx-agent.object-drawing-gallery.installed-drt.rectangle/v1\n{}\n{}\n{}\n{}\n",
            DRAWING_GALLERY_TEMPLATE_SHA256,
            template.len(),
            source_sha256,
            output_sha256,
        )
        .as_bytes(),
    );
    prepared_from_section(
        "P08-19-C40",
        "OBJ-003",
        "obj.drawing_gallery",
        "obj-003-drawing-gallery.hwpx",
        shape_package,
        &output,
        vec![LoweringEvidence {
            profile_id: "hwpx-agent.object-drawing-gallery.installed-drt.rectangle/v1".to_owned(),
            capability_id: "obj.drawing_gallery".to_owned(),
            plan_sha256,
            source_section_sha256: source_sha256,
            output_section_sha256: output_sha256,
            modified_unit_count: 1,
        }],
        "rectangle",
        8_101,
        18_101,
        false,
    )
}

fn paragraph_band_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let source = section_from_package(shape_package)?;
    let marked = replace_fixture_marker(
        &source,
        "OBJ-001 obj.shape_insert",
        "OBJ-014 obj.paragraph_band_object",
    )?;
    let (sized, mut evidence) = paragraph_band_geometry(&marked)?;
    let (output, appearance_evidence) = paragraph_band_appearance(&sized)?;
    evidence.insert(0, paragraph_band_semantic_evidence(&source, &output)?);
    evidence.push(appearance_evidence);
    prepared_from_section(
        "P08-19-C41",
        "OBJ-014",
        "obj.paragraph_band_object",
        "obj-014-paragraph-band.hwpx",
        shape_package,
        &output,
        evidence,
        "rectangle",
        8_101,
        18_101,
        false,
    )
}

fn paragraph_band_geometry(section: &[u8]) -> Result<(Vec<u8>, Vec<LoweringEvidence>), AnyError> {
    let (anchored, anchor_receipt) = geometry::lower(
        section,
        ObjectGeometryOperation::SetAnchor {
            anchor: ObjectAnchor {
                treat_as_character: false,
                affect_line_spacing: false,
                flow_with_text: true,
                allow_overlap: true,
                hold_anchor_and_shape: true,
                horizontal_reference: ObjectHorizontalReference::Paragraph,
                vertical_reference: ObjectVerticalReference::Paragraph,
            },
        },
    )?;
    let (positioned, position_receipt) = geometry::lower(
        &anchored,
        ObjectGeometryOperation::SetPosition {
            position: ObjectPosition {
                horizontal_alignment: ObjectHorizontalAlignment::Left,
                vertical_alignment: ObjectVerticalAlignment::Top,
                horizontal_offset_hwpunit: 0,
                vertical_offset_hwpunit: 0,
            },
        },
    )?;
    let (wrapped, wrap_receipt) = geometry::lower(
        &positioned,
        ObjectGeometryOperation::SetWrap {
            wrap: ObjectWrap {
                text_wrap: ObjectTextWrap::BehindText,
                text_flow: ObjectTextFlow::BothSides,
            },
            outer_margins: ObjectOuterMargins {
                left_hwpunit: 0,
                right_hwpunit: 0,
                top_hwpunit: 0,
                bottom_hwpunit: 0,
            },
        },
    )?;
    let mut component = geometry::read(&wrapped)?.state.component();
    component.original_size.width_hwpunit = PARAGRAPH_BAND_WIDTH;
    component.original_size.height_hwpunit = PARAGRAPH_BAND_HEIGHT;
    component.current_size = component.original_size;
    let (sized, size_receipt) = geometry::lower(
        &wrapped,
        ObjectGeometryOperation::SetSize {
            size: ObjectSize {
                width_hwpunit: PARAGRAPH_BAND_WIDTH,
                width_reference: ObjectWidthReference::Absolute,
                height_hwpunit: PARAGRAPH_BAND_HEIGHT,
                height_reference: ObjectHeightReference::Absolute,
                protect: true,
            },
            component,
        },
    )?;
    Ok((
        sized,
        vec![
            geometry::evidence(&anchor_receipt),
            geometry::evidence(&position_receipt),
            geometry::evidence(&wrap_receipt),
            geometry::evidence(&size_receipt),
        ],
    ))
}

fn paragraph_band_appearance(section: &[u8]) -> Result<(Vec<u8>, LoweringEvidence), AnyError> {
    let appearance_source = appearance::read_appearance(section, 0, 8_101, 18_101)?;
    if appearance_source.target_kind != AppearanceTargetKind::BasicShape {
        return Err("paragraph-band source is not a basic shape".into());
    }
    let mut target_appearance = appearance_source.appearance.clone();
    target_appearance.fill = Some(FillAppearance::Solid {
        color: appearance::color(224, 238, 252),
        alpha: appearance::fraction(0)?,
    });
    let (output, appearance_receipt) = appearance::lower(
        section,
        0,
        8_101,
        18_101,
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetSolidFill,
        appearance_source.appearance,
        target_appearance,
    )?;
    Ok((output, appearance::evidence(&appearance_receipt)))
}

fn paragraph_band_semantic_evidence(
    source_section: &[u8],
    output_section: &[u8],
) -> Result<LoweringEvidence, AnyError> {
    let limits = special_limits()?;
    let semantic_source = empty_source_state()?;
    let request = ObjectSpecialRequest::from_draft(
        ObjectSpecialRequestDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-paragraph-band-request")?,
            expected_source_state_sha256: semantic_source.canonical_sha256(limits)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation: ObjectSpecialOperation::InsertParagraphBand {
                insertion_index: 0,
                object: paragraph_band_object()?,
            },
        },
        &semantic_source,
        FLOW_BEFORE,
        limits,
    )?;
    let semantic_plan =
        ObjectSpecialBuilder::plan(&semantic_source, &request, FLOW_BEFORE, limits)?;
    Ok(LoweringEvidence {
        profile_id: "hwpx-agent.object-paragraph-band.rectangle-behind-paragraph/v1".to_owned(),
        capability_id: semantic_plan.capability_id().to_owned(),
        plan_sha256: semantic_plan.plan_sha256().to_owned(),
        source_section_sha256: sha256(source_section),
        output_section_sha256: sha256(output_section),
        modified_unit_count: 1,
    })
}

fn caption_insert_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(shape_package)?;
    let source = source_state()?;
    let caption = ObjectCaption {
        side: ObjectCaptionSide::Bottom,
        gap_hwpunit: 360,
        width_hwpunit: 7_200,
        numbering: ObjectCaptionNumbering::None,
        label: "P08 ".to_owned(),
        text: "inserted caption".to_owned(),
    };
    let limits = special_limits()?;
    let request = ObjectSpecialRequest::from_draft(
        ObjectSpecialRequestDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-caption-insert-request")?,
            expected_source_state_sha256: source.canonical_sha256(limits)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation: ObjectSpecialOperation::InsertCaption {
                target: shape_identity()?,
                caption,
            },
        },
        &source,
        FLOW_BEFORE,
        limits,
    )?;
    let domain = ObjectSpecialBuilder::plan(&source, &request, FLOW_BEFORE, limits)?;
    let plan = ObjectCaptionInsertHwpxBuilder::plan(
        &section,
        &domain,
        FLOW_BEFORE,
        limits,
        ObjectCaptionInsertHwpxLimits::default(),
    )?;
    let (output, receipt) = ObjectCaptionInsertHwpxLowerer::lower_in_section_with_receipt(
        &section,
        &plan,
        FLOW_BEFORE,
        limits,
        ObjectCaptionInsertHwpxLimits::default(),
    )?;
    prepared_from_section(
        "P08-19-C38",
        "OBJ-013",
        "obj.caption_insert",
        "obj-013-caption-insert.hwpx",
        shape_package,
        &output,
        vec![caption_evidence(&receipt)],
        "rectangle",
        8_101,
        18_101,
        false,
    )
}

fn form_insert_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(shape_package)?;
    let source = source_state()?;
    let limits = special_limits()?;
    let request = ObjectSpecialRequest::from_draft(
        ObjectSpecialRequestDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-form-insert-request")?,
            expected_source_state_sha256: source.canonical_sha256(limits)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation: ObjectSpecialOperation::InsertFormObject {
                insertion_index: 1,
                object: form_object()?,
            },
        },
        &source,
        FLOW_BEFORE,
        limits,
    )?;
    let domain = ObjectSpecialBuilder::plan(&source, &request, FLOW_BEFORE, limits)?;
    let plan = ObjectFormInsertHwpxBuilder::plan(
        &section,
        &domain,
        FLOW_BEFORE,
        limits,
        ObjectFormInsertHwpxLimits::default(),
    )?;
    let (output, receipt) = ObjectFormInsertHwpxLowerer::lower_in_section_with_receipt(
        &section,
        &plan,
        FLOW_BEFORE,
        limits,
        ObjectFormInsertHwpxLimits::default(),
    )?;
    prepared_from_section(
        "P08-19-C39",
        "OBJ-012",
        "obj.form_object_insert",
        "obj-012-form-insert.hwpx",
        shape_package,
        &output,
        vec![form_evidence(&receipt)],
        "edit",
        8_112,
        18_112,
        false,
    )
}

fn source_state() -> Result<ObjectSpecialDocumentState, AnyError> {
    let limits = special_limits()?;
    let resource_ids = Vec::new();
    let relationship_ids = Vec::new();
    let resource_inventory_sha256 = ObjectSpecialDocumentState::resource_inventory_sha256_for(
        &resource_ids,
        &relationship_ids,
        limits,
    )?;
    Ok(ObjectSpecialDocumentState::from_draft(
        ObjectSpecialDocumentStateDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            document_order: vec![LogicalId::parse("object-8101")?],
            external_objects: vec![shape_identity()?],
            special_objects: Vec::new(),
            captions: Vec::new(),
            paragraph_ids: vec![LogicalId::parse("paragraph-1")?],
            resource_ids,
            relationship_ids,
            document_payload_sha256: STATE_C.to_owned(),
            document_properties_sha256: STATE_D.to_owned(),
            resource_inventory_sha256,
            paragraph_inventory_sha256: STATE_E.to_owned(),
            opaque_document_state_sha256: FLOW_AFTER.to_owned(),
        },
        limits,
    )?)
}

fn shape_identity() -> Result<ObjectIdentity, AnyError> {
    Ok(ObjectIdentity {
        logical_object_id: LogicalId::parse("object-8101")?,
        native_object_id: 8_101,
        native_instance_id: 18_101,
    })
}

fn form_object() -> Result<SpecialObjectState, AnyError> {
    Ok(SpecialObjectState {
        identity: ObjectIdentity {
            logical_object_id: LogicalId::parse("object-8112")?,
            native_object_id: 8_112,
            native_instance_id: 18_112,
        },
        object_kind: SpecialObjectKind::FormObject,
        geometry_state_sha256: STATE_C.to_owned(),
        appearance_state_sha256: STATE_D.to_owned(),
        property_state_sha256: STATE_E.to_owned(),
        resource_state_sha256: FLOW_BEFORE.to_owned(),
        embedded_content_state_sha256: FLOW_AFTER.to_owned(),
        opaque_state_sha256: STATE_C.to_owned(),
        payload: SpecialObjectPayload::FormObject {
            form: StaticFormPayload {
                control_kind: StaticFormControlKind::EditBox,
                name: "p08field".to_owned(),
                value: "P08 FORM INSERT".to_owned(),
                enabled: true,
                printable: true,
                active_content_present: false,
                form_properties_sha256: OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256.to_owned(),
            },
        },
    })
}

fn paragraph_band_object() -> Result<SpecialObjectState, AnyError> {
    let band_style_sha256 = sha256(
        format!(
            "behind-paragraph\nwidth={PARAGRAPH_BAND_WIDTH}\nheight={PARAGRAPH_BAND_HEIGHT}\nfill=#e0eefc\n"
        )
        .as_bytes(),
    );
    Ok(SpecialObjectState {
        identity: shape_identity()?,
        object_kind: SpecialObjectKind::ParagraphBand,
        geometry_state_sha256: STATE_C.to_owned(),
        appearance_state_sha256: STATE_D.to_owned(),
        property_state_sha256: STATE_E.to_owned(),
        resource_state_sha256: FLOW_BEFORE.to_owned(),
        embedded_content_state_sha256: FLOW_AFTER.to_owned(),
        opaque_state_sha256: STATE_C.to_owned(),
        payload: SpecialObjectPayload::ParagraphBand {
            band: ParagraphBandPayload {
                paragraph_id: LogicalId::parse("paragraph-1")?,
                placement: ParagraphBandPlacement::BehindParagraph,
                height_hwpunit: PARAGRAPH_BAND_HEIGHT,
                width_hwpunit: PARAGRAPH_BAND_WIDTH,
                band_style_sha256,
            },
        },
    })
}

fn empty_source_state() -> Result<ObjectSpecialDocumentState, AnyError> {
    let limits = special_limits()?;
    let resource_ids = Vec::new();
    let relationship_ids = Vec::new();
    let resource_inventory_sha256 = ObjectSpecialDocumentState::resource_inventory_sha256_for(
        &resource_ids,
        &relationship_ids,
        limits,
    )?;
    Ok(ObjectSpecialDocumentState::from_draft(
        ObjectSpecialDocumentStateDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            document_order: Vec::new(),
            external_objects: Vec::new(),
            special_objects: Vec::new(),
            captions: Vec::new(),
            paragraph_ids: vec![LogicalId::parse("paragraph-1")?],
            resource_ids,
            relationship_ids,
            document_payload_sha256: STATE_C.to_owned(),
            document_properties_sha256: STATE_D.to_owned(),
            resource_inventory_sha256,
            paragraph_inventory_sha256: STATE_E.to_owned(),
            opaque_document_state_sha256: FLOW_AFTER.to_owned(),
        },
        limits,
    )?)
}

fn qualified_drawing_gallery_template() -> Result<Vec<u8>, AnyError> {
    let path = Path::new(DRAWING_GALLERY_TEMPLATE_PATH);
    let metadata = fs::symlink_metadata(path)?;
    if metadata.file_type().is_symlink()
        || !metadata.is_file()
        || usize::try_from(metadata.len())? != DRAWING_GALLERY_TEMPLATE_BYTES
    {
        return Err("drawing-gallery Rectangle.drt identity is invalid".into());
    }
    let bytes = fs::read(path)?;
    if bytes.len() != DRAWING_GALLERY_TEMPLATE_BYTES
        || bytes.get(..COMPOUND_FILE_MAGIC.len()) != Some(COMPOUND_FILE_MAGIC)
        || sha256(&bytes) != DRAWING_GALLERY_TEMPLATE_SHA256
    {
        return Err("drawing-gallery Rectangle.drt digest or format drifted".into());
    }
    Ok(bytes)
}

fn replace_fixture_marker(
    section: &[u8],
    source_marker: &str,
    target_marker: &str,
) -> Result<Vec<u8>, AnyError> {
    let text = std::str::from_utf8(section)?;
    if text.matches(source_marker).count() != 1 || text.contains(target_marker) {
        return Err("fixture marker is absent or ambiguous".into());
    }
    Ok(text.replacen(source_marker, target_marker, 1).into_bytes())
}

fn special_limits() -> Result<ObjectSpecialLimits, AnyError> {
    Ok(ObjectSpecialLimits::new(
        ObjectSpecialLimitConfig::default(),
    )?)
}

fn caption_evidence(receipt: &ObjectCaptionInsertHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: receipt.modified_span_count,
    }
}

fn form_evidence(receipt: &ObjectFormInsertHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: receipt.modified_span_count,
    }
}
