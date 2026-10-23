use super::*;
use hwpx_agent_cli::form_product_request::{stored_literal_replacement::{regex::{StoredRegexReplacementProductRequest as Product,RegexReplacementProductError as E,
    REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA as SCHEMA},LiteralReplacementProductError as LE},stored_source_search::selector::review::StoredReviewScopeProductRequest as Discovery};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::regex::StoredRegexReplacementError as StoredError;
use hwpx_package::{WriterLimits,WriterLimitConfig,document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config,
    SourceSearchQuery as Query,SourceSearchMode as Mode,selector::SourceIndexScopeSelector as Scope,reviews::SourceReviewTextPolicy as Policy,
    replacement::{SourceReplacementRunPolicy as Run,SourceLiteralReplacementError as Compile,atoms::regex::SourceRegexReplacementError as CoreError}}};
use serde_json::{json,Value};
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/review_scope_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/review_cell_output_fixture.rs"] mod table;
const TAB:&str="<hp:tab width='1' leader='0' type='0'/>";
macro_rules! write_provider{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn policy(h:bool,m:bool)->Value{json!({"include_hidden_explanations":h,"include_memo_bodies":m})}
fn all()->Policy{Policy{include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_>{Query{query:q,mode:Mode::Regex,case_sensitive:true,whole_word:false,max_results:100}}
fn envelope(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>>{let revision=s.head.revision_id().ok_or("head")?.public_id();Ok(json!({
    "schema_version":SCHEMA,"idempotency_key":"PRIVATE-REGEX-KEY","plan_id":"regex-candidate-plan","project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":revision,
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(raw).hex(),"selector":{"revision_id":revision,"scope":"document"},
    "operation":{"kind":"replace_regex","query":"(K)","replacement":"${1}X<&","regex":true,"case_sensitive":true,"whole_word":false,"max_replacements":100,
        "run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)}}))}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{let mut zip=hwpx_package::BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(i)?)?)}
fn inventory(p:&Provider<'_>,base:&Value)->Result<Value,Box<dyn Error>>{let mut v=base.clone();v["schema_version"]=json!("hwpx-agent.product-source-search-request/v6");v["operation"]=json!({"kind":"scope_inventory"});
    let out=Discovery::prepare_json(p,&wire(&v)?,Default::default(),4)?;Ok(out.with_verified_json(p,5,|b|serde_json::from_slice(b))??)}
fn window(inv:&Value,region:&str,a:usize,z:usize)->Result<Value,Box<dyn Error>>{let n=inv["block_regions"].as_array().ok_or("regions")?.iter().position(|r|r==region).ok_or("region")?;
    let b=&inv["inventory"]["blocks"][n];let sha:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),
        "start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":a},
        "end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":z}}))}
