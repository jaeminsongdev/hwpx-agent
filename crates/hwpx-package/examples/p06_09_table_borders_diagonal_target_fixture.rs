use std::env;
use std::error::Error;
use std::path::PathBuf;

#[allow(dead_code)]
#[path = "p06_09_table_properties_target_fixture.rs"]
mod support;

fn main() -> Result<(), Box<dyn Error>> {
    let mut values = env::args_os();
    let _program = values.next();
    let ancestor = values
        .next()
        .map(PathBuf::from)
        .ok_or("missing ancestor HWPX")?;
    let expected_ancestor_sha256 = values
        .next()
        .ok_or("missing ancestor SHA-256")?
        .into_string()
        .map_err(|_| "ancestor SHA-256 is not Unicode")?;
    let output_directory = values
        .next()
        .map(PathBuf::from)
        .ok_or("missing output directory")?;
    if values.next().is_some() {
        return Err("too many arguments".into());
    }
    support::run_table_008_009_047(&ancestor, &expected_ancestor_sha256, &output_directory)
}
