#![no_main]

use std::fmt::Write as _;
use std::io::{Cursor, Write as _};

use hwpx_package::{RoundTripLimits, RoundTripVerifier};
use libfuzzer_sys::fuzz_target;
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

const MAX_STRUCTURED_SEED_BYTES: usize = 4096;
const CONTAINER_NS: &str = "urn:oasis:names:tc:opendocument:xmlns:container";
const OPF_NS: &str = "http://www.idpf.org/2007/opf/";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

fuzz_target!(|data: &[u8]| {
    if data.len() > MAX_STRUCTURED_SEED_BYTES {
        return;
    }
    let Ok(archive) = build_valid_archive(data) else {
        return;
    };
    if let Err(error) = RoundTripVerifier::verify(Cursor::new(archive), RoundTripLimits::default())
    {
        panic!("structured valid package was rejected: {}", error.code());
    }
});

fn build_valid_archive(data: &[u8]) -> Result<Vec<u8>, zip::result::ZipError> {
    let selector = data.first().copied().unwrap_or_default();
    let marker = bounded_hex(data);
    let container = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="{CONTAINER_NS}" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
  <!--{marker}-->
</container>"#
    );
    let opf = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<o:package xmlns:o="{OPF_NS}" id="pkg" version="2.0">
  <o:manifest><o:item id="section0" href="section0.xml" media-type="application/xml"/></o:manifest>
  <o:spine><o:itemref idref="section0" linear="{}"/></o:spine>
  <!--{marker}-->
</o:package>"#,
        if selector & 1 == 0 { "yes" } else { "no" }
    );
    let section = format!(r#"<q:section xmlns:q="{PARAGRAPH_NS}"><!--{marker}--></q:section>"#);
    let entries = [
        ("META-INF/container.xml", container.into_bytes()),
        ("Contents/content.hpf", opf.into_bytes()),
        ("Contents/section0.xml", section.into_bytes()),
    ];
    let permutations = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ];

    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    writer.start_file(
        "mimetype",
        SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
    )?;
    writer.write_all(b"application/hwp+zip")?;
    writer.start_file(
        "version.xml",
        options(data.get(1).copied().unwrap_or_default()),
    )?;
    writer.write_all(b"<version/>")?;

    for (ordinal, entry_index) in permutations[usize::from(selector) % permutations.len()]
        .iter()
        .enumerate()
    {
        let (path, bytes) = &entries[*entry_index];
        writer.start_file(
            *path,
            options(data.get(ordinal + 2).copied().unwrap_or_default()),
        )?;
        writer.write_all(bytes)?;
    }
    writer.finish().map(Cursor::into_inner)
}

fn options(selector: u8) -> SimpleFileOptions {
    let method = if selector & 1 == 0 {
        CompressionMethod::Stored
    } else {
        CompressionMethod::Deflated
    };
    SimpleFileOptions::default()
        .compression_method(method)
        .compression_level((method == CompressionMethod::Deflated).then_some(6))
}

fn bounded_hex(data: &[u8]) -> String {
    let mut output = String::with_capacity(data.len().min(64) * 2 + 5);
    output.push_str("seed0");
    for byte in data.iter().take(64) {
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}
