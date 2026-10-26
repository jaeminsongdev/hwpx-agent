use local_workflow::{LocalWorkflow,MaterializeSlot,WorkflowError};
use sha2::{Digest as _,Sha256};
use std::{error::Error,fs,path::PathBuf};
type R=Result<(),Box<dyn Error>>;
fn fixture(max:u64)->Result<(tempfile::TempDir,PathBuf,LocalWorkflow,[u8;32]),Box<dyn Error>>{
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");
    fs::create_dir_all(root.join("input"))?;fs::create_dir(root.join("output"))?;
    let source=b"PRIVATE-original-source";fs::write(root.join("input/source.hwpx"),source)?;
    let sha=Sha256::digest(source).into();let workflow=LocalWorkflow::open(&root,max)?;
    workflow.materialize("op_01",MaterializeSlot::Source,"input/source.hwpx",&sha)?;
    Ok((temp,root,workflow,sha))
}
#[test]
fn generated_preview_is_durable_after_reopen_and_never_a_publish_candidate()->R{
    let(_t,root,w,source)=fixture(1024)?;let bytes=b"PRIVATE-generated";let sha=Sha256::digest(bytes).into();
    let receipt=w.stage_generated_preview("op_01",&source,&sha,bytes)?;
    assert_eq!(receipt.preview.size_bytes,bytes.len()as u64);assert!(!receipt.publication_or_revision_authority);
    let reopened=LocalWorkflow::open(&root,1024)?;
    assert_eq!(reopened.inspect_generated_preview("op_01",&source,&sha)?,receipt);
    assert_eq!(fs::read(root.join(".hwpx-agent/work/op_01/generated-preview.hwpx"))?,bytes);
    assert!(reopened.publish("op_01","result.hwpx",&sha).is_err());assert!(reopened.diff("op_01").is_err());
    assert_eq!(fs::read_dir(root.join("output"))?.count(),0);
    assert_eq!(fs::read(root.join("input/source.hwpx"))?,b"PRIVATE-original-source");
    assert!(!format!("{receipt:?}").contains("PRIVATE-"));Ok(())
}
#[test]
fn wrong_source_output_and_zero_digests_reject_before_creating_preview()->R{
    let(_t,root,w,source)=fixture(1024)?;let bytes=b"generated";let sha=Sha256::digest(bytes).into();
    for(s,o)in[([9;32],sha),(source,[9;32]),([0;32],sha),(source,[0;32])]{
        assert!(w.stage_generated_preview("op_01",&s,&o,bytes).is_err());
        assert!(!root.join(".hwpx-agent/work/op_01/generated-preview.hwpx").exists());}
    Ok(())
}
#[test]
fn invalid_ids_missing_source_oversize_and_empty_output_have_no_file_effect()->R{
    let(_t,root,w,source)=fixture(32)?;let bytes=b"generated";let sha=Sha256::digest(bytes).into();
    for id in["../outside","C:/outside","missing","op_01/other"]{assert!(w.stage_generated_preview(id,&source,&sha,bytes).is_err());}
    assert!(w.stage_generated_preview("op_01",&source,&Sha256::digest(b"").into(),b"").is_err());
    let large=[1u8;33];assert!(w.stage_generated_preview("op_01",&source,&Sha256::digest(large).into(),&large).is_err());
    assert!(!root.join(".hwpx-agent/work/op_01/generated-preview.hwpx").exists());Ok(())
}
#[test]
fn create_new_and_legacy_candidate_exclusion_preserve_existing_bytes()->R{
    let(_t,root,w,source)=fixture(1024)?;let bytes=b"first";let sha=Sha256::digest(bytes).into();
    w.stage_generated_preview("op_01",&source,&sha,bytes)?;
    assert!(matches!(w.stage_generated_preview("op_01",&source,&sha,bytes),Err(WorkflowError::OutputExists)));
    assert_eq!(fs::read(root.join(".hwpx-agent/work/op_01/generated-preview.hwpx"))?,bytes);
    w.materialize("op_02",MaterializeSlot::Source,"input/source.hwpx",&source)?;
    w.materialize("op_02",MaterializeSlot::Candidate,"input/source.hwpx",&source)?;
    assert!(matches!(w.stage_generated_preview("op_02",&source,&sha,bytes),Err(WorkflowError::OutputExists)));
    assert!(!root.join(".hwpx-agent/work/op_02/generated-preview.hwpx").exists());Ok(())
}
#[test]
fn changed_preview_or_source_never_passes_readback()->R{
    let(_t,root,w,source)=fixture(1024)?;let bytes=b"generated";let sha=Sha256::digest(bytes).into();
    w.stage_generated_preview("op_01",&source,&sha,bytes)?;
    fs::write(root.join(".hwpx-agent/work/op_01/generated-preview.hwpx"),b"tampered")?;
    assert!(w.inspect_generated_preview("op_01",&source,&sha).is_err());
    fs::write(root.join(".hwpx-agent/work/op_01/generated-preview.hwpx"),bytes)?;
    fs::write(root.join(".hwpx-agent/work/op_01/source.hwpx"),b"changed source")?;
    assert!(w.inspect_generated_preview("op_01",&source,&sha).is_err());Ok(())
}
#[test]
fn preexisting_hardlink_target_cannot_overwrite_external_original()->R{
    let(t,root,w,source)=fixture(1024)?;let outside=t.path().join("outside.hwpx");fs::write(&outside,b"PRIVATE-outside")?;
    fs::hard_link(&outside,root.join(".hwpx-agent/work/op_01/generated-preview.hwpx"))?;
    let bytes=b"generated";assert!(w.stage_generated_preview("op_01",&source,&Sha256::digest(bytes).into(),bytes).is_err());
    assert_eq!(fs::read(&outside)?,b"PRIVATE-outside");Ok(())
}
