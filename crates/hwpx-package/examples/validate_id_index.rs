use std::env;
use std::fs;
use std::io::Cursor;
use std::process::ExitCode;

use hwpx_package::{
    BoundedZipReader, IdIndex, IdIndexLimits, IdKind, IdRuleProfile, PackageGraph,
    PackageGraphLimits, PackageLimits,
};

struct ProbeFailure {
    stage: &'static str,
    code: &'static str,
    issues: Vec<(&'static str, Option<IdKind>)>,
}

fn main() -> ExitCode {
    let inputs = env::args_os().skip(1).collect::<Vec<_>>();
    if inputs.is_empty() {
        eprintln!("usage_error: approved HWPX fixture path required");
        return ExitCode::from(2);
    }
    for (ordinal, path) in inputs.iter().enumerate() {
        let Ok(bytes) = fs::read(path) else {
            eprintln!("fixture {ordinal}: input_read_failed");
            return ExitCode::from(1);
        };
        let index = match validate(bytes) {
            Ok(index) => index,
            Err(failure) => {
                eprintln!(
                    "fixture {ordinal}: {}_failed:{}",
                    failure.stage, failure.code
                );
                for (code, expected_kind) in failure.issues {
                    eprintln!("fixture {ordinal}: issue:{code}:{expected_kind:?}");
                }
                return ExitCode::from(1);
            }
        };
        println!(
            "fixture {ordinal}: profile={}, parts={}, declarations={}, references={}",
            index.profile_version(),
            index.parts_scanned(),
            index.declarations().len(),
            index.references().len()
        );
    }
    ExitCode::SUCCESS
}

fn validate(bytes: Vec<u8>) -> Result<IdIndex, ProbeFailure> {
    let mut reader =
        BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default()).map_err(|error| {
            ProbeFailure {
                stage: "reader",
                code: error.code(),
                issues: Vec::new(),
            }
        })?;
    let graph =
        PackageGraph::build(&mut reader, PackageGraphLimits::default()).map_err(|error| {
            ProbeFailure {
                stage: "graph",
                code: error.code(),
                issues: Vec::new(),
            }
        })?;
    IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )
    .map_err(|error| ProbeFailure {
        stage: "index",
        code: error.code(),
        issues: error
            .validation()
            .map(|report| {
                report
                    .issues()
                    .iter()
                    .take(16)
                    .map(|issue| (issue.code(), issue.expected_kind()))
                    .collect()
            })
            .unwrap_or_default(),
    })
}
