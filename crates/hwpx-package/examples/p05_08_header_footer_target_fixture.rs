use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Read as _, Write as _};
use std::path::{Path, PathBuf};

use hwpx_package::{
    BoundedZipReader, FirstPageDisplay, FirstPageVisibility, HEADER_FOOTER_PROFILE_ID,
    Hancom2020Vs0Builder, HeaderFooterBody, HeaderFooterDefinition, HeaderFooterInline,
    HeaderFooterKind, HeaderFooterLimits, HeaderFooterLowerer, HeaderFooterParagraph,
    HeaderFooterReader, HeaderFooterRun, MasterPageDefinition, MasterPageVariant, NumberFormat,
    PackageGraph, PackageGraphLimits, PackageLimits, PageField, PageFieldKind, PageNumberPlacement,
    PageNumberPosition, PageNumberRestart, PageVariant, ParagraphChild, PreservingXmlDocument,
    SectionPagePolicy, TextAtom, TextFlowLimits, TextFlowReader, TextRunItem,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipArchive, ZipWriter};

const PAGE_TEXTS: [&str; 4] = [
    "P05-08-PAGE-ONE-FIRST-HIDDEN",
    "P05-08-PAGE-TWO-EVEN",
    "P05-08-PAGE-THREE-ODD",
    "P05-08-PAGE-FOUR-EVEN",
];
const MASTER_PAGE_PATH: &str = "Contents/masterpage0.xml";
const MASTER_PAGE_ID: &str = "p05-08-master";
const MAX_TARGET_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or("usage: p05_08_header_footer_target_fixture <build|inspect> <path.hwpx>")?;
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p05_08_header_footer_target_fixture <build|inspect> <path.hwpx>")?;
    if arguments.next().is_some() {
        return Err(
            "usage: p05_08_header_footer_target_fixture <build|inspect> <path.hwpx>".into(),
        );
    }
    match mode.as_str() {
        "build" => build(&path),
        "inspect" => inspect_path(&path),
        _ => Err("mode must be build or inspect".into()),
    }
}

fn build(path: &Path) -> Result<(), Box<dyn Error>> {
    let source = Hancom2020Vs0Builder::build(PAGE_TEXTS[0])?;
    let source_bytes = source.with_verified_bytes(ToOwned::to_owned)?;
    let bytes = rebuild_target(&source_bytes)?;
    let inspection = inspect_bytes(&bytes)?;
    let mut output = OpenOptions::new().write(true).create_new(true).open(path)?;
    output.write_all(&bytes)?;
    output.sync_all()?;
    print_result("build", &bytes, &inspection);
    Ok(())
}

fn inspect_path(path: &Path) -> Result<(), Box<dyn Error>> {
    let bytes = read_bounded_fixture(path)?;
    let inspection = inspect_bytes(&bytes)?;
    print_result("inspect", &bytes, &inspection);
    Ok(())
}

fn print_result(mode: &str, bytes: &[u8], inspection: &Inspection) {
    println!(
        concat!(
            "schema=hwpx-agent.p05-08-header-footer-target-fixture/v1 ",
            "mode={} state=pass size={} sha256={} profile={} pages={} ",
            "definitions={} page_fields={} masters={} first_hidden={} text_sha256={}"
        ),
        mode,
        bytes.len(),
        hex::encode(Sha256::digest(bytes)),
        HEADER_FOOTER_PROFILE_ID,
        inspection.page_count,
        inspection.definition_count,
        inspection.page_field_count,
        inspection.master_page_count,
        inspection.first_page_hidden,
        inspection.text_sha256,
    );
}

fn read_bounded_fixture(path: &Path) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_TARGET_FIXTURE_BYTES
    {
        return Err("fixture input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if u64::try_from(bytes.len())? != metadata.len() {
        return Err("fixture input changed while being read".into());
    }
    Ok(bytes)
}

struct Inspection {
    page_count: usize,
    definition_count: usize,
    page_field_count: usize,
    master_page_count: usize,
    first_page_hidden: bool,
    text_sha256: String,
}

struct MainParagraphReadback {
    page_count: usize,
    texts: Vec<String>,
    page_breaks: Vec<bool>,
}

fn inspect_bytes(bytes: &[u8]) -> Result<Inspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph does not cover every entry".into());
    }
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let master_bytes = read_part(&mut reader, MASTER_PAGE_PATH)?;
    let actual_policy = HeaderFooterReader::read_section(&section, HeaderFooterLimits::default())?;
    let expected_policy = target_policy();
    if actual_policy != expected_policy {
        return Err("target section header/footer semantic readback mismatch".into());
    }
    let actual_master =
        HeaderFooterReader::read_master_page(&master_bytes, HeaderFooterLimits::default())?;
    let expected_master = target_master_page();
    if actual_master != expected_master {
        return Err("target master-page semantic readback mismatch".into());
    }
    HeaderFooterReader::validate_master_pages(
        &actual_policy,
        std::slice::from_ref(&actual_master),
        HeaderFooterLimits::default(),
    )?;
    let main = read_main_paragraphs(&section)?;
    if main.texts != PAGE_TEXTS || main.page_breaks != [false, true, true, true] {
        return Err("target main page text or forced break sequence mismatch".into());
    }
    let canonical_text = main.texts.join("\n");
    let page_field_count = actual_policy
        .definitions
        .iter()
        .flat_map(|definition| &definition.body.paragraphs)
        .flat_map(|paragraph| &paragraph.runs)
        .flat_map(|run| &run.inlines)
        .filter(|inline| matches!(inline, HeaderFooterInline::PageField(_)))
        .count();
    let first_page_hidden = actual_policy.first_page.header.is_hidden()
        && actual_policy.first_page.footer.is_hidden()
        && actual_policy.first_page.master_page.is_hidden()
        && actual_policy.first_page.page_number.is_hidden();
    if !first_page_hidden || page_field_count != 8 {
        return Err("target first-page or page-field coverage mismatch".into());
    }
    Ok(Inspection {
        page_count: main.page_count,
        definition_count: actual_policy.definitions.len(),
        page_field_count,
        master_page_count: actual_policy.master_page_references.len(),
        first_page_hidden,
        text_sha256: hex::encode(Sha256::digest(canonical_text.as_bytes())),
    })
}

fn read_part(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("required fixture part is missing")?;
    Ok(reader.read_entry(index)?)
}

fn read_main_paragraphs(section: &[u8]) -> Result<MainParagraphReadback, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    let root = document.root_element();
    let mut texts = Vec::new();
    let mut page_breaks = Vec::new();
    for element in document.elements() {
        if element.name().namespace() != Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
            || element.name().local_name() != "p"
            || element.parent() != Some(root)
        {
            continue;
        }
        let span = element.outer_span().ok_or("paragraph outer span missing")?;
        let paragraph = std::str::from_utf8(&section[span.start()..span.end()])?;
        let paragraph = paragraph
            .strip_prefix("<hp:p ")
            .map(|remainder| {
                format!(
                    "<hp:p xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" {remainder}"
                )
            })
            .ok_or("top-level paragraph does not start with the expected qualified name")?;
        let flow = TextFlowReader::read(paragraph.as_bytes(), TextFlowLimits::default())?;
        let mut visible = String::new();
        for child in &flow.children {
            let ParagraphChild::Run(run) = child else {
                continue;
            };
            for item in &run.items {
                let TextRunItem::Text(span) = item else {
                    continue;
                };
                for atom in &span.atoms {
                    if let TextAtom::Text(text) = atom {
                        visible.push_str(text);
                    }
                }
            }
        }
        if visible.starts_with("P05-08-PAGE-") {
            texts.push(visible);
            page_breaks.push(flow.paragraph.page_break);
        }
    }
    Ok(MainParagraphReadback {
        page_count: texts.len(),
        texts,
        page_breaks,
    })
}

fn rebuild_target(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = ZipArchive::new(Cursor::new(source))?;
    let master_page = HeaderFooterLowerer::lower_master_page(
        &target_master_page(),
        HeaderFooterLimits::default(),
    )?
    .0;
    let mut parts = Vec::with_capacity(archive.len() + 1);
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        let path = entry.name().to_owned();
        let method = entry.compression();
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        match path.as_str() {
            "Contents/section0.xml" => bytes = build_section(&bytes)?,
            "Contents/content.hpf" => bytes = add_master_to_package_document(&bytes)?,
            "META-INF/container.rdf" => bytes = add_master_to_rdf(&bytes)?,
            "Preview/PrvText.txt" => {
                bytes = format!("HWPX Agent P05-08\n{}\n", PAGE_TEXTS.join("\n")).into_bytes();
            }
            _ => {}
        }
        parts.push((path, method, bytes));
    }
    parts.push((
        MASTER_PAGE_PATH.to_owned(),
        CompressionMethod::Deflated,
        master_page,
    ));
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, method, bytes) in parts {
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(6));
        }
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn build_section(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut section = std::str::from_utf8(source)?.to_owned();
    section = replace_exact_once(&section, "masterPageCnt=\"0\"", "masterPageCnt=\"1\"")?;
    section = replace_exact_once(
        &section,
        r#"<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>"#,
        r#"<hp:startNum pageStartsOn="BOTH" page="1" pic="1" tbl="1" equation="1"/>"#,
    )?;
    for attribute in [
        "hideFirstHeader",
        "hideFirstFooter",
        "hideFirstMasterPage",
        "hideFirstPageNum",
    ] {
        section = replace_exact_once(
            &section,
            &format!("{attribute}=\"0\""),
            &format!("{attribute}=\"1\""),
        )?;
    }
    section = replace_exact_once(
        &section,
        "</hp:secPr>",
        &format!("<hp:masterPage idRef=\"{MASTER_PAGE_ID}\"/></hp:secPr>"),
    )?;
    let controls = HeaderFooterLowerer::lower_section_controls(
        &target_policy(),
        HeaderFooterLimits::default(),
    )?;
    section = replace_exact_once(
        &section,
        "</hp:secPr><hp:ctrl><hp:colPr",
        &format!(
            "</hp:secPr>{}<hp:ctrl><hp:colPr",
            std::str::from_utf8(&controls)?
        ),
    )?;
    let mut extra_pages = String::new();
    for (index, text) in PAGE_TEXTS.iter().enumerate().skip(1) {
        extra_pages.push_str(&main_paragraph(index + 1, text));
    }
    replace_exact_once(&section, "</hs:sec>", &format!("{extra_pages}</hs:sec>"))
        .map(String::into_bytes)
}

fn main_paragraph(id: usize, text: &str) -> String {
    format!(
        concat!(
            r#"<hp:p id="{}" paraPrIDRef="0" styleIDRef="0" pageBreak="1" "#,
            r#"columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t>{}</hp:t>"#,
            r#"</hp:run><hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" "#,
            r#"textheight="1000" baseline="850" spacing="600" horzpos="0" horzsize="42520" "#,
            r#"flags="393216"/></hp:linesegarray></hp:p>"#,
        ),
        id, text
    )
}

fn add_master_to_package_document(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(bytes)?;
    Ok(replace_exact_once(
        source,
        r#"<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>"#,
        concat!(
            r#"<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>"#,
            r#"<opf:item id="masterpage0" href="Contents/masterpage0.xml" media-type="application/xml"/>"#,
        ),
    )?
    .into_bytes())
}

fn add_master_to_rdf(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(bytes)?;
    let anchor = concat!(
        r#"<rdf:Description rdf:about="Contents/section0.xml"><rdf:type "#,
        r#"rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#SectionFile"/>"#,
        r#"</rdf:Description>"#,
    );
    let replacement = format!(
        concat!(
            "{}",
            r#"<rdf:Description rdf:about=""><ns0:hasPart "#,
            r#"xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" "#,
            r#"rdf:resource="Contents/masterpage0.xml"/></rdf:Description>"#,
            r#"<rdf:Description rdf:about="Contents/masterpage0.xml"><rdf:type "#,
            r#"rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#MasterPageFile"/>"#,
            r#"</rdf:Description>"#,
        ),
        anchor
    );
    Ok(replace_exact_once(source, anchor, &replacement)?.into_bytes())
}

fn target_policy() -> SectionPagePolicy {
    SectionPagePolicy {
        restart: PageNumberRestart {
            page_starts_on: PageVariant::Both,
            page: 1,
            picture: 1,
            table: 1,
            equation: 1,
        },
        first_page: FirstPageVisibility {
            header: FirstPageDisplay::Hide,
            footer: FirstPageDisplay::Hide,
            master_page: FirstPageDisplay::Hide,
            page_number: FirstPageDisplay::Hide,
        },
        page_starts_on: Some(PageVariant::Both),
        page_number: Some(PageNumberPlacement {
            position: PageNumberPosition::BottomCenter,
            format: NumberFormat::Digit,
            side_character: "-".to_owned(),
        }),
        definitions: vec![
            header_footer_definition(HeaderFooterKind::Header, PageVariant::Even, 100),
            header_footer_definition(HeaderFooterKind::Header, PageVariant::Odd, 101),
            header_footer_definition(HeaderFooterKind::Footer, PageVariant::Even, 200),
            header_footer_definition(HeaderFooterKind::Footer, PageVariant::Odd, 201),
        ],
        master_page_references: vec![MASTER_PAGE_ID.to_owned()],
        declared_master_page_count: 1,
    }
}

fn header_footer_definition(
    kind: HeaderFooterKind,
    applies_to: PageVariant,
    id: u32,
) -> HeaderFooterDefinition {
    let kind_label = match kind {
        HeaderFooterKind::Header => "HEADER",
        HeaderFooterKind::Footer => "FOOTER",
    };
    let variant_label = match applies_to {
        PageVariant::Even => "EVEN",
        PageVariant::Odd => "ODD",
        PageVariant::Both => "BOTH",
    };
    let inlines = vec![
        HeaderFooterInline::Text {
            value: format!("P05-08-{variant_label}-{kind_label}-"),
            character_style_id_ref: Some(0),
        },
        HeaderFooterInline::PageField(page_field(PageFieldKind::Page)),
        HeaderFooterInline::Text {
            value: "-OF-".to_owned(),
            character_style_id_ref: Some(0),
        },
        HeaderFooterInline::PageField(page_field(PageFieldKind::TotalPage)),
    ];
    HeaderFooterDefinition {
        id,
        kind,
        applies_to,
        body: typed_body(
            &format!("p05-08-body-{id}"),
            &format!("p05-08-paragraph-{id}"),
            inlines,
        ),
    }
}

fn page_field(kind: PageFieldKind) -> PageField {
    PageField {
        displayed_number: 1,
        kind,
        format: NumberFormat::Digit,
        user_character: String::new(),
        prefix: String::new(),
        suffix: String::new(),
        superscript: false,
    }
}

fn target_master_page() -> MasterPageDefinition {
    MasterPageDefinition {
        id: MASTER_PAGE_ID.to_owned(),
        applies_to: MasterPageVariant::Both,
        optional_page_number: None,
        duplicate_on_page: false,
        in_front: false,
        body: typed_body(
            "p05-08-master-body",
            "p05-08-master-paragraph",
            vec![HeaderFooterInline::Text {
                value: "P05-08-MASTER-PAGE".to_owned(),
                character_style_id_ref: Some(0),
            }],
        ),
    }
}

fn typed_body(id: &str, paragraph_id: &str, inlines: Vec<HeaderFooterInline>) -> HeaderFooterBody {
    let has_number_reference = inlines
        .iter()
        .any(|inline| matches!(inline, HeaderFooterInline::PageField(_)));
    HeaderFooterBody {
        id: id.to_owned(),
        text_direction: hwpx_package::HeaderFooterTextDirection::Horizontal,
        line_wrap: hwpx_package::HeaderFooterLineWrap::Break,
        vertical_alignment: hwpx_package::HeaderFooterVerticalAlignment::Center,
        link_list_id_ref: 0,
        link_list_next_id_ref: 0,
        text_width: 42_520,
        text_height: 2_000,
        has_text_reference: false,
        has_number_reference,
        paragraphs: vec![HeaderFooterParagraph {
            id: paragraph_id.to_owned(),
            paragraph_property_id_ref: 0,
            style_id_ref: 0,
            page_break: false,
            column_break: false,
            merged: false,
            runs: vec![HeaderFooterRun {
                character_style_id_ref: 0,
                inlines,
            }],
        }],
    }
}

fn replace_exact_once(source: &str, from: &str, to: &str) -> Result<String, Box<dyn Error>> {
    let matches = source.matches(from).count();
    if matches != 1 {
        return Err(format!(
            "fixture mutation anchor is not exact: matches={matches} anchor={from}"
        )
        .into());
    }
    Ok(source.replacen(from, to, 1))
}

#[cfg(test)]
mod tests {
    use super::*;

    type TestResult = Result<(), Box<dyn Error>>;

    #[test]
    fn bounded_fixture_reader_rejects_empty_and_oversized_files() -> TestResult {
        let directory = tempfile::tempdir()?;
        let empty = directory.path().join("empty.hwpx");
        fs::write(&empty, [])?;
        assert!(read_bounded_fixture(&empty).is_err());
        let oversized = directory.path().join("oversized.hwpx");
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&oversized)?;
        file.set_len(MAX_TARGET_FIXTURE_BYTES + 1)?;
        assert!(read_bounded_fixture(&oversized).is_err());
        Ok(())
    }

    #[test]
    fn target_policy_covers_even_odd_first_page_fields_and_master() -> TestResult {
        let policy = target_policy();
        assert_eq!(policy.definitions.len(), 4);
        assert!(policy.first_page.header.is_hidden());
        assert!(policy.first_page.footer.is_hidden());
        assert!(policy.first_page.page_number.is_hidden());
        assert_eq!(policy.master_page_references, [MASTER_PAGE_ID]);
        HeaderFooterReader::validate_master_pages(
            &policy,
            &[target_master_page()],
            HeaderFooterLimits::default(),
        )?;
        Ok(())
    }
}
