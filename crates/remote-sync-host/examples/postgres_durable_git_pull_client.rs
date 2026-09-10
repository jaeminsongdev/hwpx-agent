use std::net::{Ipv4Addr, SocketAddr};
use std::process::ExitCode;
use std::time::Duration;

use local_sync::{
    AuthenticatedRemoteSyncAdapter, Connectivity, LocalMirror, LoopbackTcpTransport, MirrorPhase,
    PullOutcome, RemoteHead, SingleUseCredentialProvider, SyncError,
};
use serde::Serialize;
use zeroize::Zeroizing;

const REQUIRED_MODE: &str = "isolated-current-pc-durable-git-pull-client";

#[derive(Clone, Copy, Debug)]
enum ProbeFailure {
    Configuration,
    Exchange,
    RemoteUnavailable,
    RemoteRejected,
    InvalidResponse,
    Output,
}

impl ProbeFailure {
    const fn code(self) -> &'static str {
        match self {
            Self::Configuration => "PROBE_CONFIGURATION_REJECTED",
            Self::Exchange => "PROBE_EXCHANGE_FAILED",
            Self::RemoteUnavailable => "PROBE_REMOTE_UNAVAILABLE",
            Self::RemoteRejected => "PROBE_REMOTE_REJECTED",
            Self::InvalidResponse => "PROBE_RESPONSE_INVALID",
            Self::Output => "PROBE_OUTPUT_UNAVAILABLE",
        }
    }
}

#[derive(Serialize)]
struct PullEvent {
    schema_version: &'static str,
    outcome: &'static str,
    phase: &'static str,
    observed_generation: u64,
    conflict_generation: Option<u64>,
    snapshot_preserved: bool,
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
        initial_snapshot.clone(),
        Connectivity::Online,
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    if setting("HWPX_P17_CLIENT_STATE")? == "ahead" {
        mirror
            .queue_local_change(
                setting("HWPX_P17_LOCAL_SNAPSHOT_SHA256")?,
                setting("HWPX_P17_OPERATION_PLAN_SHA256")?,
            )
            .map_err(|_| ProbeFailure::Configuration)?;
    } else if setting("HWPX_P17_CLIENT_STATE")? != "clean" {
        return Err(ProbeFailure::Configuration);
    }
    let before = mirror.snapshot();
    let result = mirror.pull(&mut adapter);
    let after = mirror.snapshot();
    let outcome = match result {
        Ok(PullOutcome::Unchanged) => "unchanged",
        Ok(PullOutcome::Updated) => "updated",
        Err(SyncError::Conflict) => "conflict",
        Err(SyncError::RemoteUnavailable) => return Err(ProbeFailure::RemoteUnavailable),
        Err(SyncError::RemoteRejected) => return Err(ProbeFailure::RemoteRejected),
        Err(SyncError::InvalidResponse) => return Err(ProbeFailure::InvalidResponse),
        Err(_) => return Err(ProbeFailure::Exchange),
    };
    let phase = match after.phase {
        MirrorPhase::Clean => "clean",
        MirrorPhase::Ahead => "ahead",
        MirrorPhase::Conflict => "conflict",
    };
    let event = PullEvent {
        schema_version: "hwpx-agent.p17-durable-git-pull-client-probe/v1",
        outcome,
        phase,
        observed_generation: after.observed_generation,
        conflict_generation: after.conflict_generation,
        snapshot_preserved: outcome != "conflict"
            || (after.snapshot_sha256 == before.snapshot_sha256
                && after.pending_plan_sha256 == before.pending_plan_sha256),
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
