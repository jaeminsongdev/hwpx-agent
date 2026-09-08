use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{CaptionSide, TablePageSplitPolicy};
use hwpx_package::{
    BoundedZipReader, IdIndex, IdIndexLimits, IdIssueKind, IdRuleProfile, PackageGraph,
    PackageGraphLimits, PackageLimits, PreservingXmlDocument, TablePaginationHwpxLimits,
    TablePaginationHwpxReader,
};
use sha2::{Digest as _, Sha256};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const EXACT_TARGET_SHA256: &str =
    "44cfcd14d867e6b53f4a015061666fe3b9ac990d3b3c321faae863d172fe8316";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Role {
    Target,
    Readback,
}

impl Role {
    fn parse(value: &str) -> Result<Self, Box<dyn Error>> {
        match value {
            "target" => Ok(Self::Target),
            "readback" => Ok(Self::Readback),
            _ => Err("role must be target or readback".into()),
        }
    }

    const fn label(self) -> &'static str {
        match self {
            Self::Target => "target",
            Self::Readback => "readback",
        }
    }
}

struct Arguments {
    input: PathBuf,
    expected_sha256: String,
    role: Role,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let input = values
            .next()
            .map(PathBuf::from)
            .ok_or("missing input HWPX")?;
        let expected_sha256 = values
            .next()
            .ok_or("missing expected SHA-256")?
            .into_string()
            .map_err(|_| "expected SHA-256 is not Unicode")?;
        let role = values
            .next()
            .ok_or("missing role")?
            .into_string()
            .map_err(|_| "role is not Unicode")?;
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            input,
            expected_sha256,
            role: Role::parse(&role)?,
        })
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let arguments = Arguments::parse()?;
    require_lower_sha256(&arguments.expected_sha256)?;
    if arguments.role == Role::Target && arguments.expected_sha256 != EXACT_TARGET_SHA256 {
        return Err("exact target identity differs".into());
    }
    let bytes = read_bounded_file(&arguments.input, MAX_FIXTURE_BYTES)?;
    let observed_sha256 = hex(Sha256::digest(&bytes).into());
    if observed_sha256 != arguments.expected_sha256 {
        return Err("input SHA-256 mismatch".into());
    }

    let inspection = inspect(&bytes, arguments.role)?;
    println!(
        concat!(
            "schema=hwpx-agent.p06-07-table-pagination-target-oracle/v1 state=pass ",
            "role={} input_sha256={} package_parts={} tables=6 top_level_tables=5 ",
            "nested_tables=1 captions=5 equation_objects=1 line_caches={} section_sha256={}"
        ),
        arguments.role.label(),
        observed_sha256,
        inspection.package_parts,
        inspection.line_caches,
        inspection.section_sha256,
    );
    Ok(())
}

struct Inspection {
    package_parts: usize,
    line_caches: usize,
    section_sha256: String,
}

fn inspect(bytes: &[u8], role: Role) -> Result<Inspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph cardinality mismatch".into());
    }
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let id_result = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_formula_v3(),
        IdIndexLimits::default(),
    );
    if let Err(error) = id_result
        && !is_exact_equation_profile_gap(&error, &section)?
    {
        return Err(error.into());
    }
    require_tables(&section)?;
    let text = String::from_utf8(section.clone())?;
    for (marker, count) in [
        ("P06-07 ALLOW TOP", 1),
        ("P06-07 AVOID-ROW BOTTOM", 1),
        ("P06-07 B MERGED", 18),
        ("P06-07 B ROW", 30),
        ("P06-07 B NESTED", 1),
        ("P06-07 NESTED TABLE CELL", 1),
        ("P06-07 B EQUATION", 1),
        ("P06-07 BEFORE PAGE START", 1),
        ("P06-07 EXACT PAGE START", 1),
        ("P06-07 AFTER PAGE START", 1),
        ("<hp:tbl ", 6),
        ("<hp:caption ", 5),
        ("<hp:equation ", 1),
    ] {
        if text.matches(marker).count() != count {
            return Err(format!("marker cardinality differs: {marker}").into());
        }
    }
    let line_caches = text.matches("<hp:linesegarray>").count();
    match role {
        Role::Target if line_caches != 0 => return Err("target has stale line caches".into()),
        Role::Readback if line_caches == 0 => {
            return Err("readback has no renderer-produced line cache".into());
        }
        _ => {}
    }
    Ok(Inspection {
        package_parts: graph.parts.len(),
        line_caches,
        section_sha256: hex(Sha256::digest(&section).into()),
    })
}

fn is_exact_equation_profile_gap(
    error: &hwpx_package::IdIndexError,
    section: &[u8],
) -> Result<bool, Box<dyn Error>> {
    let Some(report) = error.validation() else {
        return Ok(false);
    };
    let [issue] = report.issues() else {
        return Ok(false);
    };
    if issue.kind() != IdIssueKind::UnknownIdLikeAttribute
        || issue.source().part().as_str() != "Contents/section0.xml"
    {
        return Ok(false);
    }
    let document = PreservingXmlDocument::parse(section)?;
    let Some(element) = document.elements().get(issue.source().element_index()) else {
        return Ok(false);
    };
    let Some(attribute) = element.attributes().get(issue.source().attribute_index()) else {
        return Ok(false);
    };
    let value_span = issue.source().value_span();
    let value = section.get(value_span.start()..value_span.end());
    Ok(
        element.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
            && element.name().local_name() == "equation"
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == "id"
            && value == Some(b"2100000100"),
    )
}

fn require_tables(section: &[u8]) -> Result<(), Box<dyn Error>> {
    let limits = TablePaginationHwpxLimits::default();
    let expected = [
        (TablePageSplitPolicy::Allow, 1, Some(CaptionSide::Top)),
        (TablePageSplitPolicy::AvoidRow, 1, Some(CaptionSide::Bottom)),
        (TablePageSplitPolicy::AvoidTable, 0, None),
        (TablePageSplitPolicy::AvoidTable, 1, Some(CaptionSide::Top)),
        (TablePageSplitPolicy::AvoidTable, 1, Some(CaptionSide::Top)),
        (
            TablePageSplitPolicy::AvoidTable,
            1,
            Some(CaptionSide::Bottom),
        ),
    ];
    if TablePaginationHwpxReader::count_in_section(section, limits)? != expected.len() {
        return Err("table cardinality differs".into());
    }
    for (ordinal, (page_split, header_rows, caption_side)) in expected.into_iter().enumerate() {
        let readback = TablePaginationHwpxReader::read_in_section(section, ordinal, limits)?;
        if readback.page_split != page_split
            || readback.repeat_header_rows != header_rows
            || readback.caption.as_ref().map(|caption| caption.side) != caption_side
        {
            return Err(format!("table {ordinal} pagination semantics differ").into());
        }
    }
    Ok(())
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
        .ok_or("required package part is missing")?;
    Ok(reader.read_entry(index)?)
}

fn read_bounded_file(path: &Path, maximum: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > maximum
    {
        return Err("input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if bytes.len() as u64 != metadata.len() {
        return Err("input changed while being read".into());
    }
    Ok(bytes)
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("SHA-256 must be 64 lowercase hexadecimal characters".into());
    }
    Ok(())
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn target_artifact_passes_when_present() {
        let path = concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../fixtures/target-build/p06-07-table-pagination-target-20260909-04/target.hwpx"
        );
        let Ok(bytes) = fs::read(path) else {
            return;
        };
        inspect(&bytes, Role::Target).expect("target oracle");
        assert_eq!(hex(Sha256::digest(&bytes).into()), EXACT_TARGET_SHA256);
    }

    #[test]
    fn target_artifact_fails_closed_as_renderer_readback() {
        let path = concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../fixtures/target-build/p06-07-table-pagination-target-20260909-04/target.hwpx"
        );
        let Ok(bytes) = fs::read(path) else {
            return;
        };
        assert!(inspect(&bytes, Role::Readback).is_err());
    }

    #[test]
    fn target_artifact_package_tamper_rejects() {
        let path = concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../fixtures/target-build/p06-07-table-pagination-target-20260908-02/target.hwpx"
        );
        let Ok(mut bytes) = fs::read(path) else {
            return;
        };
        bytes[0] = b'X';
        assert!(inspect(&bytes, Role::Target).is_err());
    }
}
