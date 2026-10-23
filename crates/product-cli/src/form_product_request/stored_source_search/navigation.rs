//! Strict SEARCH-005 continuation on a current, authenticated retained search preparation.
use super::*;
use hwpx_package::document_import::search::navigation::SourceSearchNavigationRequest;
use sha2::{Digest as _,Sha256};
pub const SOURCE_SEARCH_NEXT_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-next-request/v1";
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct NextRequest {schema_version:String,search_receipt_sha256:String,navigation:SourceSearchNavigationRequest}
impl NextRequest {
    fn parse(raw:&[u8])->Result<Self,E> {
        if raw.is_empty()||raw.len()>SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);
        let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
        let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !value.is_object()||!value.get("navigation").is_some_and(serde_json::Value::is_object)
            ||value.get("navigation").and_then(|v|v.get("cursor")).is_some_and(|v|!v.is_null()&&!v.is_object()) {return Err(E::Request);}
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        if request.schema_version!=SOURCE_SEARCH_NEXT_REQUEST_SCHEMA||request.search_receipt_sha256.len()!=64
            ||!request.search_receipt_sha256.bytes().all(|c|c.is_ascii_digit()||(b'a'..=b'f').contains(&c)){return Err(E::Request);}Ok(request)
    }
}
pub(super) fn receipt_context(receipt:&SourceSearchProductReceipt)->Result<[u8;32],E> {
    Ok(Sha256::digest(bounded(receipt,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?).into())
}
pub(super) fn bound_next(raw:&[u8],receipt:&SourceSearchProductReceipt)->Result<(SourceSearchNavigationRequest,[u8;32]),E> {
    let request=NextRequest::parse(raw)?;let context=receipt_context(receipt)?;
    if request.search_receipt_sha256!=hex::encode(context){return Err(E::Binding);}Ok((request.navigation,context))
}
impl PreparedStoredSourceSearchProduct {
    /// # Errors
    /// Identifies this retained preparation, including original key/plan/provider scope.
    /// The digest and cursor are not access grants or durable idempotency claims.
    pub fn navigation_receipt_sha256(&self)->Result<String,E> {Ok(hex::encode(self.navigation_context()?))}
    fn navigation_context(&self)->Result<[u8;32],E> {
        Ok(Sha256::digest(bounded(&self.receipt,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?).into())
    }
    /// # Errors
    /// Performs source-bound forward/backward continuation with explicit wrap,
    /// fresh original authorization and final head, without rerunning the query.
    pub fn with_next_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=NextRequest::parse(raw)?;
        if request.search_receipt_sha256!=self.navigation_receipt_sha256()? {return Err(E::Binding);}
        self.check(provider)?;
        Ok(self.candidate.with_next_verified_json(provider,&request.navigation,self.navigation_context()?,now,consume)?)
    }
}
