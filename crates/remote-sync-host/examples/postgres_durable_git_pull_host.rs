use std::io::{self, Write as _};
use std::net::{Ipv4Addr, SocketAddr};
use std::path::PathBuf;
use std::process::ExitCode;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use remote_sync_host::{
    GitPullHost, GitPullServeOutcome, LocalPostgresGitMirrorPullCoordinator,
    LocalPostgresHistoryCheckpointConfig, LoopbackGitPullServer,
};
use serde::Serialize;
use uuid::Uuid;
use zeroize::Zeroizing;

const REQUIRED_MODE: &str = "isolated-current-pc-durable-git-pull";
const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const SERVICE_ID: &str = "p17-durable-git-pull-probe";

#[derive(Clone, Copy, Debug)]
enum ProbeFailure {
    Configuration,
    Database,
    Server,
    Clock,
    Output,
}

impl ProbeFailure {
    const fn code(self) -> &'static str {
        match self {
            Self::Configuration => "PROBE_CONFIGURATION_REJECTED",
            Self::Database => "PROBE_DATABASE_UNAVAILABLE",
            Self::Server => "PROBE_SERVER_UNAVAILABLE",
            Self::Clock => "PROBE_CLOCK_UNAVAILABLE",
            Self::Output => "PROBE_OUTPUT_UNAVAILABLE",
        }
    }
}

#[derive(Serialize)]
struct ReadyEvent {
    schema_version: &'static str,
    event: &'static str,
    port: u16,
    expected_exchanges: u8,
}

#[derive(Serialize)]
struct CompleteEvent {
    schema_version: &'static str,
    event: &'static str,
    succeeded: u8,
    rejected: u8,
    unavailable: u8,
}

struct ProbeConfig {
    database: LocalPostgresHistoryCheckpointConfig,
    bind_port: u16,
    exchanges: u8,
    tenant_id: TenantId,
    repository: PathBuf,
    git_program: PathBuf,
    hmac_secret: Zeroizing<String>,
}

fn setting(name: &str) -> Result<String, ProbeFailure> {
    std::env::var(name).map_err(|_| ProbeFailure::Configuration)
}

fn number<T: std::str::FromStr>(name: &str) -> Result<T, ProbeFailure> {
    setting(name)?
        .parse::<T>()
        .map_err(|_| ProbeFailure::Configuration)
}

fn now_unix_seconds() -> Result<u64, ProbeFailure> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|_| ProbeFailure::Clock)
        .map(|duration| duration.as_secs())
}

fn read_config() -> Result<ProbeConfig, ProbeFailure> {
    if setting("HWPX_P17_PROBE_MODE")? != REQUIRED_MODE {
        return Err(ProbeFailure::Configuration);
    }
    let bind_port = number::<u16>("HWPX_P17_BIND_PORT")?;
    let exchanges = number::<u8>("HWPX_P17_EXCHANGES")?;
    if !(1..=8).contains(&exchanges) {
        return Err(ProbeFailure::Configuration);
    }
    let tenant_id = TenantId::new(
        Uuid::parse_str(&setting("HWPX_P17_TENANT_UUID")?)
            .map_err(|_| ProbeFailure::Configuration)?,
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    let database = LocalPostgresHistoryCheckpointConfig::new(
        number::<u16>("HWPX_P17_PG_PORT")?,
        setting("HWPX_P17_PG_DATABASE")?,
        setting("HWPX_P17_PG_USER")?,
        setting("HWPX_P17_PG_PASSWORD")?,
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    Ok(ProbeConfig {
        database,
        bind_port,
        exchanges,
        tenant_id,
        repository: PathBuf::from(setting("HWPX_P17_BARE_REPOSITORY")?),
        git_program: PathBuf::from(setting("HWPX_P17_GIT_PROGRAM")?),
        hmac_secret: Zeroizing::new(setting("HWPX_P17_AUTH_HMAC_SECRET")?),
    })
}

fn authentication(
    config: &ProbeConfig,
    now: u64,
) -> Result<(AuthMiddleware, SubjectDigest), ProbeFailure> {
    let active_from = now.checked_sub(60).ok_or(ProbeFailure::Clock)?;
    let active_until = now.checked_add(600).ok_or(ProbeFailure::Clock)?;
    let mut authentication = AuthMiddleware::new(
        RESOURCE,
        METADATA,
        60,
        AuthRegistryLimits::product_maximums(),
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    authentication
        .register_local_hmac_key(
            ISSUER,
            KEY_ID,
            config.hmac_secret.as_bytes().to_vec(),
            active_from,
            active_until,
        )
        .map_err(|_| ProbeFailure::Configuration)?;
    let subject = authentication
        .register_service(
            ISSUER,
            SERVICE_ID,
            PrincipalGrant::new(
                config.tenant_id,
                TenantRole::Worker,
                [AuthScope::MirrorSync],
                active_from,
                active_until,
            )
            .map_err(|_| ProbeFailure::Configuration)?,
        )
        .map_err(|_| ProbeFailure::Configuration)?;
    Ok((authentication, subject))
}

fn write_event(event: &impl Serialize) -> Result<(), ProbeFailure> {
    let encoded = serde_json::to_string(event).map_err(|_| ProbeFailure::Output)?;
    let mut output = io::stdout().lock();
    writeln!(output, "{encoded}").map_err(|_| ProbeFailure::Output)?;
    output.flush().map_err(|_| ProbeFailure::Output)
}

fn run() -> Result<(), ProbeFailure> {
    let config = read_config()?;
    let now = now_unix_seconds()?;
    let (authentication, subject) = authentication(&config, now)?;
    let coordinator = LocalPostgresGitMirrorPullCoordinator::connect(
        &config.database,
        config.tenant_id,
        subject,
        &config.repository,
        &config.git_program,
    )
    .map_err(|_| ProbeFailure::Database)?;
    let host = GitPullHost::new(authentication, coordinator);
    let server = LoopbackGitPullServer::bind(
        SocketAddr::from((Ipv4Addr::LOCALHOST, config.bind_port)),
        host,
        Duration::from_secs(5),
    )
    .map_err(|_| ProbeFailure::Server)?;
    let port = server
        .local_addr()
        .map_err(|_| ProbeFailure::Server)?
        .port();
    write_event(&ReadyEvent {
        schema_version: "hwpx-agent.p17-durable-git-pull-host-probe/v1",
        event: "ready",
        port,
        expected_exchanges: config.exchanges,
    })?;
    let mut succeeded = 0_u8;
    let mut rejected = 0_u8;
    let mut unavailable = 0_u8;
    for _ in 0..config.exchanges {
        match server
            .serve_one_at(now_unix_seconds()?)
            .map_err(|_| ProbeFailure::Server)?
        {
            GitPullServeOutcome::Succeeded => succeeded = succeeded.saturating_add(1),
            GitPullServeOutcome::Rejected => rejected = rejected.saturating_add(1),
            GitPullServeOutcome::Unavailable => unavailable = unavailable.saturating_add(1),
        }
    }
    write_event(&CompleteEvent {
        schema_version: "hwpx-agent.p17-durable-git-pull-host-probe/v1",
        event: "complete",
        succeeded,
        rejected,
        unavailable,
    })
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
