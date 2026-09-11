use std::error::Error;
use std::io::{Cursor, Write};

use domain_ir::{MathAstDraft, MathAstLimits};
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits,
    EqEditParseRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, EQUATION_HWPX_PROFILE_ID, EQUATION_HWPX_SCHEMA_VERSION, EquationColor,
    EquationExtent, EquationExtentSource, EquationHwpxBuilder, EquationHwpxError,
    EquationHwpxLimitConfig, EquationHwpxLimits, EquationHwpxLowerer, EquationHwpxReader,
    EquationHwpxRequest, EquationHwpxRequestDraft, EquationLayout, EquationStyle, IdIndexLimits,
    PackageGraph, PackageGraphLimits, PackageLimits, PreservingWriter, WriterLimits,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;
type TestReader = BoundedZipReader<Cursor<Vec<u8>>>;

const FLOW_BEFORE: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_AFTER: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const SECTION_PATH: &str = "Contents/section0.xml";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;

const HEADER: &str = r#"<h:head xmlns:h="http://www.hancom.co.kr/hwpml/2011/head">
  <h:fontface lang="HANGUL"><h:font id="1"/></h:fontface>
  <h:fontface lang="LATIN"><h:font id="1"/></h:fontface>
  <h:fontface lang="HANJA"><h:font id="1"/></h:fontface>
  <h:fontface lang="JAPANESE"><h:font id="1"/></h:fontface>
  <h:fontface lang="OTHER"><h:font id="1"/></h:fontface>
  <h:fontface lang="SYMBOL"><h:font id="1"/></h:fontface>
  <h:fontface lang="USER"><h:font id="1"/></h:fontface>
  <h:borderFill id="1"/>
  <h:charPr id="1" borderFillIDRef="1"><h:fontRef hangul="1" latin="1" hanja="1" japanese="1" other="1" symbol="1" user="1"/></h:charPr>
  <h:tabPr id="1"/><h:numbering id="1"/><h:bullet id="1"/>
  <h:paraPr id="1" tabPrIDRef="1"><h:heading type="OUTLINE" idRef="0"/><h:paraHead charPrIDRef="1"/></h:paraPr>
  <h:style id="1" charPrIDRef="1" paraPrIDRef="1" nextStyleIDRef="1"/><h:memoShape id="1"/>
</h:head>"#;

#[test]
fn display_ast_lowers_to_exact_native_object_and_closed_package() -> TestResult {
    let section = display_section();
    let bytes = valid_archive(&section)?;
    let (mut reader, graph) = open_graph(bytes)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        EquationLayout::Display,
        limits,
    )?;
    assert_eq!(source.equation_count(), 0);
    let request = request(&source, EquationLayout::Display, 77, &limits)?;
    let lowered = EquationHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits)?;

    assert!(lowered.receipt().preservation_verified());
    assert!(lowered.receipt().native_readback_verified());
    assert!(lowered.receipt().render_required());
    assert_ne!(
        lowered.receipt().output_section_sha256(),
        source.section_sha256()
    );
    assert_eq!(lowered.patch().changed_parts(), 1);
    assert_eq!(lowered.patch().added_parts(), 0);
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    Ok(())
}

#[test]
fn inline_layout_is_structurally_distinct_and_semantically_read_back() -> TestResult {
    let bytes = valid_archive(&inline_section())?;
    let (mut reader, graph) = open_graph(bytes)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        1,
        EquationLayout::Inline,
        limits,
    )?;
    let request = request(&source, EquationLayout::Inline, 91, &limits)?;
    let lowered = EquationHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits)?;
    assert!(lowered.receipt().native_readback_verified());
    assert_eq!(lowered.patch().changed_parts(), 1);
    Ok(())
}

#[test]
fn exact_current_profile_native_reader_inspects_script_style_extent_and_layout() -> TestResult {
    let section = format!(
        concat!(
            "<hs:sec xmlns:hs=\"{section_ns}\" xmlns:q=\"{ns}\"><q:p id=\"1\" paraPrIDRef=\"1\" styleIDRef=\"1\">",
            "<q:run charPrIDRef=\"1\"><q:equation id=\"55\" zOrder=\"0\" numberingType=\"EQUATION\" ",
            "textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" ",
            "version=\"Equation Version 60\" baseLine=\"85\" textColor=\"#102030\" baseUnit=\"1000\" lineMode=\"CHAR\" font=\"HancomEQN\">",
            "<q:sz width=\"17000\" widthRelTo=\"ABSOLUTE\" height=\"6000\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<q:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"0\" ",
            "vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<q:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<q:script>sum _{{i=1}} ^{{32}} {{i^2}} + int _0 ^1 {{x^4 + 3x^2 + 1}} dx = 10416</q:script>",
            "</q:equation><q:t/></q:run></q:p></hs:sec>"
        ),
        section_ns = SECTION_NS,
        ns = PARAGRAPH_NS,
    );
    let readback =
        EquationHwpxReader::read_in_section(section.as_bytes(), 0, EquationHwpxLimits::default())?;
    assert_eq!(readback.object_id(), 55);
    assert_eq!(readback.layout(), EquationLayout::Display);
    assert_eq!(
        readback.style().text_color,
        EquationColor {
            red: 16,
            green: 32,
            blue: 48
        }
    );
    assert_eq!(readback.extent().width_hwpunit, 17_000);
    assert_eq!(readback.native_object_count(), 1);
    assert!(!readback.semantic_sha256().is_empty());
    assert!(!readback.script_sha256().is_empty());
    Ok(())
}

#[test]
fn saved_target_line_cache_is_admitted_without_weakening_equation_shape() -> TestResult {
    let base = native_section("x + 1", 8);
    let with_line_cache = base.replace(
        "</q:run></q:p>",
        concat!(
            "</q:run><q:linesegarray><q:lineseg textpos=\"0\" vertpos=\"1600\" ",
            "vertsize=\"6000\" textheight=\"6000\" baseline=\"5100\" spacing=\"3600\" ",
            "horzpos=\"0\" horzsize=\"42520\" flags=\"393216\"/>",
            "</q:linesegarray></q:p>"
        ),
    );
    let readback = EquationHwpxReader::read_in_section(
        with_line_cache.as_bytes(),
        0,
        EquationHwpxLimits::default(),
    )?;
    assert_eq!(readback.object_id(), 8);

    let unknown = with_line_cache.replace("</q:p>", "<q:unknown/></q:p>");
    assert_code(
        EquationHwpxReader::read_in_section(unknown.as_bytes(), 0, EquationHwpxLimits::default()),
        "equation_hwpx_readback_mismatch",
    );
    Ok(())
}

#[test]
fn request_rejects_source_and_flow_drift_at_admission() -> TestResult {
    let bytes = valid_archive(&display_section())?;
    let (mut reader, graph) = open_graph(bytes)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        EquationLayout::Display,
        limits,
    )?;
    let mut draft = request_draft(&source, EquationLayout::Display, 9, &limits)?;
    draft.expected_section_sha256 = "0".repeat(64);
    assert_code(
        EquationHwpxRequest::from_draft(draft, &source, FLOW_BEFORE, limits),
        "equation_hwpx_source_drift",
    );

    let draft = request_draft(&source, EquationLayout::Display, 9, &limits)?;
    assert_code(
        EquationHwpxRequest::from_draft(draft, &source, &"c".repeat(64), limits),
        "equation_hwpx_flow_drift",
    );
    Ok(())
}

#[test]
fn lowerer_rechecks_package_and_document_flow_drift() -> TestResult {
    let initial = valid_archive(&display_section())?;
    let (mut initial_reader, initial_graph) = open_graph(initial)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut initial_reader,
        &initial_graph,
        SECTION_PATH,
        0,
        0,
        EquationLayout::Display,
        limits,
    )?;
    let request = request(&source, EquationLayout::Display, 11, &limits)?;
    assert_code(
        EquationHwpxLowerer::lower(
            &mut initial_reader,
            &initial_graph,
            &request,
            &"c".repeat(64),
            limits,
        ),
        "equation_hwpx_flow_drift",
    );

    let drifted = display_section().replace("styleIDRef=\"1\"", "styleIDRef=\"01\"");
    let (mut drifted_reader, drifted_graph) = open_graph(valid_archive(&drifted)?)?;
    assert_code(
        EquationHwpxLowerer::lower(
            &mut drifted_reader,
            &drifted_graph,
            &request,
            FLOW_BEFORE,
            limits,
        ),
        "equation_hwpx_source_drift",
    );
    Ok(())
}

#[test]
fn object_id_collision_and_ambiguous_targets_fail_closed() -> TestResult {
    let with_table = display_section().replace("<q:t/>", "<q:tbl id=\"44\"><q:t/></q:tbl>");
    let (mut bad_reader, bad_graph) = open_graph(valid_archive(&with_table)?)?;
    assert_code(
        EquationHwpxBuilder::inspect_source(
            &mut bad_reader,
            &bad_graph,
            SECTION_PATH,
            0,
            0,
            EquationLayout::Display,
            EquationHwpxLimits::default(),
        ),
        "equation_hwpx_unsupported_target",
    );

    let section = display_section().replace(
        "</hs:sec>",
        "<q:p id=\"2\"><q:run charPrIDRef=\"1\"><q:tbl id=\"44\"/><q:t/></q:run></q:p></hs:sec>",
    );
    let (mut reader, graph) = open_graph(valid_archive(&section)?)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        EquationLayout::Display,
        limits,
    )?;
    let request = request(&source, EquationLayout::Display, 44, &limits)?;
    assert_code(
        EquationHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits),
        "equation_hwpx_object_id_collision",
    );
    Ok(())
}

#[test]
fn provisional_extent_is_mandatory_until_estimator_gate() -> TestResult {
    let bytes = valid_archive(&display_section())?;
    let (mut reader, graph) = open_graph(bytes)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        EquationLayout::Display,
        limits,
    )?;
    let mut draft = request_draft(&source, EquationLayout::Display, 9, &limits)?;
    draft.extent.render_required = false;
    assert_code(
        EquationHwpxRequest::from_draft(draft, &source, FLOW_BEFORE, limits),
        "equation_hwpx_invalid_extent",
    );

    let mut draft = request_draft(&source, EquationLayout::Display, 9, &limits)?;
    draft.extent.source = EquationExtentSource::ValidatedEstimator;
    draft.extent.source_evidence_sha256 = Some("d".repeat(64));
    assert_code(
        EquationHwpxRequest::from_draft(draft, &source, FLOW_BEFORE, limits),
        "equation_hwpx_invalid_extent",
    );
    Ok(())
}

#[test]
fn strict_json_unknown_duplicate_and_limits_are_rejected() -> TestResult {
    let bytes = valid_archive(&display_section())?;
    let (mut reader, graph) = open_graph(bytes)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        EquationLayout::Display,
        limits,
    )?;
    let draft = request_draft(&source, EquationLayout::Display, 9, &limits)?;
    let json = serde_json::to_vec(&draft)?;
    assert!(EquationHwpxRequest::from_json(&json, &source, FLOW_BEFORE, limits).is_ok());
    let duplicate = format!(
        "{{\"schema_version\":\"duplicate\",{}",
        std::str::from_utf8(&json)?[1..].to_owned()
    );
    assert_code(
        EquationHwpxRequest::from_json(duplicate.as_bytes(), &source, FLOW_BEFORE, limits),
        "equation_hwpx_invalid_json",
    );

    let mut value = serde_json::to_value(&draft)?;
    let Some(object) = value.as_object_mut() else {
        return Err("serialized request was not an object".into());
    };
    object.insert(
        "raw_xml".to_owned(),
        serde_json::Value::String("<equation/>".to_owned()),
    );
    assert_code(
        EquationHwpxRequest::from_json(&serde_json::to_vec(&value)?, &source, FLOW_BEFORE, limits),
        "equation_hwpx_invalid_json",
    );

    let too_small = EquationHwpxLimits::new(
        EquationHwpxLimitConfig {
            serialized_bytes: 1,
            ..EquationHwpxLimitConfig::default()
        },
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        hwpx_package::PatchLimits::default(),
        MathAstLimits::default(),
        EqEditLimits::default(),
    )?;
    assert_code(
        EquationHwpxRequest::from_json(&json, &source, FLOW_BEFORE, too_small),
        "equation_hwpx_input_limit",
    );
    Ok(())
}

#[test]
fn tampered_native_shape_script_and_duplicate_ids_are_rejected() {
    let base = native_section("x + 1", 8);
    let limits = EquationHwpxLimits::default();
    assert!(EquationHwpxReader::read_in_section(base.as_bytes(), 0, limits).is_ok());
    for drifted in [
        base.replace("font=\"HancomEQN\"", "font=\"Arial\""),
        base.replace("treatAsChar=\"1\"", "treatAsChar=\"0\""),
        base.replace("<q:script>x + 1</q:script>", "<q:script>x +</q:script>"),
        base.replace("<q:outMargin", "<q:unknown"),
        base.replace("<q:t/>", "<q:t>unexpected</q:t>"),
    ] {
        assert!(EquationHwpxReader::read_in_section(drifted.as_bytes(), 0, limits).is_err());
    }
    let duplicate = base.replace(
        "</hs:sec>",
        &format!("{}</hs:sec>", native_equation_paragraph("y", 8)),
    );
    assert_code(
        EquationHwpxReader::read_in_section(duplicate.as_bytes(), 0, limits),
        "equation_hwpx_object_id_collision",
    );
}

#[test]
fn canonical_receipts_are_deterministic_and_debug_is_redacted() -> TestResult {
    let bytes = valid_archive(&display_section())?;
    let (mut reader, graph) = open_graph(bytes)?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        EquationLayout::Display,
        limits,
    )?;
    let request = request(&source, EquationLayout::Display, 14, &limits)?;
    assert_eq!(
        request.canonical_json(limits)?,
        request.canonical_json(limits)?
    );
    let lowered = EquationHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits)?;
    assert_eq!(
        lowered.receipt().canonical_json(limits)?,
        lowered.receipt().canonical_json(limits)?
    );
    let debug = format!("{source:?} {request:?} {:?}", lowered.receipt());
    for secret in [
        source.section_sha256(),
        request.semantic_sha256(),
        "14",
        "sum",
    ] {
        assert!(!debug.contains(secret), "debug leaked {secret}");
    }
    Ok(())
}

fn request(
    source: &hwpx_package::EquationHwpxSource,
    layout: EquationLayout,
    object_id: u32,
    limits: &EquationHwpxLimits,
) -> Result<EquationHwpxRequest, EquationHwpxError> {
    EquationHwpxRequest::from_draft(
        request_draft(source, layout, object_id, limits).map_err(|_| EquationHwpxError::MathAst)?,
        source,
        FLOW_BEFORE,
        *limits,
    )
}

fn request_draft(
    source: &hwpx_package::EquationHwpxSource,
    layout: EquationLayout,
    object_id: u32,
    limits: &EquationHwpxLimits,
) -> Result<EquationHwpxRequestDraft, Box<dyn Error>> {
    Ok(EquationHwpxRequestDraft {
        schema_version: EQUATION_HWPX_SCHEMA_VERSION.to_owned(),
        profile_id: EQUATION_HWPX_PROFILE_ID.to_owned(),
        section_part: source.section_part().to_owned(),
        paragraph_ordinal: 0,
        run_ordinal: usize::from(layout == EquationLayout::Inline),
        expected_package_state_sha256: source.package_state_sha256().to_owned(),
        expected_section_sha256: source.section_sha256().to_owned(),
        expected_paragraph_sha256: source.paragraph_sha256().to_owned(),
        expected_run_sha256: source.run_sha256().to_owned(),
        expected_object_ids_sha256: source.object_ids_sha256().to_owned(),
        expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
        target_document_flow_sha256: FLOW_AFTER.to_owned(),
        object_id,
        layout,
        style: EquationStyle::default(),
        extent: EquationExtent {
            width_hwpunit: 17_000,
            height_hwpunit: 6_000,
            source: EquationExtentSource::Provisional,
            source_evidence_sha256: None,
            render_required: true,
        },
        math_ast: ast_draft(
            "sum _{i=1} ^{32} {i^2} + int _0 ^1 {x^4 + 3x^2 + 1} dx = 10416",
            limits,
        )?,
    })
}

fn ast_draft(source: &str, limits: &EquationHwpxLimits) -> Result<MathAstDraft, Box<dyn Error>> {
    let parsed = EqEditEngine::new(limits.eqedit, limits.math)?.parse(EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source: source.to_owned(),
    })?;
    Ok(serde_json::from_slice(
        &parsed.ast().canonical_json(limits.math)?,
    )?)
}

fn display_section() -> String {
    format!(
        "<hs:sec xmlns:hs=\"{SECTION_NS}\" xmlns:q=\"{PARAGRAPH_NS}\"><q:p id=\"1\" paraPrIDRef=\"1\" styleIDRef=\"1\"><q:run charPrIDRef=\"1\"><q:t/></q:run></q:p></hs:sec>"
    )
}

fn inline_section() -> String {
    format!(
        "<hs:sec xmlns:hs=\"{SECTION_NS}\" xmlns:q=\"{PARAGRAPH_NS}\"><q:p id=\"1\" paraPrIDRef=\"1\" styleIDRef=\"1\"><q:run charPrIDRef=\"1\"><q:t>prefix</q:t></q:run><q:run charPrIDRef=\"1\"><q:t/></q:run></q:p></hs:sec>"
    )
}

fn native_section(script: &str, id: u32) -> String {
    format!(
        "<hs:sec xmlns:hs=\"{SECTION_NS}\" xmlns:q=\"{PARAGRAPH_NS}\">{}</hs:sec>",
        native_equation_paragraph(script, id)
    )
}

fn native_equation_paragraph(script: &str, id: u32) -> String {
    format!(
        concat!(
            "<q:p id=\"1\"><q:run charPrIDRef=\"1\"><q:equation id=\"{id}\" zOrder=\"0\" numberingType=\"EQUATION\" textWrap=\"TOP_AND_BOTTOM\" ",
            "textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" version=\"Equation Version 60\" baseLine=\"85\" textColor=\"#000000\" baseUnit=\"1000\" lineMode=\"CHAR\" font=\"HancomEQN\">",
            "<q:sz width=\"17000\" widthRelTo=\"ABSOLUTE\" height=\"6000\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<q:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"0\" vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<q:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/><q:script>{script}</q:script>",
            "</q:equation><q:t/></q:run></q:p>"
        ),
        id = id,
        script = script,
    )
}

fn valid_archive(section: &str) -> Result<Vec<u8>, zip::result::ZipError> {
    let opf = r#"<?xml version="1.0" encoding="UTF-8"?>
<o:package xmlns:o="http://www.idpf.org/2007/opf/" id="pkg" version="2.0">
  <o:manifest><o:item id="header" href="header.xml" media-type="application/xml"/><o:item id="section0" href="section0.xml" media-type="application/xml"/></o:manifest>
  <o:spine><o:itemref idref="section0" linear="yes"/></o:spine>
</o:package>"#;
    archive(vec![
        entry(
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            opf.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/header.xml",
            HEADER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            SECTION_PATH,
            section.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ])
}

fn entry(
    name: &str,
    bytes: &[u8],
    method: CompressionMethod,
) -> (String, Vec<u8>, CompressionMethod) {
    (name.to_owned(), bytes.to_vec(), method)
}

fn archive(
    entries: Vec<(String, Vec<u8>, CompressionMethod)>,
) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes, method) in entries {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(method),
        )?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn open_graph(bytes: Vec<u8>) -> Result<(TestReader, PackageGraph), Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok((reader, graph))
}

fn assert_code<T>(result: Result<T, EquationHwpxError>, expected: &str) {
    let Err(error) = result else {
        panic!("operation unexpectedly succeeded")
    };
    assert_eq!(error.code(), expected, "{error:?}");
}
