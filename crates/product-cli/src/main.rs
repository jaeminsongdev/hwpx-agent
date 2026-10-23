use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

use hwpx_agent_cli::Vs0Engine;

fn main() -> ExitCode {
    if env::args_os().nth(1).as_deref() == Some(std::ffi::OsStr::new("reference-source")) {
        return reference_source();
    }
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{}", error.code());
            ExitCode::from(2)
        }
    }
}

fn reference_source() -> ExitCode {
    use hwpx_agent_cli::reference_validation_product::source::{
        REFERENCE_SOURCE_INCOMPLETE_EXIT, ReferenceSourceError, assess_cli_arguments,
    };
    let result = assess_cli_arguments(env::args_os().skip(2)).and_then(|assessment| {
        let limits = domain_ir::ReferenceAuxiliaryLimits::new(Default::default())
            .map_err(|_| ReferenceSourceError::Request)?;
        assessment.canonical_json(limits)
    });
    match result {
        Ok(json) => {
            println!("{}", String::from_utf8_lossy(&json));
            ExitCode::from(REFERENCE_SOURCE_INCOMPLETE_EXIT)
        }
        Err(error) => {
            eprintln!("{error}");
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
