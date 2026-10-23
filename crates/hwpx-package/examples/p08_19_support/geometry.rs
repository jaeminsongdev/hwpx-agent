use domain_ir::{
    LogicalId, OBJECT_GEOMETRY_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAnchor, ObjectExtent,
    ObjectFlip, ObjectGeometryBuilder, ObjectGeometryLimits, ObjectGeometryOperation,
    ObjectGeometryRequest, ObjectGeometryRequestDraft, ObjectHorizontalAlignment,
    ObjectHorizontalReference, ObjectOuterMargins, ObjectPosition, ObjectRotation, ObjectSize,
    ObjectTextFlow, ObjectTextWrap, ObjectVerticalAlignment, ObjectVerticalReference,
    ObjectWidthReference, ObjectWrap,
};
use hwpx_package::{
    ObjectGeometryHwpxBuilder, ObjectGeometryHwpxLimits, ObjectGeometryHwpxLowerer,
    ObjectGeometryHwpxLoweringReceipt, ObjectGeometryHwpxReader,
};

use super::common::{
    AnyError, FLOW_AFTER, FLOW_BEFORE, LoweringEvidence, PreparedCase, hex, prepared_from_section,
    section_from_package,
};

const OBJECT_ID: u32 = 8_101;
const INSTANCE_ID: u32 = 18_101;

#[allow(clippy::too_many_lines)] // One table keeps all six geometry rows visibly complete.
pub fn cases(shape_package: &[u8]) -> Result<Vec<PreparedCase>, AnyError> {
    let source = section_from_package(shape_package)?;
    let readback = read(&source)?;

    let mut size_component = readback.state.component();
    size_component.offset.x_hwpunit = 720;
    size_component.original_size = ObjectExtent {
        width_hwpunit: 14_400,
        height_hwpunit: 7_200,
    };
    size_component.current_size = ObjectExtent {
        width_hwpunit: 14_400,
        height_hwpunit: 7_200,
    };
    size_component.transform.scale = ObjectAffineMatrix {
        e1_millionths: 1_333_333,
        e2_millionths: 0,
        e3_millionths: 0,
        e4_millionths: 0,
        e5_millionths: 1_333_333,
        e6_millionths: 0,
    };

    let mut rotation_transform = readback.state.component().transform;
    rotation_transform.rotation = ObjectAffineMatrix {
        e1_millionths: 707_107,
        e2_millionths: 707_107,
        e3_millionths: 1_000_000,
        e4_millionths: -707_107,
        e5_millionths: 707_107,
        e6_millionths: 2_000_000,
    };

    let operations = vec![
        (
            "P08-19-C05",
            "OBJ-015",
            "obj.position",
            "obj-015-position.hwpx",
            ObjectGeometryOperation::SetPosition {
                position: ObjectPosition {
                    horizontal_alignment: ObjectHorizontalAlignment::Right,
                    vertical_alignment: ObjectVerticalAlignment::Bottom,
                    horizontal_offset_hwpunit: 4_000,
                    vertical_offset_hwpunit: 6_000,
                },
            },
        ),
        (
            "P08-19-C06",
            "OBJ-016",
            "obj.size",
            "obj-016-size.hwpx",
            ObjectGeometryOperation::SetSize {
                size: ObjectSize {
                    width_hwpunit: 14_400,
                    width_reference: ObjectWidthReference::Page,
                    height_hwpunit: 7_200,
                    height_reference: domain_ir::ObjectHeightReference::Page,
                    protect: true,
                },
                component: size_component,
            },
        ),
        (
            "P08-19-C07",
            "OBJ-017",
            "obj.anchor",
            "obj-017-anchor.hwpx",
            ObjectGeometryOperation::SetAnchor {
                anchor: ObjectAnchor {
                    treat_as_character: true,
                    affect_line_spacing: true,
                    flow_with_text: false,
                    allow_overlap: true,
                    hold_anchor_and_shape: false,
                    horizontal_reference: ObjectHorizontalReference::Page,
                    vertical_reference: ObjectVerticalReference::Page,
                },
            },
        ),
        (
            "P08-19-C08",
            "OBJ-018",
            "obj.wrap",
            "obj-018-wrap.hwpx",
            ObjectGeometryOperation::SetWrap {
                wrap: ObjectWrap {
                    text_wrap: ObjectTextWrap::Square,
                    text_flow: ObjectTextFlow::LargestOnly,
                },
                outer_margins: ObjectOuterMargins {
                    left_hwpunit: 200,
                    right_hwpunit: 300,
                    top_hwpunit: 400,
                    bottom_hwpunit: 500,
                },
            },
        ),
        (
            "P08-19-C09",
            "OBJ-032",
            "obj.rotate",
            "obj-032-rotate.hwpx",
            ObjectGeometryOperation::SetRotation {
                rotation: ObjectRotation {
                    angle_degrees: 45,
                    center_x_hwpunit: 5_400,
                    center_y_hwpunit: 2_700,
                    rotate_image: false,
                },
                transform: rotation_transform,
            },
        ),
        (
            "P08-19-C10",
            "OBJ-033",
            "obj.flip",
            "obj-033-flip.hwpx",
            ObjectGeometryOperation::SetFlip {
                flip: ObjectFlip {
                    horizontal: true,
                    vertical: false,
                },
                transform: readback.state.component().transform,
            },
        ),
    ];

    operations
        .into_iter()
        .map(|(case_id, feature_id, capability_id, file, operation)| {
            let (output, receipt) = lower(&source, operation)?;
            if receipt.capability_id != capability_id {
                return Err("geometry receipt capability drifted".into());
            }
            prepared_from_section(
                case_id,
                feature_id,
                capability_id,
                file,
                shape_package,
                &output,
                vec![evidence(&receipt)],
                "rectangle",
                OBJECT_ID,
                INSTANCE_ID,
                false,
            )
        })
        .collect()
}

pub fn protect_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let source = section_from_package(shape_package)?;
    let (output, receipt) = lower(
        &source,
        ObjectGeometryOperation::SetLocked { enabled: true },
    )?;
    prepared_from_section(
        "P08-19-C26",
        "OBJ-045",
        "obj.object_protect",
        "obj-045-object-protect.hwpx",
        shape_package,
        &output,
        vec![evidence(&receipt)],
        "rectangle",
        OBJECT_ID,
        INSTANCE_ID,
        false,
    )
}

pub(super) fn read(section: &[u8]) -> Result<hwpx_package::ObjectGeometryHwpxReadback, AnyError> {
    Ok(ObjectGeometryHwpxReader::read_in_section(
        section,
        0,
        LogicalId::parse("object-8101")?,
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
    )?)
}

pub(super) fn lower(
    section: &[u8],
    operation: ObjectGeometryOperation,
) -> Result<(Vec<u8>, ObjectGeometryHwpxLoweringReceipt), AnyError> {
    let readback = read(section)?;
    let request = ObjectGeometryRequest::from_draft(
        ObjectGeometryRequestDraft {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-geometry-request")?,
            expected_source_state_sha256: readback
                .state
                .canonical_sha256(ObjectGeometryLimits::default())?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation,
        },
        &readback.state,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
    )?;
    let domain = ObjectGeometryBuilder::plan(
        &readback.state,
        &request,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
    )?;
    let plan = ObjectGeometryHwpxBuilder::plan(
        section,
        0,
        &domain,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
    )?;
    Ok(ObjectGeometryHwpxLowerer::lower_in_section_with_receipt(
        section,
        &plan,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
    )?)
}

pub(super) fn evidence(receipt: &ObjectGeometryHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: receipt.modified_attribute_count,
    }
}
