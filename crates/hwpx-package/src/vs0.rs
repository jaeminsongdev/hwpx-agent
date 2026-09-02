use std::fmt;
use std::io::{Cursor, Write};

use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, System, ZipWriter};

use crate::{
    BoundedZipReader, GraphError, IdIndex, IdIndexLimits, IdRuleProfile, PackageGraph,
    PackageGraphLimits, PackageLimits,
};

pub const HANCOM_2020_VS0_MAX_TEXT_BYTES: usize = 4 * 1024;
const MAX_ARTIFACT_BYTES: usize = 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const HEADER_XML: &str = include_str!("hancom_2020_minimal_header.xml");
const MIMETYPE: &str = "application/hwp+zip";
const VERSION_XML: &str = concat!(
    r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>"#,
    r#"<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" "#,
    r#"tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="0" "#,
    r#"buildNumber="1" os="1" xmlVersion="1.4" application="Hancom Office Hangul" "#,
    r#"appVersion="11, 0, 0, 9136 WIN32LEWindows_10"/>"#,
);
const CONTAINER_XML: &str = concat!(
    r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>"#,
    r#"<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" "#,
    r#"xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf">"#,
    r#"<ocf:rootfiles><ocf:rootfile full-path="Contents/content.hpf" "#,
    r#"media-type="application/hwpml-package+xml"/>"#,
    r#"<ocf:rootfile full-path="Preview/PrvText.txt" media-type="text/plain"/>"#,
    r#"<ocf:rootfile full-path="META-INF/container.rdf" "#,
    r#"media-type="application/rdf+xml"/></ocf:rootfiles></ocf:container>"#,
);
const CONTENT_HPF: &str = concat!(
    r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>"#,
    r#"<opf:package xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" "#,
    r#"xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" "#,
    r#"xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" "#,
    r#"xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" "#,
    r#"xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" "#,
    r#"xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" "#,
    r#"xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" "#,
    r#"xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" "#,
    r#"xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" "#,
    r#"xmlns:dc="http://purl.org/dc/elements/1.1/" "#,
    r#"xmlns:opf="http://www.idpf.org/2007/opf/" "#,
    r#"xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" "#,
    r#"xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" "#,
    r#"xmlns:epub="http://www.idpf.org/2007/ops" "#,
    r#"xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" version="" "#,
    r#"unique-identifier="" id=""><opf:metadata><opf:title>HWPX Agent VS-0</opf:title>"#,
    r#"<opf:language>ko</opf:language></opf:metadata><opf:manifest>"#,
    r#"<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>"#,
    r#"<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>"#,
    r#"<opf:item id="settings" href="settings.xml" media-type="application/xml"/>"#,
    r#"</opf:manifest><opf:spine><opf:itemref idref="header" linear="no"/>"#,
    r#"<opf:itemref idref="section0" linear="no"/></opf:spine></opf:package>"#,
);
const SETTINGS_XML: &str = concat!(
    r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>"#,
    r#"<ha:HWPApplicationSetting xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" "#,
    r#"xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">"#,
    r#"<ha:CaretPosition listIDRef="0" paraIDRef="1" pos="0"/>"#,
    r#"</ha:HWPApplicationSetting>"#,
);
const CONTAINER_RDF: &str = concat!(
    r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>"#,
    r#"<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">"#,
    r#"<rdf:Description rdf:about=""><ns0:hasPart "#,
    r#"xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" "#,
    r#"rdf:resource="Contents/header.xml"/></rdf:Description>"#,
    r#"<rdf:Description rdf:about="Contents/header.xml"><rdf:type "#,
    r#"rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#HeaderFile"/>"#,
    r#"</rdf:Description><rdf:Description rdf:about=""><ns0:hasPart "#,
    r#"xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" "#,
    r#"rdf:resource="Contents/section0.xml"/></rdf:Description>"#,
    r#"<rdf:Description rdf:about="Contents/section0.xml"><rdf:type "#,
    r#"rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#SectionFile"/>"#,
    r#"</rdf:Description><rdf:Description rdf:about=""><rdf:type "#,
    r#"rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#Document"/>"#,
    r#"</rdf:Description></rdf:RDF>"#,
);
const MANIFEST_XML: &str = concat!(
    r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>"#,
    r#"<odf:manifest xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>"#,
);
const TRANSPARENT_PNG_1X1: &[u8] = &[
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
    0x89, 0x00, 0x00, 0x00, 0x0d, 0x49, 0x44, 0x41, 0x54, 0x08, 0xd7, 0x63, 0xf8, 0xcf, 0xc0, 0xf0,
    0x1f, 0x00, 0x05, 0x00, 0x01, 0xff, 0x89, 0x99, 0x3d, 0x1d, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
    0x4e, 0x44, 0xae, 0x42, 0x60, 0x82,
];

/// One deterministic, graph-validated VS-0 HWPX. Raw bytes are only available to a verified
/// in-process consumer callback, so callers cannot accidentally publish an unchecked artifact.
pub struct Hancom2020Vs0Artifact {
    bytes: Box<[u8]>,
    sha256: [u8; 32],
    part_count: usize,
}

impl Hancom2020Vs0Artifact {
    #[must_use]
    pub const fn size_bytes(&self) -> usize {
        self.bytes.len()
    }

    #[must_use]
    pub const fn sha256(&self) -> [u8; 32] {
        self.sha256
    }

    #[must_use]
    pub const fn part_count(&self) -> usize {
        self.part_count
    }

    /// Rehashes and reopens the package through the P03 bounded graph trust chain.
    ///
    /// # Errors
    ///
    /// Returns a stable error if bytes, bounds or package closure no longer match.
    pub fn verify(&self) -> Result<(), Hancom2020Vs0Error> {
        if self.bytes.len() > MAX_ARTIFACT_BYTES
            || <[u8; 32]>::from(Sha256::digest(&self.bytes)) != self.sha256
        {
            return Err(Hancom2020Vs0Error::ArtifactMismatch);
        }
        let part_count = verify_package(&self.bytes)?;
        if part_count != self.part_count {
            return Err(Hancom2020Vs0Error::ArtifactMismatch);
        }
        Ok(())
    }

    /// Gives one callback temporary access to already reverified bytes.
    ///
    /// # Errors
    ///
    /// Does not invoke the callback when verification fails.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, Hancom2020Vs0Error> {
        self.verify()?;
        Ok(consume(&self.bytes))
    }
}

impl fmt::Debug for Hancom2020Vs0Artifact {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("Hancom2020Vs0Artifact")
            .field("size_bytes", &self.bytes.len())
            .field("sha256", &self.sha256)
            .field("part_count", &self.part_count)
            .finish()
    }
}

#[derive(Debug)]
pub struct Hancom2020Vs0Builder;

impl Hancom2020Vs0Builder {
    /// Builds one deterministic A4 portrait HWPX with one default-style paragraph.
    ///
    /// # Errors
    ///
    /// Rejects empty, multiline, control-bearing or oversized text and any package that does not
    /// reopen through the bounded P03 package graph.
    pub fn build(text: &str) -> Result<Hancom2020Vs0Artifact, Hancom2020Vs0Error> {
        validate_text(text)?;
        let section_xml = section_xml(&escape_xml_text(text));
        let preview_text = format!("HWPX Agent VS-0\r\n{text}");
        let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
        write_part(&mut writer, "mimetype", MIMETYPE, CompressionMethod::Stored)?;
        write_part(
            &mut writer,
            "version.xml",
            VERSION_XML,
            CompressionMethod::Stored,
        )?;
        write_part(
            &mut writer,
            "Contents/header.xml",
            HEADER_XML,
            CompressionMethod::Deflated,
        )?;
        write_part(
            &mut writer,
            "Contents/section0.xml",
            &section_xml,
            CompressionMethod::Deflated,
        )?;
        write_part(
            &mut writer,
            "Preview/PrvText.txt",
            &preview_text,
            CompressionMethod::Deflated,
        )?;
        write_part(
            &mut writer,
            "settings.xml",
            SETTINGS_XML,
            CompressionMethod::Deflated,
        )?;
        write_bytes_part(
            &mut writer,
            "Preview/PrvImage.png",
            TRANSPARENT_PNG_1X1,
            CompressionMethod::Stored,
        )?;
        write_part(
            &mut writer,
            "META-INF/container.rdf",
            CONTAINER_RDF,
            CompressionMethod::Deflated,
        )?;
        write_part(
            &mut writer,
            "Contents/content.hpf",
            CONTENT_HPF,
            CompressionMethod::Deflated,
        )?;
        write_part(
            &mut writer,
            "META-INF/container.xml",
            CONTAINER_XML,
            CompressionMethod::Deflated,
        )?;
        write_part(
            &mut writer,
            "META-INF/manifest.xml",
            MANIFEST_XML,
            CompressionMethod::Deflated,
        )?;
        let cursor = writer
            .finish()
            .map_err(|_| Hancom2020Vs0Error::ZipConstruction)?;
        let bytes = cursor.into_inner();
        if bytes.is_empty() || bytes.len() > MAX_ARTIFACT_BYTES {
            return Err(Hancom2020Vs0Error::OutputLimitExceeded);
        }
        let part_count = verify_package(&bytes)?;
        let sha256 = Sha256::digest(&bytes).into();
        Ok(Hancom2020Vs0Artifact {
            bytes: bytes.into_boxed_slice(),
            sha256,
            part_count,
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum Hancom2020Vs0Error {
    #[error("VS-0 paragraph text is invalid")]
    InvalidText,
    #[error("VS-0 output exceeds its finite limit")]
    OutputLimitExceeded,
    #[error("VS-0 ZIP construction failed")]
    ZipConstruction,
    #[error("VS-0 package validation failed")]
    PackageValidation,
    #[error("VS-0 artifact identity mismatch")]
    ArtifactMismatch,
}

impl Hancom2020Vs0Error {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidText => "hancom_2020_vs0_invalid_text",
            Self::OutputLimitExceeded => "hancom_2020_vs0_output_limit_exceeded",
            Self::ZipConstruction => "hancom_2020_vs0_zip_construction",
            Self::PackageValidation => "hancom_2020_vs0_package_validation",
            Self::ArtifactMismatch => "hancom_2020_vs0_artifact_mismatch",
        }
    }
}

fn validate_text(text: &str) -> Result<(), Hancom2020Vs0Error> {
    if text.is_empty()
        || text.len() > HANCOM_2020_VS0_MAX_TEXT_BYTES
        || text.chars().any(|character| {
            character.is_control() || matches!(character as u32 & 0xffff, 0xfffe | 0xffff)
        })
    {
        return Err(Hancom2020Vs0Error::InvalidText);
    }
    Ok(())
}

fn escape_xml_text(text: &str) -> String {
    let mut escaped = String::with_capacity(text.len());
    for character in text.chars() {
        match character {
            '&' => escaped.push_str("&amp;"),
            '<' => escaped.push_str("&lt;"),
            '>' => escaped.push_str("&gt;"),
            '"' => escaped.push_str("&quot;"),
            '\'' => escaped.push_str("&apos;"),
            _ => escaped.push(character),
        }
    }
    escaped
}

fn section_xml(escaped_text: &str) -> String {
    format!(
        concat!(
            r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>"#,
            r#"<hs:sec xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" "#,
            r#"xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" "#,
            r#"xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" "#,
            r#"xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" "#,
            r#"xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" "#,
            r#"xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" "#,
            r#"xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" "#,
            r#"xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" "#,
            r#"xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" "#,
            r#"xmlns:dc="http://purl.org/dc/elements/1.1/" "#,
            r#"xmlns:opf="http://www.idpf.org/2007/opf/" "#,
            r#"xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" "#,
            r#"xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" "#,
            r#"xmlns:epub="http://www.idpf.org/2007/ops" "#,
            r#"xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">"#,
            r#"<hp:p id="1" paraPrIDRef="0" styleIDRef="0" pageBreak="0" "#,
            r#"columnBreak="0" merged="0"><hp:run charPrIDRef="0">"#,
            r#"<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" "#,
            r#"tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1" "#,
            r#"memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">"#,
            r#"<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>"#,
            r#"<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>"#,
            r#"<hp:visibility hideFirstHeader="0" hideFirstFooter="0" "#,
            r#"hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" "#,
            r#"hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>"#,
            r#"<hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>"#,
            r#"<hp:pagePr landscape="WIDELY" width="59528" height="84186" "#,
            r#"gutterType="LEFT_ONLY"><hp:margin header="4252" footer="4252" gutter="0" "#,
            r#"left="8504" right="8504" top="5668" bottom="4252"/></hp:pagePr>"#,
            r#"<hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" "#,
            r#"suffixChar=")" supscript="0"/><hp:noteLine length="-1" type="SOLID" "#,
            r##"width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="283" "##,
            r#"belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/>"#,
            r#"<hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr>"#,
            r#"<hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" "#,
            r#"suffixChar=")" supscript="0"/><hp:noteLine length="14692344" type="SOLID" "#,
            r##"width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="0" "##,
            r#"belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/>"#,
            r#"<hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr>"#,
            r#"<hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" "#,
            r#"headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" "#,
            r#"right="1417" top="1417" bottom="1417"/></hp:pageBorderFill>"#,
            r#"<hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" "#,
            r#"headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" "#,
            r#"right="1417" top="1417" bottom="1417"/></hp:pageBorderFill>"#,
            r#"<hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" "#,
            r#"headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" "#,
            r#"right="1417" top="1417" bottom="1417"/></hp:pageBorderFill>"#,
            r#"</hp:secPr><hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" "#,
            r#"colCount="1" sameSz="1" sameGap="0"/></hp:ctrl></hp:run>"#,
            r#"<hp:run charPrIDRef="0"><hp:t>{}</hp:t></hp:run>"#,
            r#"<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" "#,
            r#"textheight="1000" baseline="850" spacing="600" horzpos="0" horzsize="42520" "#,
            r#"flags="393216"/></hp:linesegarray></hp:p></hs:sec>"#,
        ),
        escaped_text,
    )
}

fn write_part(
    writer: &mut ZipWriter<Cursor<Vec<u8>>>,
    path: &str,
    value: &str,
    method: CompressionMethod,
) -> Result<(), Hancom2020Vs0Error> {
    write_bytes_part(writer, path, value.as_bytes(), method)
}

fn write_bytes_part(
    writer: &mut ZipWriter<Cursor<Vec<u8>>>,
    path: &str,
    value: &[u8],
    method: CompressionMethod,
) -> Result<(), Hancom2020Vs0Error> {
    let mut options = SimpleFileOptions::default()
        .compression_method(method)
        .last_modified_time(DateTime::default())
        .system(System::Unix)
        .unix_permissions(0o644);
    if method == CompressionMethod::Deflated {
        options = options.compression_level(Some(NORMALIZED_DEFLATE_LEVEL));
    }
    writer
        .start_file(path, options)
        .map_err(|_| Hancom2020Vs0Error::ZipConstruction)?;
    writer
        .write_all(value)
        .map_err(|_| Hancom2020Vs0Error::ZipConstruction)
}

fn verify_package(bytes: &[u8]) -> Result<usize, Hancom2020Vs0Error> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())
        .map_err(|_| Hancom2020Vs0Error::PackageValidation)?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())
        .map_err(|_error: GraphError| Hancom2020Vs0Error::PackageValidation)?;
    let _index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )
    .map_err(|_| Hancom2020Vs0Error::PackageValidation)?;
    Ok(graph.parts.len())
}
