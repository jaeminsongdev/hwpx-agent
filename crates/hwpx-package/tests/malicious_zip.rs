use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_package::{BoundedZipReader, PackageLimitConfig, PackageLimits};
use zip::write::{FullFileOptions, SimpleFileOptions};
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn valid_stored_and_deflated_entries_are_verified() -> TestResult {
    let bytes = build_zip(&[
        (
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        (
            "Contents/section0.xml",
            b"<hp:sec xmlns:hp=\"urn:test\">\xed\x95\x9c\xea\xb8\x80</hp:sec>",
            CompressionMethod::Deflated,
        ),
    ])?;
    let mut package = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    assert_eq!(package.entries().len(), 2);
    assert_eq!(package.entries()[0].path.as_str(), "mimetype");
    assert_eq!(package.read_entry(0)?, b"application/hwp+zip");
    assert!(package.read_entry(1)?.starts_with(b"<hp:sec"));
    Ok(())
}

#[test]
fn limits_are_finite_and_checked_before_allocation() -> TestResult {
    let defaults = PackageLimitConfig::default();
    let mut invalid = defaults;
    invalid.max_archive_bytes = 0;
    assert_error(PackageLimits::new(invalid), "invalid_limit")?;
    invalid = defaults;
    invalid.max_archive_bytes = PackageLimits::HARD_MAX_ARCHIVE_BYTES + 1;
    assert_error(PackageLimits::new(invalid), "invalid_limit")?;
    invalid = defaults;
    invalid.max_entry_expanded_bytes = 100;
    invalid.max_total_expanded_bytes = 99;
    assert_error(PackageLimits::new(invalid), "invalid_limit_relation")?;

    let one = build_zip(&[("one.xml", b"0123456789", CompressionMethod::Stored)])?;
    let mut archive_limit = defaults;
    archive_limit.max_archive_bytes = one.len() as u64 - 1;
    expect_open_code(
        &one,
        PackageLimits::new(archive_limit)?,
        "archive_too_large",
    )?;

    let two = build_zip(&[
        ("one.xml", b"12345678", CompressionMethod::Stored),
        ("two.xml", b"12345678", CompressionMethod::Stored),
    ])?;
    let mut entry_count = defaults;
    entry_count.max_entries = 1;
    expect_open_code(&two, PackageLimits::new(entry_count)?, "too_many_entries")?;

    let mut entry_size = defaults;
    entry_size.max_entry_expanded_bytes = 9;
    entry_size.max_total_expanded_bytes = 20;
    expect_open_code(
        &one,
        PackageLimits::new(entry_size)?,
        "entry_expanded_too_large",
    )?;

    let mut total_size = defaults;
    total_size.max_entry_expanded_bytes = 10;
    total_size.max_total_expanded_bytes = 12;
    expect_open_code(
        &two,
        PackageLimits::new(total_size)?,
        "total_expanded_too_large",
    )?;

    let bomb = build_zip(&[("bomb.xml", &[0_u8; 16_384], CompressionMethod::Deflated)])?;
    let mut ratio = defaults;
    ratio.max_compression_ratio = 2;
    expect_open_code(
        &bomb,
        PackageLimits::new(ratio)?,
        "compression_ratio_exceeded",
    )?;
    Ok(())
}

#[test]
fn unsafe_and_ambiguous_paths_fail_closed() -> TestResult {
    let cases = [
        ("/absolute.xml", "name_absolute"),
        ("../escape.xml", "name_traversal"),
        ("Contents/./section.xml", "name_traversal"),
        ("Contents//section.xml", "name_empty_component"),
        ("Contents\\section.xml", "name_backslash"),
        ("bad\0name.xml", "name_control_character"),
        ("bad\nname.xml", "name_control_character"),
        ("CON.xml", "name_reserved"),
        ("Lpt9.bin", "name_reserved"),
        ("name. ", "name_ambiguous_suffix"),
        ("C:stream.xml", "name_drive_or_stream"),
    ];
    for (name, code) in cases {
        let bytes = build_zip(&[(name, b"x", CompressionMethod::Stored)])?;
        expect_open_code(&bytes, PackageLimits::default(), code)?;
    }

    let mut non_utf8 = build_zip(&[("badx.xml", b"x", CompressionMethod::Stored)])?;
    set_entry_name(&mut non_utf8, 0, b"bad\xFF.xml")?;
    expect_open_code(&non_utf8, PackageLimits::default(), "name_not_utf8")?;

    let long = build_zip(&[("123456789.xml", b"x", CompressionMethod::Stored)])?;
    let name_limit = PackageLimitConfig {
        max_name_bytes: 8,
        ..PackageLimitConfig::default()
    };
    expect_open_code(
        &long,
        PackageLimits::new(name_limit)?,
        "invalid_name_length",
    )?;

    let deep = build_zip(&[("a/b/c/d.xml", b"x", CompressionMethod::Stored)])?;
    let depth_limit = PackageLimitConfig {
        max_path_depth: 3,
        ..PackageLimitConfig::default()
    };
    expect_open_code(&deep, PackageLimits::new(depth_limit)?, "path_too_deep")?;
    Ok(())
}

#[test]
fn duplicate_casefold_and_normalization_collisions_are_rejected() -> TestResult {
    let mut exact = build_zip(&[
        ("Contents/a.xml", b"1", CompressionMethod::Stored),
        ("Contents/b.xml", b"2", CompressionMethod::Stored),
    ])?;
    set_entry_name(&mut exact, 1, b"Contents/a.xml")?;
    expect_open_code(&exact, PackageLimits::default(), "name_collision")?;

    let case = build_zip(&[
        ("Contents/A.xml", b"1", CompressionMethod::Stored),
        ("contents/a.XML", b"2", CompressionMethod::Stored),
    ])?;
    expect_open_code(&case, PackageLimits::default(), "name_collision")?;

    let unicode = build_zip(&[
        ("Contents/caf\u{e9}.xml", b"1", CompressionMethod::Stored),
        ("Contents/cafe\u{301}.xml", b"2", CompressionMethod::Stored),
    ])?;
    expect_open_code(&unicode, PackageLimits::default(), "name_collision")?;

    let casefold = build_zip(&[
        ("Contents/stra\u{df}e.xml", b"1", CompressionMethod::Stored),
        ("Contents/STRASSE.xml", b"2", CompressionMethod::Stored),
    ])?;
    expect_open_code(&casefold, PackageLimits::default(), "name_collision")?;
    Ok(())
}

#[test]
fn structural_extensions_and_header_attacks_are_rejected() -> TestResult {
    let empty = finish_writer(ZipWriter::new(Cursor::new(Vec::new())))?;
    expect_open_code(&empty, PackageLimits::default(), "empty_archive")?;

    let normal = build_zip(&[("Contents/a.xml", b"abcd", CompressionMethod::Stored)])?;
    let mut trailing = normal.clone();
    trailing.extend_from_slice(b"tail");
    expect_open_code(
        &trailing,
        PackageLimits::default(),
        "unexpected_trailing_data",
    )?;

    let mut preamble = b"prefix".to_vec();
    preamble.extend_from_slice(&normal);
    expect_open_code(&preamble, PackageLimits::default(), "unexpected_preamble")?;

    let mut zip64 = normal.clone();
    let eocd = find_signature(&zip64, b"PK\x05\x06", 0)?;
    zip64[eocd + 8..eocd + 10].copy_from_slice(&u16::MAX.to_le_bytes());
    zip64[eocd + 10..eocd + 12].copy_from_slice(&u16::MAX.to_le_bytes());
    expect_open_code(&zip64, PackageLimits::default(), "zip64_unsupported")?;

    let mut multi_disk = normal.clone();
    let eocd = find_signature(&multi_disk, b"PK\x05\x06", 0)?;
    multi_disk[eocd + 4..eocd + 6].copy_from_slice(&1_u16.to_le_bytes());
    expect_open_code(
        &multi_disk,
        PackageLimits::default(),
        "multi_disk_unsupported",
    )?;

    let mut descriptor = normal.clone();
    set_flags(&mut descriptor, 0x0008)?;
    expect_open_code(
        &descriptor,
        PackageLimits::default(),
        "data_descriptor_unsupported",
    )?;

    let mut encrypted = normal.clone();
    set_flags(&mut encrypted, 0x0001)?;
    expect_open_code(&encrypted, PackageLimits::default(), "encrypted_entry")?;

    let mut unsupported = normal.clone();
    set_method(&mut unsupported, 12)?;
    expect_open_code(
        &unsupported,
        PackageLimits::default(),
        "unsupported_compression",
    )?;

    let nested_name = build_zip(&[("BinData/payload.zip", b"x", CompressionMethod::Stored)])?;
    expect_open_code(&nested_name, PackageLimits::default(), "nested_archive")?;

    let mut inconsistent = normal.clone();
    let local = find_signature(&inconsistent, b"PK\x03\x04", 0)?;
    inconsistent[local + 18..local + 22].copy_from_slice(&5_u32.to_le_bytes());
    expect_open_code(&inconsistent, PackageLimits::default(), "header_mismatch")?;

    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    writer.set_comment("0123456789")?;
    writer.start_file("a.xml", SimpleFileOptions::default())?;
    writer.write_all(b"x")?;
    let commented = finish_writer(writer)?;
    let comment_limits = PackageLimitConfig {
        max_comment_bytes: 4,
        ..PackageLimitConfig::default()
    };
    expect_open_code(
        &commented,
        PackageLimits::new(comment_limits)?,
        "comment_too_large",
    )?;
    Ok(())
}

#[test]
fn overlap_crc_nested_magic_and_symlink_fail_without_partial_output() -> TestResult {
    let mut overlap = build_zip(&[
        ("one.xml", b"1111", CompressionMethod::Stored),
        ("two.xml", b"2222", CompressionMethod::Stored),
    ])?;
    let local = find_signature(&overlap, b"PK\x03\x04", 0)?;
    let central = find_signature(&overlap, b"PK\x01\x02", 0)?;
    overlap[local + 18..local + 22].copy_from_slice(&40_u32.to_le_bytes());
    overlap[local + 22..local + 26].copy_from_slice(&40_u32.to_le_bytes());
    overlap[central + 20..central + 24].copy_from_slice(&40_u32.to_le_bytes());
    overlap[central + 24..central + 28].copy_from_slice(&40_u32.to_le_bytes());
    expect_open_code(&overlap, PackageLimits::default(), "overlapping_entries")?;

    let mut crc = build_zip(&[("Contents/a.xml", b"abcd", CompressionMethod::Stored)])?;
    let local = find_signature(&crc, b"PK\x03\x04", 0)?;
    let name_len = usize::from(u16::from_le_bytes([crc[local + 26], crc[local + 27]]));
    let extra_len = usize::from(u16::from_le_bytes([crc[local + 28], crc[local + 29]]));
    let payload = local + 30 + name_len + extra_len;
    crc[payload] ^= 0x01;
    let mut package = BoundedZipReader::open(Cursor::new(crc), PackageLimits::default())?;
    assert_read_code(&mut package, 0, "entry_integrity")?;

    let nested = build_zip(&[(
        "BinData/payload.bin",
        b"PK\x03\x04nested",
        CompressionMethod::Stored,
    )])?;
    let mut package = BoundedZipReader::open(Cursor::new(nested), PackageLimits::default())?;
    assert_read_code(&mut package, 0, "nested_archive")?;

    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    writer.add_symlink("BinData/link", "target", SimpleFileOptions::default())?;
    let symlink = finish_writer(writer)?;
    expect_open_code(&symlink, PackageLimits::default(), "unsupported_file_type")?;
    Ok(())
}

#[test]
fn repeated_rejection_has_a_stable_code() -> TestResult {
    let bytes = build_zip(&[("../escape.xml", b"x", CompressionMethod::Stored)])?;
    for _ in 0..32 {
        expect_open_code(&bytes, PackageLimits::default(), "name_traversal")?;
    }
    Ok(())
}

#[test]
fn directory_indexes_and_extra_metadata_are_bounded() -> TestResult {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    writer.add_directory("Contents/", SimpleFileOptions::default())?;
    writer.start_file("Contents/a.xml", SimpleFileOptions::default())?;
    writer.write_all(b"x")?;
    let bytes = finish_writer(writer)?;
    let mut package = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    assert_read_code(&mut package, 0, "entry_is_directory")?;
    assert_read_code(&mut package, 2, "entry_index_out_of_range")?;

    let mut options = FullFileOptions::default();
    options.add_extra_data(0xFFFF, [0_u8; 16], false)?;
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    writer.start_file("a.xml", options)?;
    writer.write_all(b"x")?;
    let extra = finish_writer(writer)?;
    let limits = PackageLimitConfig {
        max_extra_field_bytes: 8,
        ..PackageLimitConfig::default()
    };
    expect_open_code(&extra, PackageLimits::new(limits)?, "extra_field_too_large")?;

    let mut unsupported_flags = build_zip(&[("a.xml", b"x", CompressionMethod::Stored)])?;
    set_flags(&mut unsupported_flags, 0x0010)?;
    expect_open_code(
        &unsupported_flags,
        PackageLimits::default(),
        "unsupported_flags",
    )?;
    Ok(())
}

fn build_zip(entries: &[(&str, &[u8], CompressionMethod)]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, contents, method) in entries {
        let options = SimpleFileOptions::default().compression_method(*method);
        writer.start_file(*name, options)?;
        writer.write_all(contents)?;
    }
    finish_writer(writer)
}

fn finish_writer(writer: ZipWriter<Cursor<Vec<u8>>>) -> Result<Vec<u8>, Box<dyn Error>> {
    Ok(writer.finish()?.into_inner())
}

fn expect_open_code(bytes: &[u8], limits: PackageLimits, expected: &str) -> TestResult {
    match BoundedZipReader::open(Cursor::new(bytes), limits) {
        Ok(_) => Err(format!("archive unexpectedly passed; expected {expected}").into()),
        Err(error) => {
            assert_eq!(error.code(), expected);
            Ok(())
        }
    }
}

fn assert_error<T>(result: Result<T, hwpx_package::PackageError>, expected: &str) -> TestResult {
    match result {
        Ok(_) => Err(format!("operation unexpectedly passed; expected {expected}").into()),
        Err(error) => {
            assert_eq!(error.code(), expected);
            Ok(())
        }
    }
}

fn assert_read_code<R: std::io::Read + std::io::Seek>(
    package: &mut BoundedZipReader<R>,
    index: usize,
    expected: &str,
) -> TestResult {
    match package.read_entry(index) {
        Ok(_) => Err(format!("entry unexpectedly passed; expected {expected}").into()),
        Err(error) => {
            assert_eq!(error.code(), expected);
            Ok(())
        }
    }
}

fn find_signature(
    bytes: &[u8],
    signature: &[u8],
    occurrence: usize,
) -> Result<usize, Box<dyn Error>> {
    bytes
        .windows(signature.len())
        .enumerate()
        .filter(|(_, window)| *window == signature)
        .nth(occurrence)
        .map(|(position, _)| position)
        .ok_or_else(|| "ZIP signature was not found".into())
}

fn set_flags(bytes: &mut [u8], flag: u16) -> TestResult {
    let local = find_signature(bytes, b"PK\x03\x04", 0)?;
    let central = find_signature(bytes, b"PK\x01\x02", 0)?;
    let local_flags = u16::from_le_bytes([bytes[local + 6], bytes[local + 7]]) | flag;
    let central_flags = u16::from_le_bytes([bytes[central + 8], bytes[central + 9]]) | flag;
    bytes[local + 6..local + 8].copy_from_slice(&local_flags.to_le_bytes());
    bytes[central + 8..central + 10].copy_from_slice(&central_flags.to_le_bytes());
    Ok(())
}

fn set_method(bytes: &mut [u8], method: u16) -> TestResult {
    let local = find_signature(bytes, b"PK\x03\x04", 0)?;
    let central = find_signature(bytes, b"PK\x01\x02", 0)?;
    bytes[local + 8..local + 10].copy_from_slice(&method.to_le_bytes());
    bytes[central + 10..central + 12].copy_from_slice(&method.to_le_bytes());
    Ok(())
}

fn set_entry_name(bytes: &mut [u8], occurrence: usize, replacement: &[u8]) -> TestResult {
    let local = find_signature(bytes, b"PK\x03\x04", occurrence)?;
    let central = find_signature(bytes, b"PK\x01\x02", occurrence)?;
    let local_len = usize::from(u16::from_le_bytes([bytes[local + 26], bytes[local + 27]]));
    let central_len = usize::from(u16::from_le_bytes([
        bytes[central + 28],
        bytes[central + 29],
    ]));
    if replacement.len() != local_len || replacement.len() != central_len {
        return Err("replacement entry name length differs".into());
    }
    bytes[local + 30..local + 30 + local_len].copy_from_slice(replacement);
    bytes[central + 46..central + 46 + central_len].copy_from_slice(replacement);
    Ok(())
}
