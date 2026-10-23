    use super::*;
    use hwpx_package::document_import::structure::{caption_edit_batch::CaptionLayoutReplacement as Layout,
        caption_layout::CaptionLayout};
    use domain_ir::NativeCaptionSide;
    fn layout()->CaptionLayout {CaptionLayout {side:NativeCaptionSide::Left,full_size:true,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}}
    #[test]
    fn caption_state_compiler_reuses_exact_joined_input_and_matches_original_combined_output() -> TestResult {
        let bytes=with_begin(&object(0,"<hp:t>private old</hp:t>"))?;let source=structure(&bytes,"state-compiler")?;
        let state=ImportedCaptionSourceState::import(&source,limits()?)?;let frame=&state.frames().frames()[0];
        let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"private changed & <x>\r\n"}];
        let layouts=[Layout {caption_id:&frame.logical_caption_id,layout:layout()}];
        let candidate=state.lower_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
        let baseline=source.lower_caption_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
        assert_eq!(&candidate.receipt().source_state,state.receipt());assert_eq!(&candidate.receipt().output,baseline.receipt());
        assert!(candidate.receipt().input_numbering_and_frames_reused);assert!(!candidate.receipt().execution_publication_authority);
        let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;
        assert_eq!(parts(&output)?,parts(&baseline.with_verified_bytes(<[u8]>::to_vec)?)?);
        let rebuilt=structure(&output,"state-compiler")?;let after=ImportedCaptionSourceState::import(&rebuilt,limits()?)?;
        assert_eq!(after.frames().plain_text(&after.frames().frames()[0].segments[0].logical_source_id),Some(texts[0].replacement));
        assert_eq!(after.numbering().controls()[0].stored_number,19);
        assert_eq!(after.object_states().objects()[0].object_state_sha256,state.object_states().objects()[0].object_state_sha256);
        assert_ne!(after.receipt().joined_state_sha256,state.receipt().joined_state_sha256);
        assert!(!format!("{candidate:?}{}",serde_json::to_string(candidate.receipt())?).contains("private changed"));Ok(())
    }
    #[test]
    fn caption_state_compiler_whole_form_proof_requires_same_original_state_proof_and_fresh_bytes() -> TestResult {
        let bytes=with_begin(&object(0,"<hp:t>oldA</hp:t>"))?;let forms=base::forms(&bytes,"state-proof")?;
        let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;let frame=&state.frames().frames()[0];
        let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"new"}];
        let layouts=[Layout {caption_id:&frame.logical_caption_id,layout:layout()}];let proof=forms.reconstruct_source_for_verification(&bytes)?;
        let candidate=proof.lower_caption_state_edit_batch_candidate(&forms,&state,&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
        let pure=state.lower_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
        assert_eq!(candidate.receipt(),pure.receipt());
        let other=base::forms(&bytes,"state-proof")?;let other_state=ImportedCaptionSourceState::import(other.body_structure(),limits()?)?;
        assert!(matches!(proof.lower_caption_state_edit_batch_candidate(&forms,&other_state,&bytes,&texts,&layouts,limits()?,WriterLimits::default()),Err(E::Source)));
        assert!(matches!(proof.lower_caption_state_edit_batch_candidate(&other,&state,&bytes,&texts,&layouts,limits()?,WriterLimits::default()),Err(E::Source)));
        assert!(matches!(proof.lower_caption_state_edit_batch_candidate(&other,&other_state,&bytes,&texts,&layouts,limits()?,WriterLimits::default()),Err(E::Source)));
        let mut drift=bytes.clone();drift[0]^=1;
        assert!(matches!(proof.lower_caption_state_edit_batch_candidate(&forms,&state,&drift,&texts,&layouts,limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
    }
    #[test]
    fn caption_state_compiler_admission_limits_are_exact_and_cannot_be_reused_under_other_budgets() -> TestResult {
        let bytes=with_begin(&object(0,"<hp:t>oldA</hp:t>"))?;let source=structure(&bytes,"state-limits")?;
        let state=ImportedCaptionSourceState::import(&source,limits()?)?;let frame=&state.frames().frames()[0];
        let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"new"}];
        for config in [ReferenceAuxiliaryLimitConfig {text_bytes:1,..Default::default()},
            ReferenceAuxiliaryLimitConfig {text_bytes:128_000,..Default::default()},
            ReferenceAuxiliaryLimitConfig {items_per_kind:100,..Default::default()}] {
            let changed=ReferenceAuxiliaryLimits::new(config)?;
            assert!(matches!(state.lower_edit_batch_candidate(&bytes,&texts,&[],changed,WriterLimits::default()),Err(E::Limit)));
        }
        let original=state.lower_edit_batch_candidate(&bytes,&texts,&[],limits()?,WriterLimits::default())?;
        assert!(original.receipt().input_numbering_and_frames_reused);Ok(())
    }
    #[test]
    fn caption_state_compiler_keeps_invalid_duplicate_noop_opaque_protection_writer_and_source_rejections() -> TestResult {
        let bytes=with_begin(&object(0,"<hp:t>oldA</hp:t>"))?;let source=structure(&bytes,"state-rejections")?;
        let state=ImportedCaptionSourceState::import(&source,limits()?)?;let frame=&state.frames().frames()[0];
        let good=Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"new"};
        assert!(matches!(state.lower_edit_batch_candidate(&bytes,&[Request {replacement:"bad\0",..good}],&[],limits()?,WriterLimits::default()),Err(E::Value)));
        let duplicate=[Request {caption_id:good.caption_id,text_id:good.text_id,replacement:"new"},Request {caption_id:good.caption_id,text_id:good.text_id,replacement:"other"}];
        assert!(matches!(state.lower_edit_batch_candidate(&bytes,&duplicate,&[],limits()?,WriterLimits::default()),Err(E::Selection)));
        assert!(matches!(state.lower_edit_batch_candidate(&bytes,&[Request {caption_id:good.caption_id,text_id:good.text_id,replacement:"oldA"}],&[],limits()?,WriterLimits::default()),Err(E::NoChange)));
        let foreign=LogicalId::parse("foreign-state-caption")?;
        assert!(matches!(state.lower_edit_batch_candidate(&bytes,&[Request {caption_id:&foreign,text_id:good.text_id,replacement:"new"}],&[],limits()?,WriterLimits::default()),Err(E::Selection)));
        assert!(matches!(state.lower_edit_batch_candidate(&bytes,&[good],&[],limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?),Err(E::Writer)));
        let mut drift=bytes.clone();drift[0]^=1;
        assert!(matches!(state.lower_edit_batch_candidate(&drift,&[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"new"}],&[],limits()?,WriterLimits::default()),Err(E::Source)));
        let locked=with_begin(&object(0,"<hp:t>oldA</hp:t>").replace("lock='0'","lock='1'"))?;
        let source=structure(&locked,"state-locked")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let frame=&state.frames().frames()[0];
        let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"new"}];
        assert!(matches!(state.lower_edit_batch_candidate(&locked,&texts,&[Layout {caption_id:&frame.logical_caption_id,layout:layout()}],limits()?,WriterLimits::default()),Err(E::Protection)));
        let opaque=with_begin(&object(0,"<hp:t>old<!--private-->A</hp:t>"))?;let source=structure(&opaque,"state-opaque")?;
        let state=ImportedCaptionSourceState::import(&source,limits()?)?;let frame=&state.frames().frames()[0];
        let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"new"}];
        assert!(matches!(state.lower_edit_batch_candidate(&opaque,&texts,&[],limits()?,WriterLimits::default()),Err(E::Selection)));Ok(())
    }
    #[test]
    fn caption_state_compiler_multiple_parts_keeps_source_state_binding_and_complete_output_readback() -> TestResult {
        let bytes=rewrite(&fixture::two_sections()?,|name,data|{
            if name=="Contents/header.xml"{return Ok(HEADER.as_bytes().to_vec());}
            if name.starts_with("Contents/section"){let i=usize::from(name.ends_with("section1.xml"));let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&object(i,"<hp:t>oldA</hp:t>"));
                return Ok(if i==1{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)
        })?;
        let forms=base::forms(&bytes,"state-multiple")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;
        let frames=state.frames().frames();let texts=[Request {caption_id:&frames[0].logical_caption_id,text_id:&frames[0].segments[0].logical_source_id,replacement:"first"}];
        let layouts=[Layout {caption_id:&frames[1].logical_caption_id,layout:layout()}];let proof=forms.reconstruct_source_for_verification(&bytes)?;
        let result=proof.lower_caption_state_edit_batch_candidate(&forms,&state,&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
        assert_eq!((result.receipt().output.changed_parts,result.receipt().output.observed_protection_parts),(2,2));
        let output=result.with_verified_bytes(<[u8]>::to_vec)?;let before=parts(&bytes)?;let after=parts(&output)?;
        for (name,old) in before {if !name.starts_with("Contents/section"){assert_eq!(after[&name],old);}}
        let rebuilt=structure(&output,"state-multiple")?;let after=ImportedCaptionSourceState::import(&rebuilt,limits()?)?;
        assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[19,19]);
        assert!(!result.receipt().source_state.sequence_interpretation_and_recalculation_qualified);Ok(())
    }
    #[test]
    fn caption_state_compiler_repeated192_request_outputs_reuse_models_not_source_verification_or_authority() -> TestResult {
        let bytes=with_begin(&(0..64).map(|i|object(i,"<hp:t>oldA</hp:t>")).collect::<String>())?;
        let source=structure(&bytes,"state-many")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let ids=selections(&source)?;
        let values=(0..128).map(|i|format!("private replacement {i}")).collect::<Vec<_>>();
        let texts=ids.iter().zip(&values).map(|((caption_id,text_id),replacement)|Request {caption_id,text_id,replacement}).collect::<Vec<_>>();
        let layouts=ids.iter().step_by(2).map(|(caption_id,_)|Layout {caption_id,layout:layout()}).collect::<Vec<_>>();
        let first=state.lower_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
        let reverse_text=ids.iter().zip(&values).rev().map(|((caption_id,text_id),replacement)|Request {caption_id,text_id,replacement}).collect::<Vec<_>>();
        let reverse_layout=layouts.iter().rev().copied().collect::<Vec<_>>();
        let second=state.lower_edit_batch_candidate(&bytes,&reverse_text,&reverse_layout,limits()?,WriterLimits::default())?;
        assert_eq!((first.receipt().output.text_changes.len(),first.receipt().output.layout_changes.len()),(128,64));
        assert_eq!(first.receipt().source_state.joined_state_sha256,second.receipt().source_state.joined_state_sha256);
        assert_eq!(parts(&first.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&second.with_verified_bytes(<[u8]>::to_vec)?)?);
        assert!(!first.receipt().execution_publication_authority&&!first.receipt().output.execution_publication_authority);
        assert!(!serde_json::to_string(first.receipt())?.contains("private replacement"));Ok(())
    }

