//! Fresh current source/catalog/routes for each final commit boundary, not execution authority.
use super::*;
use crate::stored_revision_commit::StoredPrecommitGuard;

impl PreparedCatalogMaskExecutionManifest{
    /// # Errors
    /// The trusted server supplies a fresh routing snapshot/time at EACH check, not public request JSON.
    /// The original manifest validates identity, health, policy and source; the current catalog is mandatory.
    /// Does not authenticate the routing source itself, open a denied product route or grant Native permission.
    pub fn current_commit_guard<'a,R,B,S,V,F>(&'a self,provider:&'a StoredFormProvider<'_,R,B,S,V>,formats:&'a dyn CurrentPersonalInfoCatalogSource,
        mut current:F)->impl StoredPrecommitGuard+'a
    where R:ArtifactMetadataRepository+'a,B:EncryptedBlobStore+'a,S:ArtifactScanner+'a,V:RevisionRepository+'a,
        F:FnMut()->Result<(RouteContext,CapabilityRouteCatalog,u64),()>+'a{
        let mut stopped=false;
        move||{
            if stopped{return Err(StoredCommitError::CurrentGuard);}
            let result=current().and_then(|(context,routes,now)|self.verify(provider,formats,&context,&routes,now).map(|_|()).map_err(|_|()));
            if result.is_err(){stopped=true;return Err(StoredCommitError::CurrentGuard);}Ok(())
        }
    }
}
