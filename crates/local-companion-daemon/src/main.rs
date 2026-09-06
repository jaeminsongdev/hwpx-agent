#![forbid(unsafe_code)]

use std::io::{self, BufRead, Write as _};
use std::path::PathBuf;

use local_companion_daemon::{
    LocalCompanionConfig, LocalCompanionDaemon, MAX_REQUEST_BYTES, SessionToken,
};

fn main() {
    if run().is_err() {
        eprintln!("local-companion-daemon: stopped safely");
        std::process::exit(1);
    }
}

fn run() -> Result<(), ()> {
    let config_path = exact_config_argument()?;
    let config = LocalCompanionConfig::load(&config_path).map_err(|_| ())?;
    let token = SessionToken::from_environment().map_err(|_| ())?;
    let daemon = LocalCompanionDaemon::new(config);
    let stdin = io::stdin();
    let mut reader = io::BufReader::new(stdin.lock());
    loop {
        let Some(bytes) = read_bounded_line(&mut reader)? else {
            return Ok(());
        };
        let response = daemon.handle(&bytes, &token);
        let mut stdout = io::stdout().lock();
        serde_json::to_writer(&mut stdout, &response).map_err(|_| ())?;
        stdout.write_all(b"\n").map_err(|_| ())?;
        stdout.flush().map_err(|_| ())?;
    }
}

fn exact_config_argument() -> Result<PathBuf, ()> {
    let mut arguments = std::env::args_os();
    let _program = arguments.next().ok_or(())?;
    if arguments.next().as_deref() != Some(std::ffi::OsStr::new("--config")) {
        return Err(());
    }
    let path = PathBuf::from(arguments.next().ok_or(())?);
    if arguments.next().is_some() || !path.is_absolute() {
        return Err(());
    }
    Ok(path)
}

fn read_bounded_line(reader: &mut impl BufRead) -> Result<Option<Vec<u8>>, ()> {
    let mut limited = io::Read::take(&mut *reader, (MAX_REQUEST_BYTES + 2) as u64);
    let mut bytes = Vec::new();
    let count = limited.read_until(b'\n', &mut bytes).map_err(|_| ())?;
    if count == 0 {
        return Ok(None);
    }
    if bytes.len() > MAX_REQUEST_BYTES + 1 || bytes.last() != Some(&b'\n') {
        return Err(());
    }
    bytes.pop();
    if bytes.last() == Some(&b'\r') {
        bytes.pop();
    }
    if bytes.is_empty() || bytes.len() > MAX_REQUEST_BYTES {
        return Err(());
    }
    Ok(Some(bytes))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bounded_reader_requires_complete_nonempty_line() {
        assert_eq!(
            read_bounded_line(&mut &b"{}\n"[..]),
            Ok(Some(b"{}".to_vec()))
        );
        assert!(read_bounded_line(&mut &b""[..]).is_ok_and(|value| value.is_none()));
        assert!(read_bounded_line(&mut &b"{}"[..]).is_err());
        assert!(read_bounded_line(&mut &b"\n"[..]).is_err());
    }
}
