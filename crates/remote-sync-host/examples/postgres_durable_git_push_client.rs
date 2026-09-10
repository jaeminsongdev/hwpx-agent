use std::net::{Ipv4Addr, SocketAddr};
use std::process::ExitCode;
use std::time::Duration;

use local_sync::{
    AuthenticatedRemoteSyncAdapter, Connectivity, LocalMirror, LoopbackTcpTransport, RemoteHead,
    SingleUseCredentialProvider,
};
use serde::Serialize;
use zeroize::Zeroizing;

const REQUIRED_MODE: &str = "isolated-current-pc-durable-git-push-client";

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
struct PushEvent {
    schema_version: &'static str,
    outcome: &'static str,
    revision_id: String,
    generation: u64,
    snapshot_sha256: String,
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
    if port == 0 {
        return Err(ProbeFailure::Configuration);
    }
    let authorization = Zeroizing::new(setting("HWPX_P17_AUTHORIZATION")?);
    let credentials = SingleUseCredentialProvider::new(authorization.to_string())
        .map_err(|_| ProbeFailure::Configuration)?;
    let transport = LoopbackTcpTransport::new(
        SocketAddr::from((Ipv4Addr::LOCALHOST, port)),
        Duration::from_secs(10),
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    let mut adapter = AuthenticatedRemoteSyncAdapter::new(credentials, transport);
    let initial_snapshot = setting("HWPX_P17_INITIAL_SNAPSHOT_SHA256")?;
    let result_snapshot = setting("HWPX_P17_RESULT_SNAPSHOT_SHA256")?;
    let mut mirror = LocalMirror::new(
        setting("HWPX_P17_PROJECT_ID")?,
        setting("HWPX_P17_BRANCH_ID")?,
        setting("HWPX_P17_MIRROR_ID")?,
        RemoteHead::new(
            if generation == 0 {
                None
            } else {
                Some(setting("HWPX_P17_REVISION_ID")?)
            },
            generation,
        )
        .map_err(|_| ProbeFailure::Configuration)?,
        initial_snapshot,
        Connectivity::Online,
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    mirror
        .queue_local_change(
            result_snapshot.clone(),
            setting("HWPX_P17_OPERATION_PLAN_SHA256")?,
        )
        .map_err(|_| ProbeFailure::Configuration)?;
    let outcome = mirror
        .push(&mut adapter, setting("HWPX_P17_IDEMPOTENCY_KEY")?)
        .map_err(|_| ProbeFailure::Exchange)?;
    let snapshot = mirror.snapshot();
    let event = PushEvent {
        schema_version: "hwpx-agent.p17-durable-git-push-client-probe/v1",
        outcome: "succeeded",
        revision_id: outcome
            .head
            .revision_id()
            .ok_or(ProbeFailure::Exchange)?
            .to_owned(),
        generation: outcome.head.generation(),
        snapshot_sha256: snapshot.snapshot_sha256,
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
