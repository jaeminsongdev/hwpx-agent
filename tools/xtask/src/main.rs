#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::ffi::OsStr;
use std::fmt::Write as _;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use prost::Message;
use serde_json::Value;
use sha2::{Digest, Sha256};

const GENERATED_FILES: &[&str] = &[
    "descriptor/hwpx-agent-foundation.pb",
    "csharp/Foundation.cs",
    "rust/src/hwpx_agent.foundation.v1.rs",
    "rust/src/schema_models.rs",
    "typescript/src/schema-models.ts",
    "typescript/schema-catalog.json",
    "typescript/schema-catalog-v2.json",
];

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let arguments: Vec<String> = env::args().skip(1).collect();
    if arguments.first().map(String::as_str) != Some("generate") {
        return Err("usage: cargo run -p xtask -- generate [--check]".into());
    }
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("cannot locate repository root")?
        .to_path_buf();
    let generated = root.join("protocol/generated");
    if arguments.iter().any(|argument| argument == "--check") {
        let temporary = tempfile::tempdir()?;
        generate(&root, temporary.path())?;
        compare_generated(&generated, temporary.path())?;
        verify_contract_baseline(&root, temporary.path())?;
        println!("generated artifacts are current");
    } else {
        generate(&root, &generated)?;
        println!("generated artifacts updated");
    }
    Ok(())
}

fn generate(root: &Path, output: &Path) -> Result<(), Box<dyn std::error::Error>> {
    // Windows protoc은 비 ASCII repository path를 손상시킬 수 있으므로 모든 native
    // codegen I/O를 ASCII temp 아래에서 수행하고 Rust fs로 결과만 게시한다.
    let native_staging = ascii_native_tempdir()?;
    let proto_root = native_staging.path().join("proto");
    let proto = proto_root.join("hwpx_agent/foundation/v1/foundation.proto");
    fs::create_dir_all(proto.parent().ok_or("proto has no parent")?)?;
    fs::copy(
        root.join("protocol/proto/hwpx_agent/foundation/v1/foundation.proto"),
        &proto,
    )?;
    let rust_staging = native_staging.path().join("generated/rust/src");
    let csharp_staging = native_staging.path().join("generated/csharp");
    let descriptor_staging = native_staging
        .path()
        .join("generated/descriptor/hwpx-agent-foundation.pb");
    for directory in [
        &rust_staging,
        &csharp_staging,
        descriptor_staging
            .parent()
            .ok_or("descriptor has no parent")?,
        &output.join("rust/src"),
        &output.join("csharp"),
        output
            .join("descriptor/hwpx-agent-foundation.pb")
            .parent()
            .ok_or("output descriptor has no parent")?,
        &output.join("typescript/src"),
    ] {
        fs::create_dir_all(directory)?;
    }

    let protoc = protoc_bin_vendored::protoc_bin_path()?;
    let status = Command::new(&protoc)
        .arg(format!("--proto_path={}", proto_root.display()))
        .arg(format!("--csharp_out={}", csharp_staging.display()))
        .arg(format!(
            "--descriptor_set_out={}",
            descriptor_staging.display()
        ))
        .arg("--include_imports")
        .arg(&proto)
        .status()?;
    if !status.success() {
        return Err("protoc C#/descriptor generation failed".into());
    }

    let descriptor_bytes = fs::read(&descriptor_staging)?;
    let descriptor_set = prost_types::FileDescriptorSet::decode(descriptor_bytes.as_slice())?;
    let mut prost = prost_build::Config::new();
    prost.out_dir(&rust_staging);
    prost.compile_fds(descriptor_set)?;

    fs::copy(
        rust_staging.join("hwpx_agent.foundation.v1.rs"),
        output.join("rust/src/hwpx_agent.foundation.v1.rs"),
    )?;
    fs::copy(
        csharp_staging.join("Foundation.cs"),
        output.join("csharp/Foundation.cs"),
    )?;
    fs::copy(
        descriptor_staging,
        output.join("descriptor/hwpx-agent-foundation.pb"),
    )?;

    generate_schema_models(root, output)?;
    Ok(())
}

fn ascii_native_tempdir() -> Result<tempfile::TempDir, Box<dyn std::error::Error>> {
    let mut candidates = Vec::new();
    if let Some(profile) = env::var_os("USERPROFILE") {
        candidates.push(PathBuf::from(profile).join("AppData/Local/Temp"));
    }
    if let Some(local) = env::var_os("LOCALAPPDATA") {
        candidates.push(PathBuf::from(local).join("Temp"));
    }
    candidates.push(env::temp_dir());
    for candidate in candidates {
        if candidate.to_string_lossy().is_ascii()
            && candidate.is_dir()
            && let Ok(directory) = tempfile::Builder::new()
                .prefix("hwpx-agent-codegen-")
                .tempdir_in(candidate)
        {
            return Ok(directory);
        }
    }
    Err("no writable ASCII temporary directory is available for protoc".into())
}

fn generate_schema_models(root: &Path, output: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let source = root.join("protocol/json-schema");
    let mut schemas = Vec::new();
    for entry in fs::read_dir(&source)? {
        let path = entry?.path();
        if path.extension() != Some(OsStr::new("json")) {
            continue;
        }
        let bytes = fs::read(&path)?;
        let value: Value = serde_json::from_slice(&bytes)?;
        let id = value
            .get("$id")
            .and_then(Value::as_str)
            .ok_or("schema missing $id")?
            .to_owned();
        let title = value
            .get("title")
            .and_then(Value::as_str)
            .ok_or("schema missing title")?
            .to_owned();
        schemas.push((id, title, value, hex::encode(Sha256::digest(bytes))));
    }
    schemas.sort_by(|left, right| left.0.cmp(&right.0));

    let mut typescript = String::from("// @generated by xtask; DO NOT EDIT.\n\n");
    let ids = schemas
        .iter()
        .map(|(id, _, _, _)| format!("  {id:?},"))
        .collect::<Vec<_>>()
        .join("\n");
    let _ = write!(
        typescript,
        "export const schemaIds = [\n{ids}\n] as const;\n\n"
    );
    for (index, (_, title, schema, _)) in schemas.iter().enumerate() {
        if index > 0 {
            typescript.push('\n');
        }
        typescript.push_str(&render_interface(title, schema));
    }
    fs::write(output.join("typescript/src/schema-models.ts"), typescript)?;

    fs::write(
        output.join("rust/src/schema_models.rs"),
        render_rust_schema_models(&schemas),
    )?;

    let foundation_catalog = schemas
        .iter()
        .filter(|(id, _, _, _)| id.contains("/schemas/foundation/"))
        .map(|(id, title, _, sha256)| {
            serde_json::json!({ "id": id, "title": title, "sha256": sha256 })
        })
        .collect::<Vec<_>>();
    write_schema_catalog(
        &output.join("typescript/schema-catalog.json"),
        &foundation_catalog,
    )?;
    let additive_catalog = schemas
        .iter()
        .map(|(id, title, _, sha256)| {
            serde_json::json!({ "id": id, "title": title, "sha256": sha256 })
        })
        .collect::<Vec<_>>();
    write_schema_catalog(
        &output.join("typescript/schema-catalog-v2.json"),
        &additive_catalog,
    )?;
    Ok(())
}

fn write_schema_catalog(path: &Path, schemas: &[Value]) -> Result<(), Box<dyn std::error::Error>> {
    fs::write(
        path,
        format!(
            "{}\n",
            serde_json::to_string_pretty(&serde_json::json!({ "schemas": schemas }))?
        ),
    )?;
    Ok(())
}

fn render_rust_schema_models(schemas: &[(String, String, Value, String)]) -> String {
    let mut output = String::from("// @generated by xtask; DO NOT EDIT.\n\n");
    for (_, title, schema, _) in schemas {
        if schema.get("x-rust-model").and_then(Value::as_bool) != Some(true) {
            continue;
        }
        let required: BTreeSet<&str> = schema
            .get("required")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .collect();
        let properties: BTreeMap<&str, &Value> = schema
            .get("properties")
            .and_then(Value::as_object)
            .into_iter()
            .flat_map(|object| object.iter())
            .map(|(name, value)| (name.as_str(), value))
            .collect();
        output
            .push_str("#[derive(Clone, Debug, PartialEq, serde::Serialize, serde::Deserialize)]\n");
        output.push_str("#[serde(deny_unknown_fields)]\n");
        let _ = writeln!(output, "pub struct {title} {{");
        for (name, value) in properties {
            let kind = rust_type(value);
            let kind = if required.contains(name) {
                kind
            } else {
                format!("Option<{kind}>")
            };
            let _ = writeln!(output, "    pub {name}: {kind},");
        }
        output.push_str("}\n\n");
    }
    let trimmed_length = output.trim_end().len();
    output.truncate(trimmed_length);
    output.push('\n');
    output
}

fn rust_type(schema: &Value) -> String {
    if schema.get("const").is_some() || schema.get("enum").is_some() {
        return "String".to_owned();
    }
    match schema.get("type") {
        Some(Value::String(kind)) => match kind.as_str() {
            "string" => "String".to_owned(),
            "integer" => "u64".to_owned(),
            "number" => "f64".to_owned(),
            "boolean" => "bool".to_owned(),
            "array" => format!(
                "Vec<{}>",
                schema
                    .get("items")
                    .map_or_else(|| "serde_json::Value".to_owned(), rust_type)
            ),
            _ => "serde_json::Value".to_owned(),
        },
        Some(Value::Array(kinds)) => {
            let non_null = kinds
                .iter()
                .filter_map(Value::as_str)
                .find(|kind| *kind != "null");
            let inner = match non_null {
                Some("string") => "String",
                Some("integer") => "u64",
                Some("number") => "f64",
                Some("boolean") => "bool",
                _ => "serde_json::Value",
            };
            if kinds.iter().any(|kind| kind.as_str() == Some("null")) {
                format!("Option<{inner}>")
            } else {
                inner.to_owned()
            }
        }
        _ => "serde_json::Value".to_owned(),
    }
}

fn render_interface(title: &str, schema: &Value) -> String {
    let required: BTreeSet<&str> = schema
        .get("required")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
        .collect();
    let properties: BTreeMap<&str, &Value> = schema
        .get("properties")
        .and_then(Value::as_object)
        .into_iter()
        .flat_map(|object| object.iter())
        .map(|(name, value)| (name.as_str(), value))
        .collect();
    let mut output = format!("export interface {title} {{\n");
    for (name, value) in properties {
        let optional = if required.contains(name) { "" } else { "?" };
        let _ = writeln!(output, "  {name}{optional}: {};", typescript_type(value));
    }
    output.push_str("}\n");
    output
}

fn typescript_type(schema: &Value) -> String {
    if let Some(values) = schema.get("enum").and_then(Value::as_array) {
        return values
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(" | ");
    }
    if let Some(constant) = schema.get("const") {
        return constant.to_string();
    }
    match schema.get("type") {
        Some(Value::String(kind)) => match kind.as_str() {
            "string" => "string".to_owned(),
            "integer" | "number" => "number".to_owned(),
            "boolean" => "boolean".to_owned(),
            "array" => format!(
                "Array<{}>",
                schema
                    .get("items")
                    .map_or_else(|| "unknown".to_owned(), typescript_type)
            ),
            "object" => "Record<string, unknown>".to_owned(),
            "null" => "null".to_owned(),
            _ => "unknown".to_owned(),
        },
        Some(Value::Array(kinds)) => kinds
            .iter()
            .filter_map(Value::as_str)
            .map(|kind| if kind == "null" { "null" } else { "string" })
            .collect::<Vec<_>>()
            .join(" | "),
        _ => "unknown".to_owned(),
    }
}

fn compare_generated(
    expected_root: &Path,
    actual_root: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut drift = Vec::new();
    for relative in GENERATED_FILES {
        let expected = expected_root.join(relative);
        let actual = actual_root.join(relative);
        if !expected.is_file() || fs::read(&expected)? != fs::read(&actual)? {
            drift.push(*relative);
        }
    }
    if drift.is_empty() {
        Ok(())
    } else {
        Err(format!("generated artifact drift: {}", drift.join(", ")).into())
    }
}

fn verify_contract_baseline(
    root: &Path,
    generated_root: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut mismatches = Vec::new();
    let mut lock_paths = fs::read_dir(root.join("protocol/baseline"))?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| {
            path.file_name()
                .is_some_and(|name| name.to_string_lossy().ends_with(".lock.json"))
        })
        .collect::<Vec<_>>();
    lock_paths.sort();
    if lock_paths.is_empty() {
        return Err("no protocol baseline locks found".into());
    }
    for lock_path in lock_paths {
        let lock: Value = serde_json::from_slice(&fs::read(&lock_path)?)?;
        let artifacts = lock
            .get("artifacts")
            .and_then(Value::as_array)
            .ok_or("protocol baseline artifacts are missing")?;
        for artifact in artifacts {
            let relative = artifact
                .get("path")
                .and_then(Value::as_str)
                .ok_or("protocol baseline path is missing")?;
            let expected = artifact
                .get("sha256")
                .and_then(Value::as_str)
                .ok_or("protocol baseline hash is missing")?;
            let actual = hex::encode(Sha256::digest(fs::read(generated_root.join(relative))?));
            if actual != expected {
                mismatches.push(relative.to_owned());
            }
        }
    }
    if mismatches.is_empty() {
        Ok(())
    } else {
        Err(format!(
            "v1 contract baseline changed without a new version/migration: {}",
            mismatches.join(", ")
        )
        .into())
    }
}
