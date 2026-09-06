use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::Write as _;
use std::path::{Path, PathBuf};

use hwpx_package::{
    HANCOM_2020_DENSE_COLUMN_FLOW_PROFILE_ID, Hancom2020ColumnFlowPolicy,
    Hancom2020Vs1LayoutBuilder, Hancom2020Vs1LayoutDocument, Hancom2020Vs1LayoutInspection,
};
use sha2::{Digest as _, Sha256};

const TITLE: &str = "P05-07-DENSE-START";
const END_MARKER: &str = "P05-07-DENSE-END";
const BODY_PARAGRAPH_COUNT: usize = 30;
const MAX_TARGET_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or("usage: p05_07_dense_column_flow_target_fixture <build|inspect> <path.hwpx>")?;
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p05_07_dense_column_flow_target_fixture <build|inspect> <path.hwpx>")?;
    if arguments.next().is_some() {
        return Err(
            "usage: p05_07_dense_column_flow_target_fixture <build|inspect> <path.hwpx>".into(),
        );
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
    Ok(Hancom2020Vs1LayoutDocument::new_automatic_balanced(
        TITLE,
        target_body(),
    )?)
}

fn target_body() -> Vec<String> {
    (1..=BODY_PARAGRAPH_COUNT)
        .map(|index| {
            let suffix = if index == BODY_PARAGRAPH_COUNT {
                format!(" {END_MARKER}")
            } else {
                String::new()
            };
            format!(
                "P05-07-DENSE-LINE-{index:02} automatic balanced column flow keeps this ordered synthetic paragraph intact across the current Hangul 2020 two-column layout.{suffix}"
            )
        })
        .collect()
}

fn validate_target(inspection: &Hancom2020Vs1LayoutInspection) -> Result<(), Box<dyn Error>> {
    let expected_text = [TITLE.to_owned()]
        .into_iter()
        .chain(target_body())
        .collect::<Vec<_>>()
        .join("\n");
    if inspection.profile_id != HANCOM_2020_DENSE_COLUMN_FLOW_PROFILE_ID
        || inspection.column_flow_policy != Hancom2020ColumnFlowPolicy::AutomaticBalanced
        || inspection.paragraph_count != BODY_PARAGRAPH_COUNT + 1
        || inspection.column_break_count != 0
        || inspection.page_metrics.body_width != 80_220
        || inspection.column_metrics.column_count != 2
        || inspection.column_metrics.total_gap != 1_700
        || inspection.visible_text_sha256
            != <[u8; 32]>::from(Sha256::digest(expected_text.as_bytes()))
    {
        return Err("P05-07 dense column-flow target semantic inspection mismatch".into());
    }
    Ok(())
}

fn print_result(mode: &str, bytes: &[u8], inspection: &Hancom2020Vs1LayoutInspection) {
    println!(
        "schema=hwpx-agent.p05-07-dense-column-flow-target-fixture/v1 mode={mode} state=pass size={} sha256={} paragraphs={} column_breaks={} body_width={} columns={} gap={} text_sha256={}",
        bytes.len(),
        hex::encode(Sha256::digest(bytes)),
        inspection.paragraph_count,
        inspection.column_break_count,
        inspection.page_metrics.body_width,
        inspection.column_metrics.column_count,
        inspection.column_metrics.total_gap,
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
    fn dense_fixture_build_is_deterministic_and_never_overwrites() -> Result<(), Box<dyn Error>> {
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
    fn dense_fixture_has_unique_start_end_and_ordered_markers() -> Result<(), Box<dyn Error>> {
        let body = target_body();
        assert_eq!(body.len(), BODY_PARAGRAPH_COUNT);
        assert_eq!(
            body.iter().filter(|line| line.contains(END_MARKER)).count(),
            1
        );
        for (index, line) in body.iter().enumerate() {
            assert!(line.starts_with(&format!("P05-07-DENSE-LINE-{:02}", index + 1)));
        }
        let artifact = Hancom2020Vs1LayoutBuilder::build(&target_document()?)?;
        validate_target(artifact.inspection())?;
        Ok(())
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
}
