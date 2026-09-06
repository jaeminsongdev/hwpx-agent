use std::io::{self, Write as _};
use std::net::{Ipv4Addr, SocketAddr};
use std::process::ExitCode;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use artifact_service::{ContentDigest, SubjectDigest, TenantId};
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use remote_sync_host::{
    CheckpointHost, LocalPostgresHistoryCheckpointConfig, LocalPostgresHistoryCheckpointDispatcher,
    LoopbackCheckpointServer,
};
use retention_sync_service::{
    MirrorId, MirrorRegistration, ProjectRole, RemoteHead, RequestContext, RetentionClass,
    RetentionPolicy, RetentionSyncService,
};
use revision_service::{BranchId, ProjectId, RevisionId};
use serde::Serialize;
use uuid::Uuid;
use zeroize::Zeroizing;

const REQUIRED_MODE: &str = "isolated-current-pc";
const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const SERVICE_ID: &str = "p17-checkpoint-probe";

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
    generation: u64,
    tenant_id: TenantId,
    project_id: ProjectId,
    branch_id: BranchId,
    mirror_id: MirrorId,
    revision_id: RevisionId,
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

fn policy() -> Result<RetentionPolicy, ProbeFailure> {
    RetentionPolicy::new(
        [
            (RetentionClass::Source, 3_600),
            (RetentionClass::Result, 3_600),
            (RetentionClass::Preview, 3_600),
            (RetentionClass::Evidence, 3_600),
            (RetentionClass::Trace, 3_600),
            (RetentionClass::Diff, 3_600),
            (RetentionClass::Receipt, 3_600),
        ],
        0,
    )
    .map_err(|_| ProbeFailure::Configuration)
}

fn write_event(event: &impl Serialize) -> Result<(), ProbeFailure> {
    let encoded = serde_json::to_string(event).map_err(|_| ProbeFailure::Output)?;
    let mut output = io::stdout().lock();
    writeln!(output, "{encoded}").map_err(|_| ProbeFailure::Output)?;
    output.flush().map_err(|_| ProbeFailure::Output)
}

fn read_config() -> Result<ProbeConfig, ProbeFailure> {
    if setting("HWPX_P17_PROBE_MODE")? != REQUIRED_MODE {
        return Err(ProbeFailure::Configuration);
    }
    let database_port = number::<u16>("HWPX_P17_PG_PORT")?;
    let bind_port = number::<u16>("HWPX_P17_BIND_PORT")?;
    let exchanges = number::<u8>("HWPX_P17_EXCHANGES")?;
    let generation = number::<u64>("HWPX_P17_GENERATION")?;
    if !(1..=8).contains(&exchanges) || generation == 0 {
        return Err(ProbeFailure::Configuration);
    }
    let tenant_id = TenantId::new(
        Uuid::parse_str(&setting("HWPX_P17_TENANT_UUID")?)
            .map_err(|_| ProbeFailure::Configuration)?,
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    let project_id = ProjectId::parse(&setting("HWPX_P17_PROJECT_ID")?)
        .map_err(|_| ProbeFailure::Configuration)?;
    let branch_id = BranchId::parse(&setting("HWPX_P17_BRANCH_ID")?)
        .map_err(|_| ProbeFailure::Configuration)?;
    let mirror_id = MirrorId::parse_public(&setting("HWPX_P17_MIRROR_ID")?)
        .map_err(|_| ProbeFailure::Configuration)?;
    let revision_id = RevisionId::parse(&setting("HWPX_P17_REVISION_ID")?)
        .map_err(|_| ProbeFailure::Configuration)?;
    let database = LocalPostgresHistoryCheckpointConfig::new(
        database_port,
        setting("HWPX_P17_PG_DATABASE")?,
        setting("HWPX_P17_PG_USER")?,
        setting("HWPX_P17_PG_PASSWORD")?,
    )
    .map_err(|_| ProbeFailure::Configuration)?;
    Ok(ProbeConfig {
        database,
        bind_port,
        exchanges,
        generation,
        tenant_id,
        project_id,
        branch_id,
        mirror_id,
        revision_id,
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
    let service_subject = authentication
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
    Ok((authentication, service_subject))
}

fn registry(
    config: &ProbeConfig,
    service_subject: SubjectDigest,
    now: u64,
) -> Result<RetentionSyncService, ProbeFailure> {
    let registry = RetentionSyncService::default();
    registry
        .put_policy(config.tenant_id, "sync.local", policy()?)
        .and_then(|()| {
            registry.provision_project(
                config.tenant_id,
                config.project_id,
                "sync.local",
                [(service_subject, ProjectRole::Owner)],
            )
        })
        .and_then(|()| {
            registry.register_branch(
                config.tenant_id,
                config.project_id,
                config.branch_id,
                RemoteHead {
                    revision_id: Some(config.revision_id),
                    generation: config.generation,
                },
            )
        })
        .and_then(|()| {
            registry.register_mirror(
                &RequestContext::new(config.tenant_id, service_subject, now),
                &MirrorRegistration {
                    project_id: config.project_id,
                    branch_id: config.branch_id,
                    mirror_id: config.mirror_id,
                    device_sha256: ContentDigest::of(b"p17-isolated-device"),
                    observed_head: RemoteHead {
                        revision_id: Some(config.revision_id),
                        generation: config.generation,
                    },
                    snapshot_sha256: ContentDigest::of(b"p17-isolated-snapshot"),
                },
            )
        })
        .map_err(|_| ProbeFailure::Configuration)?;
    Ok(registry)
}

fn run() -> Result<(), ProbeFailure> {
    let config = read_config()?;
    let now = now_unix_seconds()?;
    let (authentication, service_subject) = authentication(&config, now)?;
    let dispatcher = LocalPostgresHistoryCheckpointDispatcher::connect(
        &config.database,
        config.tenant_id,
        service_subject,
    )
    .map_err(|_| ProbeFailure::Database)?;
    let registry = registry(&config, service_subject, now)?;
    let host = CheckpointHost::new(authentication, registry, dispatcher);
    let server = LoopbackCheckpointServer::bind(
        SocketAddr::from((Ipv4Addr::LOCALHOST, config.bind_port)),
        host,
        "ko-KR".to_owned(),
        Duration::from_secs(5),
    )
    .map_err(|_| ProbeFailure::Server)?;
    let local_addr = server.local_addr().map_err(|_| ProbeFailure::Server)?;
    write_event(&ReadyEvent {
        schema_version: "hwpx-agent.p17-postgres-host-probe/v1",
        event: "ready",
        port: local_addr.port(),
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
            remote_sync_host::CheckpointServeOutcome::Succeeded => {
                succeeded = succeeded.saturating_add(1);
            }
            remote_sync_host::CheckpointServeOutcome::Rejected => {
                rejected = rejected.saturating_add(1);
            }
            remote_sync_host::CheckpointServeOutcome::Unavailable => {
                unavailable = unavailable.saturating_add(1);
            }
        }
    }
    write_event(&CompleteEvent {
        schema_version: "hwpx-agent.p17-postgres-host-probe/v1",
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
