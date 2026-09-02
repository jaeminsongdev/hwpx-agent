use std::env;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    AtomicPackagePublisher, BoundedZipReader, IdIndexLimits, NormalizedWriter, PackageGraph,
    PackageGraphLimits, PackageLimits, PreservingPatchEngine, PreservingWriter, RoundTripLimits,
    RoundTripVerifier, WriterLimits,
};

struct ProbeFailure {
    stage: &'static str,
    code: &'static str,
}

fn main() -> ExitCode {
    let arguments = env::args_os().skip(1).collect::<Vec<_>>();
    let Some((workspace_root, inputs)) = arguments.split_first() else {
        eprintln!("usage_error: private workspace root and approved HWPX fixture paths required");
        return ExitCode::from(2);
    };
    if inputs.is_empty() {
        eprintln!("usage_error: at least one approved HWPX fixture path required");
        return ExitCode::from(2);
    }
    let Ok(workspace) = SecureWorkspace::create(PathBuf::from(workspace_root)) else {
        eprintln!("workspace_create_failed");
        return ExitCode::from(1);
    };
    for (ordinal, input) in inputs.iter().enumerate() {
        let Ok(bytes) = fs::read(input) else {
            eprintln!("fixture {ordinal}: input_read_failed");
            return ExitCode::from(1);
        };
        match verify_and_publish(&workspace, ordinal, bytes) {
            Ok(evidence) => println!(
                "fixture {ordinal}: parts={}, declarations={}, references={}, untouched_policy_violations={}, preserving_deterministic={}, normalized_deterministic={}, preserving_published=true, normalized_published=true",
                evidence.source_parts(),
                evidence.declarations(),
                evidence.references(),
                evidence.untouched_policy_violations(),
                evidence.preserving_deterministic(),
                evidence.normalized_deterministic(),
            ),
            Err(failure) => {
                eprintln!(
                    "fixture {ordinal}: {}_failed:{}",
                    failure.stage, failure.code
                );
                return ExitCode::from(1);
            }
        }
    }
    ExitCode::SUCCESS
}

fn verify_and_publish(
    workspace: &SecureWorkspace,
    ordinal: usize,
    bytes: Vec<u8>,
) -> Result<hwpx_package::RoundTripEvidence, ProbeFailure> {
    let limits = RoundTripLimits::default();
    let evidence =
        RoundTripVerifier::verify(Cursor::new(bytes.as_slice()), limits).map_err(|error| {
            let diagnostic = error.diagnostic();
            ProbeFailure {
                stage: "roundtrip",
                code: diagnostic.code(),
            }
        })?;
    let mut reader =
        BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default()).map_err(|error| {
            ProbeFailure {
                stage: "reader",
                code: error.code(),
            }
        })?;
    let graph =
        PackageGraph::build(&mut reader, PackageGraphLimits::default()).map_err(|error| {
            ProbeFailure {
                stage: "graph",
                code: error.code(),
            }
        })?;
    let patch =
        PreservingPatchEngine::apply(&mut reader, &graph, &[]).map_err(|error| ProbeFailure {
            stage: "patch",
            code: error.code(),
        })?;
    let preserving = PreservingWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )
    .map_err(|error| ProbeFailure {
        stage: "preserving_writer",
        code: error.code(),
    })?;
    let normalized = NormalizedWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )
    .map_err(|error| ProbeFailure {
        stage: "normalized_writer",
        code: error.code(),
    })?;
    publish_mode(workspace, ordinal, "preserving.hwpx", &preserving)?;
    publish_mode(workspace, ordinal, "normalized.hwpx", &normalized)?;
    Ok(evidence)
}

fn publish_mode(
    workspace: &SecureWorkspace,
    ordinal: usize,
    filename: &str,
    artifact: &hwpx_package::PackageArtifact,
) -> Result<(), ProbeFailure> {
    let parent = format!("fixture-{ordinal}");
    let staging = Path::new(&parent).join(filename);
    let output = Path::new(&parent).join(filename);
    let receipt = AtomicPackagePublisher::publish(artifact, workspace, &staging, &output).map_err(
        |error| ProbeFailure {
            stage: "publish",
            code: error.code(),
        },
    )?;
    if !receipt.staged_reopen_verified() || !receipt.published_reopen_verified() {
        return Err(ProbeFailure {
            stage: "publish_receipt",
            code: "roundtrip_publication_unverified",
        });
    }
    Ok(())
}
