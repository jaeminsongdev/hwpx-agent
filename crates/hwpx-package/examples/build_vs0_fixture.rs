use std::env;
use std::error::Error;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;

use hwpx_package::Hancom2020Vs0Builder;

const FIXTURE_TEXT: &str = "HWPX Agent VS-0 한글 2020 실제 열기 검증";

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let output = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: build_vs0_fixture <new-output.hwpx>")?;
    if arguments.next().is_some() {
        return Err("usage: build_vs0_fixture <new-output.hwpx>".into());
    }
    let artifact = Hancom2020Vs0Builder::build(FIXTURE_TEXT)?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(output)?;
    artifact.with_verified_bytes(|bytes| file.write_all(bytes))??;
    file.sync_all()?;
    println!(
        "schema=hwpx-agent.vs0-fixture-build/v1 state=pass size={} sha256={}",
        artifact.size_bytes(),
        hex::encode(artifact.sha256())
    );
    Ok(())
}
