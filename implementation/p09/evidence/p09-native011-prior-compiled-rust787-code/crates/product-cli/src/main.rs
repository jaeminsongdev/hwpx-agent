use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

use hwpx_agent_cli::Vs0Engine;

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{}", error.code());
            ExitCode::from(2)
        }
    }
}

fn run() -> Result<(), hwpx_agent_cli::Vs0Error> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    if arguments.next().as_deref() != Some(std::ffi::OsStr::new("create-vs0")) {
        return Err(hwpx_agent_cli::Vs0Error::InvalidRequest);
    }
    let request = arguments
        .next()
        .map(PathBuf::from)
        .ok_or(hwpx_agent_cli::Vs0Error::InvalidRequest)?;
    let workspace = arguments
        .next()
        .map(PathBuf::from)
        .ok_or(hwpx_agent_cli::Vs0Error::InvalidRequest)?;
    if arguments.next().is_some() {
        return Err(hwpx_agent_cli::Vs0Error::InvalidRequest);
    }
    let result = Vs0Engine::new()?.execute_file(request, workspace)?;
    let public = result.public_json()?;
    println!("{}", String::from_utf8_lossy(&public));
    Ok(())
}
