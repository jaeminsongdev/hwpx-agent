use std::env;
use std::error::Error;
use std::path::PathBuf;

#[allow(dead_code)]
#[path = "p06_09_table_properties_target_oracle.rs"]
mod support;

fn main() -> Result<(), Box<dyn Error>> {
    let mut values = env::args_os();
    let _program = values.next();
    let manifest = path_argument(&mut values, "fixture manifest")?;
    let manifest_sha256 = string_argument(&mut values, "manifest SHA-256")?;
    let oracle_008 = path_argument(&mut values, "TABLE-008 oracle HWPX")?;
    let oracle_008_sha256 = string_argument(&mut values, "TABLE-008 oracle SHA-256")?;
    let oracle_009 = path_argument(&mut values, "TABLE-009 oracle HWPX")?;
    let oracle_009_sha256 = string_argument(&mut values, "TABLE-009 oracle SHA-256")?;
    let oracle_047 = path_argument(&mut values, "TABLE-047 oracle HWPX")?;
    let oracle_047_sha256 = string_argument(&mut values, "TABLE-047 oracle SHA-256")?;
    if values.next().is_some() {
        return Err("too many arguments".into());
    }
    support::run_table_008_009_047(
        &manifest,
        &manifest_sha256,
        [&oracle_008, &oracle_009, &oracle_047],
        [&oracle_008_sha256, &oracle_009_sha256, &oracle_047_sha256],
    )
}

fn path_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<PathBuf, Box<dyn Error>> {
    arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {name}").into())
}

fn string_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<String, Box<dyn Error>> {
    arguments
        .next()
        .ok_or_else(|| format!("missing {name}"))?
        .into_string()
        .map_err(|_| format!("{name} is not Unicode").into())
}
