use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::Write as _;
use std::path::{Path, PathBuf};

use hwpx_package::{
    Hancom2020Vs1LayoutBuilder, Hancom2020Vs1LayoutDocument, Hancom2020Vs1LayoutInspection,
};
use sha2::{Digest as _, Sha256};

const TITLE: &str = "P05-09 VS-1 레이아웃";
const BODY: [&str; 4] = [
    "사용자 정의 용지와 제목 스타일을 적용한 첫 번째 단락입니다.",
    "첫째 단의 마지막 단락이며 문자·문단 스타일을 함께 검증합니다.",
    "둘째 단은 명시적인 단 나누기에서 시작합니다.",
    "저장·재열기·렌더 뒤에도 의미와 레이아웃이 같아야 합니다.",
];
const MAX_TARGET_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or("usage: p05_09_vs1_layout_target_fixture <build|inspect> <path.hwpx>")?;
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p05_09_vs1_layout_target_fixture <build|inspect> <path.hwpx>")?;
    if arguments.next().is_some() {
        return Err("usage: p05_09_vs1_layout_target_fixture <build|inspect> <path.hwpx>".into());
    }
    match mode.as_str() {
        "build" => build(&path),
        "inspect" => inspect_path(&path),
        _ => Err("mode must be build or inspect".into()),
    }
}

fn build(path: &Path) -> Result<(), Box<dyn Error>> {
    let document = target_document()?;
    let artifact = Hancom2020Vs1LayoutBuilder::build(&document)?;
    let inspection = artifact.inspection().clone();
    artifact.with_verified_bytes(|bytes| -> Result<(), Box<dyn Error>> {
        validate_target(&inspection)?;
        let mut output = OpenOptions::new().write(true).create_new(true).open(path)?;
        output.write_all(bytes)?;
        output.sync_all()?;
        print_result("build", bytes, &inspection);
        Ok(())
    })??;
    Ok(())
}

fn inspect_path(path: &Path) -> Result<(), Box<dyn Error>> {
    let bytes = read_bounded_fixture(path)?;
    let inspection = Hancom2020Vs1LayoutBuilder::inspect(&bytes)?;
    validate_target(&inspection)?;
    print_result("inspect", &bytes, &inspection);
    Ok(())
}

fn target_document() -> Result<Hancom2020Vs1LayoutDocument, Box<dyn Error>> {
    Ok(Hancom2020Vs1LayoutDocument::new(
        TITLE,
        BODY.into_iter().map(str::to_owned).collect(),
    )?)
}

fn validate_target(inspection: &Hancom2020Vs1LayoutInspection) -> Result<(), Box<dyn Error>> {
    let expected_text = [TITLE]
        .into_iter()
        .chain(BODY)
        .collect::<Vec<_>>()
        .join("\n");
    if inspection.paragraph_count != BODY.len() + 1
        || inspection.column_break_count != 1
        || inspection.page_metrics.body_width != 80_220
        || inspection.column_metrics.column_count != 2
        || inspection.column_metrics.total_gap != 1_700
        || inspection.character_style_count < 2
        || inspection.paragraph_style_count < 2
        || inspection.visible_text_sha256
            != <[u8; 32]>::from(Sha256::digest(expected_text.as_bytes()))
    {
        return Err("P05-09 target semantic inspection mismatch".into());
    }
    Ok(())
}

fn print_result(mode: &str, bytes: &[u8], inspection: &Hancom2020Vs1LayoutInspection) {
    println!(
        "schema=hwpx-agent.p05-09-vs1-layout-target-fixture/v1 mode={mode} state=pass size={} sha256={} parts={} paragraphs={} column_breaks={} body_width={} columns={} gap={} char_styles={} para_styles={} text_sha256={}",
        bytes.len(),
        hex::encode(Sha256::digest(bytes)),
        inspection.part_count,
        inspection.paragraph_count,
        inspection.column_break_count,
        inspection.page_metrics.body_width,
        inspection.column_metrics.column_count,
        inspection.column_metrics.total_gap,
        inspection.character_style_count,
        inspection.paragraph_style_count,
        hex::encode(inspection.visible_text_sha256),
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

#[cfg(test)]
mod tests {
    use super::*;

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
}
