//! SQL job input data only, never an execution or registry capability.
use crate::stored_revision_commit::job::identity::StoredJobPolicy;
use artifact_service::ContentDigest;
use operation_engine::TransactionLimits;
use revision_service::{CommitId,RevisionId};
use std::fmt;
pub struct HttpsAtomicSqlJobRun<'a>{pub policy:StoredJobPolicy,pub commit:CommitId,pub new_revision:RevisionId,pub limits:TransactionLimits,
    pub agent:uuid::Uuid,pub execution:uuid::Uuid,pub lease_seconds:i32,pub event:ContentDigest,pub workspace:&'a std::path::Path}
impl fmt::Debug for HttpsAtomicSqlJobRun<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsAtomicSqlJobRun(<redacted>; server_inputs_not_authority)")}}
