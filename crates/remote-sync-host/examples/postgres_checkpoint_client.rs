use std::net::{Ipv4Addr, SocketAddr};
use std::process::ExitCode;
use std::time::Duration;

use local_sync::{
    AuthenticatedRemoteSyncAdapter, Connectivity, LocalMirror, LoopbackTcpTransport, RemoteHead,
    SingleUseCredentialProvider,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zeroize::Zeroizing;

const REQUIRED_MODE: &str = "isolated-current-pc";

#[derive(Clone, Copy, Debug)]
enum ProbeFailure {
    Configuration,
    Exchange,
    Output,
}

impl ProbeFailure {
    const fn code(self) -> &'static str {
        match self {
            Self::Configuration => "PROBE_CONFIGURATION_REJECTED",
            Self::Exchange => "PROBE_EXCHANGE_FAILED",
            Self::Output => "PROBE_OUTPUT_UNAVAILABLE",
        }
    }
}

#[derive(Serialize)]
struct CheckpointEvent {
    schema_version: &'static str,
    outcome: &'static str,
    checkpoint_id: String,
    revision_id: String,
    replayed: bool,
}

fn setting(name: &str) -> Result<String, ProbeFailure> {
    std::env::var(name).map_err(|_| ProbeFailure::Configuration)
}

fn run() -> Result<(), ProbeFailure> {
    if setting("HWPX_P17_PROBE_MODE")? != REQUIRED_MODE {
        return Err(ProbeFailure::Configuration);
    }
    let port = setting("HWPX_P17_HOST_PORT")?
        .parse::<u16>()
        .map_err(|_| ProbeFailure::Configuration)?;
    let generation = setting("HWPX_P17_GENERATION")?
        .parse::<u64>()
        .map_err(|_| ProbeFailure::Configuration)?;
    if port == 0 || generation == 0 {
        return Err(ProbeFailure::Configuration);
    }
    let authorization = Zeroizing::new(setting("HWPX_P17_AUTHORIZATION")?);
    let credentials = SingleUseCredentialProvider::new(authorization.to_string())
        .map_err(|_| ProbeFailure::Configuration)?;
    let transport = LoopbackTcpTransport::new(
        SocketAddr::from((Ipv4Addr::LOCALHOST, port)),
        Duration::from_secs(5),
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    let mut adapter = AuthenticatedRemoteSyncAdapter::new(credentials, transport);
    let revision_id = setting("HWPX_P17_REVISION_ID")?;
    let mut mirror = LocalMirror::new(
        setting("HWPX_P17_PROJECT_ID")?,
        setting("HWPX_P17_BRANCH_ID")?,
        setting("HWPX_P17_MIRROR_ID")?,
        RemoteHead::new(Some(revision_id), generation).map_err(|_| ProbeFailure::Configuration)?,
        hex::encode(Sha256::digest(b"p17-isolated-snapshot")),
        Connectivity::Online,
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    let outcome = mirror
        .checkpoint(
            &mut adapter,
            setting("HWPX_P17_IDEMPOTENCY_KEY")?,
            setting("HWPX_P17_LABEL")?,
            std::env::var("HWPX_P17_NOTE").ok(),
        )
        .map_err(|_| ProbeFailure::Exchange)?;
    let event = CheckpointEvent {
        schema_version: "hwpx-agent.p17-postgres-client-probe/v1",
        outcome: "succeeded",
        checkpoint_id: outcome.checkpoint_id,
        revision_id: outcome.revision_id,
        replayed: outcome.replayed,
    };
    println!(
        "{}",
        serde_json::to_string(&event).map_err(|_| ProbeFailure::Output)?
    );
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{}", error.code());
            ExitCode::FAILURE
        }
    }
}
