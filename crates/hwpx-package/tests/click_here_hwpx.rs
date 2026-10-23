#![allow(clippy::expect_used)] // Bounded immutable test fixtures.
use domain_ir::{
    FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult, FieldDefinition,
    FieldDocumentState, FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineLimitConfig,
    FieldEngineLimits, FieldIdentity, FieldOperation, FieldPlan, FieldRequest, FieldRequestDraft,
    FieldState, FieldUpdatePolicy, LogicalId,
};
use hwpx_package::{
    ClickHereHwpxBuilder, ClickHereHwpxLimits, ClickHereHwpxLowerer, ClickHereHwpxReader,
};
use sha2::{Digest as _, Sha256};
use std::{fs, io::Read, path::Path};
const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const FILLED: &str = r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p id="1" paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:unknown preserved="yes"/><hp:ctrl><hp:fieldBegin id="10" type="CLICK_HERE" name="field" editable="1" dirty="1" zorder="-1" fieldid="100"><hp:parameters cnt="4" name=""><hp:integerParam name="Prop">9</hp:integerParam><hp:stringParam name="Command" xml:space="preserve">opaque-command</hp:stringParam><hp:stringParam name="Direction">guide &amp; &lt;prompt&gt;</hp:stringParam><hp:stringParam name="HelpState">help</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>old</hp:t><hp:ctrl><hp:fieldEnd beginIDRef="10" fieldid="100"/></hp:ctrl><hp:t>outside &amp; exact</hp:t></hp:run></hp:p></hs:sec>"#;
fn id(s: &str) -> LogicalId {
    LogicalId::parse(s).expect("id")
}
fn limits() -> FieldEngineLimits {
    FieldEngineLimits::new(FieldEngineLimitConfig::default()).expect("limits")
}
fn map() -> Vec<LogicalId> {
    vec![id("p-1")]
}
fn state(source: &[u8]) -> FieldDocumentState {
    let observed =
        ClickHereHwpxReader::inspect_section(source, &map(), ClickHereHwpxLimits::default())
            .expect("inspect");
    let fields = observed
        .into_iter()
        .enumerate()
        .map(|(i, p)| FieldState {
            identity: FieldIdentity {
                logical_field_id: id(&format!("field-{i}")),
                native_begin_id: u32::try_from(i * 2 + 1).expect("id"),
                native_end_id: u32::try_from(i * 2 + 2).expect("id"),
            },
            anchor: FieldAnchor {
                paragraph_id: p.paragraph_id,
                run_ordinal: p.run_ordinal,
                inline_ordinal: p.inline_ordinal,
            },
            definition: FieldDefinition::ClickHere { prompt: p.prompt },
            cached_result: FieldCachedResult::Text { display: p.display },
            update_policy: FieldUpdatePolicy::RecomputeDirect,
            cache_status: FieldCacheStatus::Current,
            locked: false,
            evaluation_context_sha256: None,
            character_style_sha256: p.character_style_sha256,
            paragraph_style_sha256: p.paragraph_style_sha256,
            field_payload_sha256: p.parameters_sha256,
            opaque_properties: vec![],
        })
        .collect();
    FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.into(),
            fields,
            non_field_content_sha256: A.into(),
            style_catalog_sha256: B.into(),
            reference_inventory_sha256: A.into(),
            resource_inventory_sha256: B.into(),
            opaque_document_state_sha256: A.into(),
        },
        limits(),
    )
    .expect("state")
}
fn plan(current: &FieldDocumentState, display: &str) -> FieldPlan {
    let request = FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.into(),
            request_id: id("request-1"),
            expected_source_state_sha256: current.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: A.into(),
            target_document_flow_sha256: B.into(),
            operation: FieldOperation::UpdateResult {
                target: current.fields()[0].identity.clone(),
                cached_result: FieldCachedResult::Text {
                    display: display.into(),
                },
                evaluation_context_sha256: B.into(),
            },
        },
        current,
        A,
        limits(),
    )
    .expect("request");
    FieldEngineBuilder::plan(current, &request, A, limits()).expect("domain plan")
}
fn lower(source: &[u8], display: &str) -> Vec<u8> {
    let s = state(source);
    let d = plan(&s, display);
    let p = ClickHereHwpxBuilder::plan(
        source,
        &s,
        &d,
        A,
        &map(),
        limits(),
        ClickHereHwpxLimits::default(),
    )
    .expect("adapter plan");
    let (out, receipt) = ClickHereHwpxLowerer::lower_section_with_receipt(
        source,
        &p,
        &s,
        A,
        &map(),
        limits(),
        ClickHereHwpxLimits::default(),
    )
    .expect("lower");
    assert!(receipt.outside_declared_edits_byte_exact);
    assert_eq!(
        receipt.target_section_sha256,
        <[u8; 32]>::from(Sha256::digest(&out))
    );
    assert_eq!(
        receipt.typed_target_readback.state,
        d.target_state().clone()
    );
    if !display.is_empty() {
        assert!(!format!("{p:?}{receipt:?}").contains(display));
    }
    out
}
#[test]
fn updates_one_cache_escapes_xml_and_preserves_every_other_byte() {
    let result = lower(FILLED.as_bytes(), "new & <value> 한글 🚀");
    let expected = FILLED.replace(
        "<hp:t>old</hp:t>",
        "<hp:t>new &amp; &lt;value&gt; 한글 🚀</hp:t>",
    );
    assert_eq!(result, expected.as_bytes());
    assert_eq!(result, lower(FILLED.as_bytes(), "new & <value> 한글 🚀"));
}
#[test]
fn updates_empty_prompt_across_runs_without_restructuring_styles() {
    let source=FILLED.replace("dirty=\"1\"","dirty=\"0\"").replace("<hp:t>old</hp:t>",
        "</hp:run><hp:run charPrIDRef=\"7\"><hp:t>guide &amp; &lt;prompt&gt;</hp:t></hp:run><hp:run charPrIDRef=\"0\">");
    let observed = ClickHereHwpxReader::inspect_section(
        source.as_bytes(),
        &map(),
        ClickHereHwpxLimits::default(),
    )
    .expect("empty");
    assert_eq!(observed[0].display, "");
    let out = lower(source.as_bytes(), "filled");
    assert_eq!(
        out,
        source
            .replace("dirty=\"0\"", "dirty=\"1\"")
            .replace(
                "<hp:t>guide &amp; &lt;prompt&gt;</hp:t>",
                "<hp:t>filled</hp:t>"
            )
            .as_bytes()
    );
}
#[test]
fn clears_additional_plain_text_nodes_and_supports_empty_target() {
    let source = FILLED.replace(
        "<hp:t>old</hp:t>",
        "<hp:t>ol</hp:t></hp:run><hp:run charPrIDRef=\"2\"><hp:t>d</hp:t>",
    );
    let out = lower(source.as_bytes(), "");
    assert_eq!(
        out,
        source
            .replace("<hp:t>ol</hp:t>", "<hp:t></hp:t>")
            .replace("<hp:t>d</hp:t>", "<hp:t></hp:t>")
            .as_bytes()
    );
}
#[test]
fn supports_self_closing_plain_cache_and_alternate_namespace_prefix() {
    let source = FILLED
        .replace("<hp:t>old</hp:t>", "<hp:t/>")
        .replace("hp:", "para:")
        .replace("xmlns:hp=", "xmlns:para=");
    assert_eq!(
        lower(source.as_bytes(), "value"),
        source
            .replace("<para:t/>", "<para:t>value</para:t>")
            .as_bytes()
    );
}
#[test]
fn actual_captured_empty_filled_and_reopened_native_packages_are_read_and_lowered() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let dir =
        root.join("implementation/p09/evidence/private/p09-22-click-here-discovery-20261002-01");
    for (name, expected, display) in [
        (
            "empty",
            "60a646f488941bad203d1c1d8bab43a36f2ae5c4712396eeeb3c1acb81d50747",
            "",
        ),
        (
            "filled",
            "ab6d2d2d8f9d4375c30b16b80e963a71c31c3b3ed6c7466f5bc3da872b00ebaf",
            "P09 value & <text> 한글",
        ),
        (
            "reopened",
            "0e7ee2da6dada710f464ceaefd581a32f00ef1fbe646398d4af547ddf8aa74d0",
            "P09 value & <text> 한글",
        ),
    ] {
        let bytes =
            fs::read(dir.join(format!("{name}.hwpx"))).expect("required current-PC evidence");
        assert_eq!(hex::encode(Sha256::digest(&bytes)), expected);
        let mut archive = zip::ZipArchive::new(std::io::Cursor::new(bytes)).expect("zip");
        let mut xml = Vec::new();
        archive
            .by_name("Contents/section0.xml")
            .expect("section")
            .read_to_end(&mut xml)
            .expect("read");
        let native =
            ClickHereHwpxReader::inspect_section(&xml, &map(), ClickHereHwpxLimits::default())
                .expect("native");
        assert_eq!(native.len(), 1);
        assert_eq!(native[0].native_begin_id, 1_210_042_100);
        assert_eq!(native[0].native_field_id, 627_272_811);
        assert_eq!(native[0].display, display);
        assert_eq!(native[0].prompt, "P09 prompt & <guide>");
        let out = lower(&xml, "new verified cache");
        let next =
            ClickHereHwpxReader::inspect_section(&out, &map(), ClickHereHwpxLimits::default())
                .expect("target");
        assert_eq!(next[0].display, "new verified cache");
        assert_eq!(native[0].parameters_sha256, next[0].parameters_sha256);
    }
}
#[test]
fn rejects_unsupported_or_ambiguous_native_pairs_and_parameter_weakening() {
    for source in [
        FILLED.replace("CLICK_HERE", "DATE"),
        FILLED.replace("beginIDRef=\"10\"", "beginIDRef=\"11\""),
        FILLED.replace("fieldid=\"100\"/>", "fieldid=\"101\"/>"),
        FILLED.replace("editable=\"1\"", "editable=\"0\""),
        FILLED.replace("<hp:t>old</hp:t>", "<hp:t><hp:tab/></hp:t>"),
        FILLED.replace("<hp:t>old</hp:t>", "<hp:unknown/><hp:t>old</hp:t>"),
        FILLED.replace("cnt=\"4\"", "cnt=\"3\""),
        FILLED.replace(">9</hp:integerParam>", ">8</hp:integerParam>"),
        FILLED.replace("name=\"HelpState\"", "name=\"Unknown\""),
        FILLED.replace("dirty=\"1\"", "dirty=\"0\""),
        FILLED.replace("<hp:ctrl><hp:fieldBegin", "<hp:ctrl>stray<hp:fieldBegin"),
        FILLED.replace(
            "<hp:ctrl><hp:fieldEnd",
            "<hp:ctrl unexpected=\"1\"><hp:fieldEnd",
        ),
        FILLED.replace("<hp:t>old</hp:t>", "stray<hp:t>old</hp:t>"),
        FILLED.replace(
            "<hp:t>old</hp:t>",
            "<hp:t>old</hp:t></hp:run></hp:p><hp:p id=\"2\"><hp:run>",
        ),
    ] {
        assert!(
            ClickHereHwpxReader::inspect_section(
                source.as_bytes(),
                &map(),
                ClickHereHwpxLimits::default()
            )
            .is_err()
        );
    }
}
#[test]
fn rejects_source_state_flow_map_and_opaque_parameter_drift_at_plan_and_build() {
    let s = state(FILLED.as_bytes());
    let d = plan(&s, "new");
    let l = ClickHereHwpxLimits::default();
    let p = ClickHereHwpxBuilder::plan(FILLED.as_bytes(), &s, &d, A, &map(), limits(), l)
        .expect("plan");
    for source in [
        FILLED.replace("opaque-command", "different-command"),
        FILLED.replace("<hp:t>old</hp:t>", "<hp:t>other</hp:t>"),
        FILLED.replace("charPrIDRef=\"0\"", "charPrIDRef=\"1\""),
    ] {
        assert!(
            ClickHereHwpxBuilder::plan(source.as_bytes(), &s, &d, A, &map(), limits(), l).is_err()
        );
        assert!(
            ClickHereHwpxLowerer::lower_section_with_receipt(
                source.as_bytes(),
                &p,
                &s,
                A,
                &map(),
                limits(),
                l
            )
            .is_err()
        );
    }
    let changed = FILLED.replace("preserved=\"yes\"", "preserved=\"changed\"");
    assert!(
        ClickHereHwpxLowerer::lower_section_with_receipt(
            changed.as_bytes(),
            &p,
            &s,
            A,
            &map(),
            limits(),
            l
        )
        .is_err()
    );
    assert!(ClickHereHwpxBuilder::plan(FILLED.as_bytes(), &s, &d, B, &map(), limits(), l).is_err());
    assert!(
        ClickHereHwpxLowerer::lower_section_with_receipt(
            FILLED.as_bytes(),
            &p,
            &s,
            A,
            &[id("changed")],
            limits(),
            l
        )
        .is_err()
    );
}
#[test]
fn limits_and_redacted_debug_are_enforced() {
    for values in [
        (0, 1, 1, 1),
        (3 * 1024 * 1024, 1, 1, 1),
        (1, 0, 1, 1),
        (1, 1, 0, 1),
        (1, 1, 1, 0),
    ] {
        assert!(ClickHereHwpxLimits::new(values.0, values.1, values.2, values.3).is_err());
    }
    let l = ClickHereHwpxLimits::new(10, 1, 10, 1000).expect("small");
    assert!(ClickHereHwpxReader::inspect_section(FILLED.as_bytes(), &map(), l).is_err());
    let observed = ClickHereHwpxReader::inspect_section(
        FILLED.as_bytes(),
        &map(),
        ClickHereHwpxLimits::default(),
    )
    .expect("native");
    let debug = format!("{observed:?}");
    for value in ["opaque-command", "guide", "old", "100", "field"] {
        assert!(!debug.contains(value));
    }
}
