//! Read-only exact-request observation. NotObserved is NOT a no-effect or retry permit.
use crate::{RevisionCommitRequest, RevisionError, RevisionHead, RevisionNode, RevisionReceipt,
    RevisionRepository, RevisionRequestContext, RevisionService};

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CommitObservation {
    Committed(RevisionReceipt),
    /// Missing or hidden at this observation; an in-flight transaction may still commit.
    NotObserved,
}

impl<R: RevisionRepository> RevisionService<R> {
    /// Reconstructs the exact historical receipt through the repository's sealed-node reader.
    /// The PostgreSQL reader already verifies the persisted request/receipt/graph seal joins.
    /// Current branch head may have advanced; it is not substituted for the original receipt.
    /// # Errors
    /// Rejects a node bound to any other request/subject or a failed repository observation.
    /// Never commits, retries, changes job state or treats missing visibility as no effect.
    pub fn observe_commit(
        &self,
        context: &RevisionRequestContext,
        request: &RevisionCommitRequest,
    ) -> Result<CommitObservation, RevisionError> {
        self.repository().authorize_context(context)?;
        let generation = request.expected_head().generation().checked_add(1).ok_or(RevisionError::InvalidHead)?;
        let digest = request.canonical_sha256()?;
        let node = match self.repository().node(context.tenant_id(), request.project_id(), request.new_revision_id()) {
            Ok(node) => node,
            Err(RevisionError::NotFound) => return Ok(CommitObservation::NotObserved),
            Err(error) => return Err(error),
        };
        let expected = RevisionNode::sealed_from(request, generation, digest, context.subject());
        if node != expected { return Err(RevisionError::InvalidRequest); }
        let receipt = RevisionReceipt::from_commit(request, request.expected_head(),
            RevisionHead::new(Some(request.new_revision_id()), generation)?, digest, context.subject())?;
        Ok(CommitObservation::Committed(receipt))
    }
}
