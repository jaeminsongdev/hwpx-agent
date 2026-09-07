use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use hwpx_package::{
    BoundedZipReader, PackageGraph, PackageGraphLimits, PackageLimits, PreservationClass,
    PreservationReport, PreservationRuleProfile,
};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let input = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p06_04_preservation_diagnostic <input.hwpx>")?;
    if arguments.next().is_some() {
        return Err("exactly one input path is required".into());
    }
    let bytes = read_bounded_fixture(&input)?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let report = PreservationReport::build_with_profile(
        &mut reader,
        &graph,
        PreservationRuleProfile::Hangul2020PreviewTextV2,
    )?;
    println!(
        "schema=hwpx-agent.p06-04-preservation-diagnostic/v1 state=pass parts={} rejected={} direct_preserve_ready={}",
        report.parts().len(),
        report.counts().rejected,
        report.direct_preserve_ready(),
    );
    for record in report
        .parts()
        .iter()
        .filter(|record| record.class() == PreservationClass::Rejected)
    {
        println!(
            "rejected_path={} reason={}",
            record.path().as_str(),
            record.reason_code(),
        );
    }
    Ok(())
}

fn read_bounded_fixture(path: &Path) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_FIXTURE_BYTES
    {
        return Err("fixture input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if bytes.len() as u64 != metadata.len() {
        return Err("fixture input changed while being read".into());
    }
    Ok(bytes)
}
