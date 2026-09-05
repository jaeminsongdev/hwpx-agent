use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Read as _, Write as _};
use std::path::{Path, PathBuf};

use hwpx_package::{
    BoundedZipReader, ColumnDefinition, ColumnLayout, ColumnLineType, ColumnLineWidth,
    ColumnSeparator, ColumnSize, ColumnSizing, ColumnType, Hancom2020Vs0Builder, PackageGraph,
    PackageGraphLimits, PackageLimits, PageDimensions, PageGutterType, PageMargins,
    PageOrientation, PageSetup, PageSetupLimits, PageSetupLowerer, PageSetupReader,
    SectionColumnLimits, SectionColumnLowerer, SectionColumnReader, TextFlowLimits, TextFlowReader,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipArchive, ZipWriter};

const SECTION_ONE_TEXT: &str = "P05-07-SECTION-ONE";
const SECTION_TWO_TEXT: &str = "P05-07-SECTION-TWO";
const MAX_TARGET_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or("usage: p05_07_section_columns_target_fixture <build|inspect> <path.hwpx>")?;
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p05_07_section_columns_target_fixture <build|inspect> <path.hwpx>")?;
    if arguments.next().is_some() {
        return Err(
            "usage: p05_07_section_columns_target_fixture <build|inspect> <path.hwpx>".into(),
        );
    }
    match mode.as_str() {
        "build" => build(&path),
        "inspect" => inspect_path(&path),
        _ => Err("mode must be build or inspect".into()),
    }
}

fn build(path: &Path) -> Result<(), Box<dyn Error>> {
    let source = Hancom2020Vs0Builder::build(SECTION_ONE_TEXT)?;
    let source_bytes = source.with_verified_bytes(ToOwned::to_owned)?;
    let bytes = rebuild_with_two_sections(&source_bytes)?;
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
        "schema=hwpx-agent.p05-07-section-columns-target-fixture/v1 mode={mode} state=pass size={} sha256={} sections={} breaks={} spans={:?} body_width={} text_sha256={}",
        bytes.len(),
        hex::encode(Sha256::digest(bytes)),
        inspection.section_count,
        inspection.break_count,
        inspection.span_counts,
        inspection.body_width,
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
    section_count: usize,
    break_count: usize,
    span_counts: Vec<usize>,
    body_width: u32,
    text_sha256: String,
}

fn inspect_bytes(bytes: &[u8]) -> Result<Inspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let header = read_part(&mut reader, "Contents/header.xml")?;
    let section0 = read_part(&mut reader, "Contents/section0.xml")?;
    let section1 = read_part(&mut reader, "Contents/section1.xml")?;
    let package_document = read_part(&mut reader, "Contents/content.hpf")?;
    verify_linear_spine(&package_document)?;
    let setup = expected_page_setup()?;
    let metrics = setup.metrics(PageSetupLimits::default())?;
    for section in [&section0, &section1] {
        if PageSetupReader::read(section, PageSetupLimits::default())? != setup {
            return Err("target section page-setup semantic readback mismatch".into());
        }
    }
    let inputs = [
        (section0.as_slice(), metrics.body_width),
        (section1.as_slice(), metrics.body_width),
    ];
    let sequence = SectionColumnReader::read_sequence_with_header(
        &header,
        &inputs,
        SectionColumnLimits::default(),
    )?;
    if sequence.sections[0].spans != vec![section_one_columns()]
        || sequence.sections[1].spans != vec![section_two_columns()]
    {
        return Err("target section/column semantic readback mismatch".into());
    }
    let text0 = visible_text(&section0)?;
    let text1 = visible_text(&section1)?;
    if text0 != SECTION_ONE_TEXT || text1 != SECTION_TWO_TEXT {
        return Err("target multi-section text readback mismatch".into());
    }
    let canonical_text = format!("{text0}\n{text1}");
    let expected_spine = [
        "Contents/header.xml",
        "Contents/section0.xml",
        "Contents/section1.xml",
    ];
    let actual_spine: Vec<_> = graph
        .spine
        .iter()
        .map(hwpx_package::PackagePath::as_str)
        .collect();
    if actual_spine != expected_spine {
        return Err("target multi-section spine order mismatch".into());
    }
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph does not cover every entry".into());
    }
    Ok(Inspection {
        section_count: sequence.sections.len(),
        break_count: sequence.section_break_count(),
        span_counts: sequence
            .sections
            .iter()
            .map(|section| section.spans.len())
            .collect(),
        body_width: metrics.body_width,
        text_sha256: hex::encode(Sha256::digest(canonical_text.as_bytes())),
    })
}

fn verify_linear_spine(package_document: &[u8]) -> Result<(), Box<dyn Error>> {
    let source = std::str::from_utf8(package_document)?;
    let section0 = r#"<opf:itemref idref="section0" linear="yes"/>"#;
    let section1 = r#"<opf:itemref idref="section1" linear="yes"/>"#;
    if source.matches(section0).count() != 1
        || source.matches(section1).count() != 1
        || source.contains(r#"<opf:itemref idref="section0" linear="no"/>"#)
        || source.contains(r#"<opf:itemref idref="section1" linear="no"/>"#)
    {
        return Err("target multi-section spine is not linear".into());
    }

    Ok(())
}

fn visible_text(section: &[u8]) -> Result<String, Box<dyn Error>> {
    let paragraph = extract_exact_element(section, b"<hp:p ", b"</hp:p>")?;
    let paragraph = std::str::from_utf8(paragraph)?;
    let paragraph = replace_exact_once(
        paragraph,
        "<hp:p ",
        "<hp:p xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" ",
    )?;
    let flow = TextFlowReader::read(paragraph.as_bytes(), TextFlowLimits::default())
        .map_err(|error| std::io::Error::other(format!("text_flow:{error:?}")))?;
    Ok(flow.visible_text_nfc()?)
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

fn rebuild_with_two_sections(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = ZipArchive::new(Cursor::new(source))?;
    let mut parts = Vec::with_capacity(archive.len() + 1);
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        let path = entry.name().to_owned();
        let method = entry.compression();
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        match path.as_str() {
            "Contents/header.xml" => {
                bytes = SectionColumnLowerer::replace_header_section_count(
                    &bytes,
                    1,
                    2,
                    SectionColumnLimits::default(),
                )?
                .0;
            }
            "Contents/section0.xml" => {
                let base = PageSetupLowerer::replace_in_section(
                    &bytes,
                    &expected_page_setup()?,
                    PageSetupLimits::default(),
                )?
                .0;
                let section0 = SectionColumnLowerer::replace_in_section(
                    &base,
                    0,
                    &section_one_columns(),
                    expected_body_width()?,
                    SectionColumnLimits::default(),
                )?
                .0;
                let section1 = SectionColumnLowerer::replace_in_section(
                    &base,
                    0,
                    &section_two_columns(),
                    expected_body_width()?,
                    SectionColumnLimits::default(),
                )?
                .0;
                let section1 = replace_exact_once_bytes(
                    &section1,
                    SECTION_ONE_TEXT.as_bytes(),
                    SECTION_TWO_TEXT.as_bytes(),
                )?;
                let section1 =
                    replace_exact_once_bytes(&section1, b"<hp:p id=\"1\"", b"<hp:p id=\"2\"")?;
                parts.push((path, method, section0));
                parts.push(("Contents/section1.xml".to_owned(), method, section1));
                continue;
            }
            "Contents/content.hpf" => bytes = add_section_to_package_document(&bytes)?,
            "META-INF/container.rdf" => bytes = add_section_to_rdf(&bytes)?,
            "Preview/PrvText.txt" => {
                bytes = format!("HWPX Agent P05-07\n{SECTION_ONE_TEXT}\n{SECTION_TWO_TEXT}\n")
                    .into_bytes();
            }
            _ => {}
        }
        parts.push((path, method, bytes));
    }
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

fn add_section_to_package_document(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(bytes)?;
    let source = replace_exact_once(
        source,
        r#"<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>"#,
        concat!(
            r#"<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>"#,
            r#"<opf:item id="section1" href="Contents/section1.xml" media-type="application/xml"/>"#,
        ),
    )?;
    Ok(replace_exact_once(
        &source,
        r#"<opf:itemref idref="section0" linear="no"/>"#,
        concat!(
            r#"<opf:itemref idref="section0" linear="yes"/>"#,
            r#"<opf:itemref idref="section1" linear="yes"/>"#,
        ),
    )?
    .into_bytes())
}

fn add_section_to_rdf(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
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
            r#"rdf:resource="Contents/section1.xml"/></rdf:Description>"#,
            r#"<rdf:Description rdf:about="Contents/section1.xml"><rdf:type "#,
            r#"rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#SectionFile"/>"#,
            r#"</rdf:Description>"#,
        ),
        anchor
    );
    Ok(replace_exact_once(source, anchor, &replacement)?.into_bytes())
}

fn expected_page_setup() -> Result<PageSetup, Box<dyn Error>> {
    Ok(PageSetup {
        orientation: PageOrientation::Landscape,
        dimensions: PageDimensions::from_milli_mm(230_000, 310_000)?,
        gutter_type: PageGutterType::TopBottom,
        margins: PageMargins {
            header: 2_835,
            footer: 2_268,
            gutter: 1_417,
            left: 4_252,
            right: 3_402,
            top: 5_669,
            bottom: 4_252,
        },
    })
}

fn expected_body_width() -> Result<u32, Box<dyn Error>> {
    Ok(expected_page_setup()?
        .metrics(PageSetupLimits::default())?
        .body_width)
}

fn section_one_columns() -> ColumnDefinition {
    ColumnDefinition {
        control_id: "p05-07-equal".to_owned(),
        column_type: ColumnType::BalancedNewspaper,
        layout: ColumnLayout::Left,
        sizing: ColumnSizing::Equal {
            count: 2,
            gap: 1_700,
        },
        separator: Some(ColumnSeparator {
            line_type: ColumnLineType::Solid,
            width: ColumnLineWidth::Mm0_12,
            color: 0x0033_6699,
        }),
    }
}

fn section_two_columns() -> ColumnDefinition {
    ColumnDefinition {
        control_id: "p05-07-custom".to_owned(),
        column_type: ColumnType::Parallel,
        layout: ColumnLayout::Right,
        sizing: ColumnSizing::Custom(vec![
            ColumnSize {
                width: 30_000,
                gap: 1_700,
            },
            ColumnSize {
                width: 48_520,
                gap: 0,
            },
        ]),
        separator: Some(ColumnSeparator {
            line_type: ColumnLineType::DashDot,
            width: ColumnLineWidth::Mm0_25,
            color: 0x0066_3300,
        }),
    }
}

fn replace_exact_once(source: &str, from: &str, to: &str) -> Result<String, Box<dyn Error>> {
    if source.matches(from).count() != 1 {
        return Err("fixture mutation anchor is not exact".into());
    }
    Ok(source.replacen(from, to, 1))
}

fn replace_exact_once_bytes(
    source: &[u8],
    from: &[u8],
    to: &[u8],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let indexes: Vec<_> = source
        .windows(from.len())
        .enumerate()
        .filter_map(|(index, window)| (window == from).then_some(index))
        .collect();
    if indexes.len() != 1 {
        return Err("fixture byte mutation anchor is not exact".into());
    }
    let index = indexes[0];
    let output_len = source
        .len()
        .checked_sub(from.len())
        .and_then(|value| value.checked_add(to.len()))
        .ok_or("fixture byte mutation size overflow")?;
    let mut output = Vec::with_capacity(output_len);
    output.extend_from_slice(&source[..index]);
    output.extend_from_slice(to);
    output.extend_from_slice(&source[index + from.len()..]);
    Ok(output)
}

fn extract_exact_element<'a>(
    source: &'a [u8],
    start: &[u8],
    end: &[u8],
) -> Result<&'a [u8], Box<dyn Error>> {
    let start_index = source
        .windows(start.len())
        .position(|window| window == start)
        .ok_or("fixture element start is missing")?;
    if source[start_index + start.len()..]
        .windows(start.len())
        .any(|window| window == start)
    {
        return Err("fixture element start is not unique".into());
    }
    let relative_end = source[start_index..]
        .windows(end.len())
        .position(|window| window == end)
        .ok_or("fixture element end is missing")?;
    let end_index = start_index + relative_end + end.len();
    Ok(&source[start_index..end_index])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generated_header_declares_both_spine_sections() -> Result<(), Box<dyn Error>> {
        let source = Hancom2020Vs0Builder::build(SECTION_ONE_TEXT)?;
        let bytes = source.with_verified_bytes(rebuild_with_two_sections)??;
        let mut reader =
            BoundedZipReader::open(Cursor::new(bytes.as_slice()), PackageLimits::default())?;
        let header = read_part(&mut reader, "Contents/header.xml")?;
        let document = hwpx_package::PreservingXmlDocument::parse(&header)?;
        let root = &document.elements()[document.root_element()];
        assert_eq!(
            root.name().namespace(),
            Some("http://www.hancom.co.kr/hwpml/2011/head")
        );
        assert_eq!(root.name().local_name(), "head");
        let count = root
            .attributes()
            .iter()
            .find(|attribute| {
                attribute.name().namespace().is_none() && attribute.name().local_name() == "secCnt"
            })
            .ok_or("header section count missing")?;
        assert_eq!(
            std::str::from_utf8(&header[count.value_span().start()..count.value_span().end()])?,
            "2"
        );
        assert_eq!(inspect_bytes(&bytes)?.section_count, 2);
        Ok(())
    }

    #[test]
    fn fixture_inspector_rejects_a_stale_header_even_with_valid_spine() -> Result<(), Box<dyn Error>>
    {
        let source = Hancom2020Vs0Builder::build(SECTION_ONE_TEXT)?;
        let valid = source.with_verified_bytes(rebuild_with_two_sections)??;
        let mut archive = ZipArchive::new(Cursor::new(&valid))?;
        let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
        for index in 0..archive.len() {
            let mut entry = archive.by_index(index)?;
            let mut bytes = Vec::new();
            entry.read_to_end(&mut bytes)?;
            if entry.name() == "Contents/header.xml" {
                bytes = SectionColumnLowerer::replace_header_section_count(
                    &bytes,
                    2,
                    1,
                    SectionColumnLimits::default(),
                )?
                .0;
            }
            writer.start_file(
                entry.name(),
                SimpleFileOptions::default().compression_method(entry.compression()),
            )?;
            writer.write_all(&bytes)?;
        }
        let stale = writer.finish()?.into_inner();
        let failure = inspect_bytes(&stale)
            .err()
            .ok_or("stale header unexpectedly qualified")?;
        assert_eq!(
            failure.downcast_ref::<hwpx_package::SectionColumnError>(),
            Some(&hwpx_package::SectionColumnError::SectionCountMismatch)
        );
        Ok(())
    }

    #[test]
    fn fixture_build_is_deterministic_and_never_overwrites() -> Result<(), Box<dyn Error>> {
        let directory = tempfile::tempdir()?;
        let first = directory.path().join("first.hwpx");
        let second = directory.path().join("second.hwpx");
        build(&first)?;
        build(&second)?;
        let original = fs::read(&first)?;
        assert_eq!(original, fs::read(&second)?);
        assert!(build(&first).is_err());
        assert_eq!(original, fs::read(&first)?);
        Ok(())
    }

    #[test]
    fn exact_two_section_linear_spine_is_accepted() {
        let package_document = concat!(
            r#"<opf:spine>"#,
            r#"<opf:itemref idref="section0" linear="yes"/>"#,
            r#"<opf:itemref idref="section1" linear="yes"/>"#,
            r#"</opf:spine>"#,
        );
        verify_linear_spine(package_document.as_bytes()).expect("linear spine must pass");
    }

    #[test]
    fn non_linear_or_duplicate_section_spine_is_rejected() {
        let non_linear = concat!(
            r#"<opf:itemref idref="section0" linear="yes"/>"#,
            r#"<opf:itemref idref="section1" linear="no"/>"#,
        );
        assert!(verify_linear_spine(non_linear.as_bytes()).is_err());

        let duplicate = concat!(
            r#"<opf:itemref idref="section0" linear="yes"/>"#,
            r#"<opf:itemref idref="section0" linear="yes"/>"#,
            r#"<opf:itemref idref="section1" linear="yes"/>"#,
        );
        assert!(verify_linear_spine(duplicate.as_bytes()).is_err());
    }

    #[test]
    fn bounded_fixture_reader_rejects_empty_and_oversized_files() -> Result<(), Box<dyn Error>> {
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
    fn target_definitions_partition_the_custom_page_body() -> Result<(), Box<dyn Error>> {
        let body_width = expected_body_width()?;
        assert_eq!(body_width, 80_220);
        let first = section_one_columns().metrics(body_width, SectionColumnLimits::default())?;
        assert_eq!(first.column_count, 2);
        assert_eq!(first.total_gap, 1_700);
        let second = section_two_columns().metrics(body_width, SectionColumnLimits::default())?;
        assert_eq!(second.column_count, 2);
        assert_eq!(second.total_gap, 1_700);
        assert_eq!(second.total_column_width, 78_520);
        Ok(())
    }
}
