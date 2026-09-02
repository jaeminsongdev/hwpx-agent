use std::env;
use std::fs;
use std::io::Cursor;
use std::process::ExitCode;

use hwpx_package::{
    BoundedZipReader, PackageGraph, PackageGraphLimits, PackageLimits, PatchAttributeValue,
    PatchIntent, PatchResult, PatchText, PreservingPatchEngine, PreservingXmlDocument,
    XmlAttributeSelector,
};

struct ProbeFailure {
    stage: &'static str,
    code: &'static str,
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
        let (result, mutation) = match validate(bytes) {
            Ok(results) => results,
            Err(failure) => {
                eprintln!(
                    "fixture {ordinal}: {}_failed:{}",
                    failure.stage, failure.code
                );
                return ExitCode::from(1);
            }
        };
        println!(
            "fixture {ordinal}: profile={}, parts={}, untouched={}, changed={}, added={}, declarations={}, references={}, mutation_changed={}, mutation_untouched={}",
            result.profile_version(),
            result.parts().len(),
            result.untouched_parts(),
            result.changed_parts(),
            result.added_parts(),
            result.declaration_count(),
            result.reference_count(),
            mutation.changed_parts(),
            mutation.untouched_parts(),
        );
    }
    ExitCode::SUCCESS
}

fn validate(bytes: Vec<u8>) -> Result<(PatchResult, PatchResult), ProbeFailure> {
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
    let package_entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path == graph.package_document)
        .map(|entry| entry.index)
        .ok_or(ProbeFailure {
            stage: "probe",
            code: "package_document_missing",
        })?;
    let package_bytes = reader
        .read_entry(package_entry)
        .map_err(|error| ProbeFailure {
            stage: "probe",
            code: error.code(),
        })?;
    let document = PreservingXmlDocument::parse(&package_bytes).map_err(|error| ProbeFailure {
        stage: "probe",
        code: error.code(),
    })?;
    let mutation_intents = [linear_mutation(&package_bytes, &graph, &document)?];
    let result =
        PreservingPatchEngine::apply(&mut reader, &graph, &[]).map_err(|error| ProbeFailure {
            stage: "patch",
            code: error.code(),
        })?;
    result
        .verify_artifact_integrity()
        .map_err(|error| ProbeFailure {
            stage: "artifact",
            code: error.code(),
        })?;
    let mutation =
        PreservingPatchEngine::apply(&mut reader, &graph, &mutation_intents).map_err(|error| {
            ProbeFailure {
                stage: "mutation",
                code: error.code(),
            }
        })?;
    mutation
        .verify_artifact_integrity()
        .map_err(|error| ProbeFailure {
            stage: "mutation_artifact",
            code: error.code(),
        })?;
    Ok((result, mutation))
}

fn linear_mutation(
    package_bytes: &[u8],
    graph: &PackageGraph,
    document: &PreservingXmlDocument,
) -> Result<PatchIntent, ProbeFailure> {
    let (element_index, attribute_index, value_span) = document
        .elements()
        .iter()
        .enumerate()
        .find_map(|(element_index, element)| {
            (element.name().local_name() == "itemref")
                .then(|| {
                    element
                        .attributes()
                        .iter()
                        .enumerate()
                        .find(|(_, attribute)| attribute.name().local_name() == "linear")
                        .map(|(attribute_index, attribute)| {
                            (element_index, attribute_index, attribute.value_span())
                        })
                })
                .flatten()
        })
        .ok_or(ProbeFailure {
            stage: "probe",
            code: "patch_probe_linear_missing",
        })?;
    let current = package_bytes
        .get(value_span.start()..value_span.end())
        .ok_or(ProbeFailure {
            stage: "probe",
            code: "patch_selector_stale",
        })?;
    let replacement = match current {
        b"yes" => "no",
        b"no" => "yes",
        _ => {
            return Err(ProbeFailure {
                stage: "probe",
                code: "patch_probe_linear_invalid",
            });
        }
    };
    Ok(PatchIntent::ReplaceAttribute {
        target: XmlAttributeSelector::bind(
            &graph.package_document,
            document,
            element_index,
            attribute_index,
        )
        .map_err(|error| ProbeFailure {
            stage: "probe",
            code: error.code(),
        })?,
        value: PatchAttributeValue::Text(PatchText::new(replacement).map_err(|error| {
            ProbeFailure {
                stage: "probe",
                code: error.code(),
            }
        })?),
    })
}
