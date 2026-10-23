mod p08_19_support;

use std::env;
use std::error::Error;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::{Path, PathBuf};

use hwpx_agent_foundation::workdir::SecureWorkspace;
use p08_19_support::common::{
    PreparedCase, copied_insertion_cases, load_insertion_sources, sha256,
};
use serde::Serialize;

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_insertion_manifest_sha256: String,
    target_profile: TargetProfile,
    direct_feature_count: usize,
    cases: Vec<ManifestCase>,
    actual_hangul_2020: bool,
    save_reopen: &'static str,
    resource_integrity: &'static str,
    object_bounds: &'static str,
    render: &'static str,
    differential: &'static str,
    rollback_or_retry: &'static str,
}

#[derive(Serialize)]
struct TargetProfile {
    product: &'static str,
    build: &'static str,
    architecture: &'static str,
    locale: &'static str,
    executable_sha256: &'static str,
}

#[derive(Serialize)]
struct ManifestCase {
    case_id: String,
    feature_id: String,
    capability_id: String,
    file: String,
    package_sha256: String,
    package_bytes: usize,
    output_section_sha256: String,
    lowering_evidence: Vec<p08_19_support::common::LoweringEvidence>,
    object_kind: String,
    native_object_id: u32,
    native_instance_id: u32,
    resource_integrity_expected: bool,
}

fn main() -> Result<(), Box<dyn Error>> {
    let (input_directory, output_directory) = parse_arguments()?;
    if output_directory.exists() {
        return Err("output directory already exists".into());
    }
    if !output_directory
        .parent()
        .ok_or("output directory has no parent")?
        .is_dir()
    {
        return Err("output parent does not exist".into());
    }

    let sources = load_insertion_sources(&input_directory)?;
    let mut cases = copied_insertion_cases(&sources)?;
    cases.extend(p08_19_support::geometry::cases(&sources.shape)?);
    cases.extend(p08_19_support::appearance::cases(
        &sources.shape,
        &sources.image,
    )?);
    cases.extend(p08_19_support::properties::cases(
        &sources.shape,
        &sources.image,
        &sources.text_box,
        &sources.freeform,
    )?);
    cases.extend(p08_19_support::special::cases(&sources.shape)?);
    cases.extend(p08_19_support::composition::cases(&sources.shape)?);
    cases.extend(p08_19_support::canvas::cases(&sources.image)?);

    publish_bundle(&output_directory, sources.manifest_sha256, cases)
}

fn publish_bundle(
    output_directory: &Path,
    source_manifest_sha256: String,
    cases: Vec<PreparedCase>,
) -> Result<(), Box<dyn Error>> {
    let workspace = SecureWorkspace::create(output_directory)?;
    let mut manifest_cases = Vec::with_capacity(cases.len());
    for case in cases {
        let staging = PathBuf::from("p08-19").join(&case.file);
        let output = Path::new(&case.file);
        let staged = workspace.stage_bytes(&staging, &case.bytes)?;
        workspace.publish(&staged, output)?;
        let package_sha256 = staged.sha256;
        let package_bytes = usize::try_from(staged.size_bytes)?;
        manifest_cases.push(ManifestCase {
            case_id: case.case_id,
            feature_id: case.feature_id,
            capability_id: case.capability_id,
            file: case.file,
            package_sha256,
            package_bytes,
            output_section_sha256: case.output_section_sha256,
            lowering_evidence: case.lowering_evidence,
            object_kind: case.object_kind,
            native_object_id: case.native_object_id,
            native_instance_id: case.native_instance_id,
            resource_integrity_expected: case.resource_integrity_expected,
        });
    }
    let manifest = Manifest {
        schema_version: "hwpx-agent.p08-19-object-target-bundle/v1",
        source_insertion_manifest_sha256: source_manifest_sha256,
        target_profile: TargetProfile {
            product: "Hancom Hangul 2020",
            build: "11.0.0.9136",
            architecture: "x86",
            locale: "ko-KR",
            executable_sha256: "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        },
        direct_feature_count: manifest_cases.len(),
        cases: manifest_cases,
        actual_hangul_2020: false,
        save_reopen: "not_run",
        resource_integrity: "not_run",
        object_bounds: "not_run",
        render: "not_run",
        differential: "not_run",
        rollback_or_retry: "not_run",
    };
    let manifest_bytes = serde_json::to_vec_pretty(&manifest)?;
    write_new(
        &output_directory.join("output/fixture-manifest.json"),
        &manifest_bytes,
    )?;
    println!(
        "{}",
        serde_json::to_string(&serde_json::json!({
            "state": "pass",
            "schema_version": manifest.schema_version,
            "output_directory": output_directory.join("output"),
            "case_count": manifest.cases.len(),
            "direct_feature_count": manifest.direct_feature_count,
            "manifest_sha256": sha256(&manifest_bytes),
            "actual_hangul_2020": false
        }))?
    );
    Ok(())
}

fn parse_arguments() -> Result<(PathBuf, PathBuf), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let input = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("insertion fixture directory is required")?;
    let output = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("output directory is required")?;
    if arguments.next().is_some() {
        return Err("too many arguments".into());
    }
    if !input.is_absolute() || !output.is_absolute() {
        return Err("input and output directories must be absolute".into());
    }
    Ok((input, output))
}

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}
