use super::*;

type Opened = (TestReader, PackageGraph, hwpx_package::PackagePath, PreservingXmlDocument);

fn opened(body: &str) -> Result<Opened, Box<dyn Error>> {
    let section = format!("<q:section xmlns:q='{PARAGRAPH_NS}' xml:lang='ko' xml:space='preserve'>{body}</q:section>");
    let (mut reader, graph) = open_graph(valid_archive(&section)?)?;
    let (path, xml) = part_document(&mut reader, &graph, "Contents/section0.xml")?;
    Ok((reader, graph, path, xml))
}

fn intent(path: &hwpx_package::PackagePath, xml: &PreservingXmlDocument, indexes: &[usize], order: &[usize]) -> Result<PatchIntent, Box<dyn Error>> {
    Ok(PatchIntent::PermuteSiblingElements {
        targets: indexes.iter().map(|&i| XmlElementSelector::bind(path, xml, i)).collect::<Result<_, _>>()?,
        source_order: order.to_vec(),
    })
}

fn paragraphs(xml: &PreservingXmlDocument) -> Vec<usize> {
    xml.elements().iter().enumerate().filter(|(_, e)| e.name().local_name() == "p").map(|(i, _)| i).collect()
}

fn apply(reader: &mut TestReader, graph: &PackageGraph, intents: &[PatchIntent], limits: PatchLimits) -> Result<hwpx_package::PatchResult, PatchError> {
    PreservingPatchEngine::apply_with_limits(reader, graph, PackageGraphLimits::default(),
        hwpx_package::IdRuleProfile::current_hancom_2020_core_v1(), IdIndexLimits::default(), limits, intents)
}

fn section(result: &hwpx_package::PatchResult) -> Result<String, Box<dyn Error>> {
    result.verify_artifact_integrity()?;
    assert!(result.parts().iter().all(|p| p.disposition() != PatchPartDisposition::Untouched || p.source_sha256() == Some(p.output_sha256())));
    let artifact = PreservingWriter::build(result, PackageLimits::default(), PackageGraphLimits::default(), IdIndexLimits::default(), WriterLimits::default())?;
    artifact.with_verified_bytes(|bytes| -> Result<String, Box<dyn Error>> {
        let (mut reader, graph) = open_graph(bytes.to_vec())?;
        let entry = reader.entries().iter().find(|e| e.path.as_str() == "Contents/section0.xml").ok_or("section")?.index;
        let output = reader.read_entry(entry)?;
        let (_, xml) = part_document(&mut reader, &graph, "Contents/section0.xml")?;
        xml.verify_untouched_round_trip()?;
        Ok(String::from_utf8(output)?)
    })?
}

fn paragraph(id: usize, text: &str) -> String {
    format!("<q:p id='{id}' paraPrIDRef='1' styleIDRef='1'><q:run charPrIDRef='1'><q:t>{text}</q:t></q:run></q:p>")
}

#[test]
fn permutation_exact_unequal_subtrees_keep_inherited_and_local_namespaces() -> TestResult {
    let a = paragraph(1, "짧음 &amp; &#xAC00;");
    let b = paragraph(2, "LONGER-PRIVATE<z:leaf xmlns:z='urn:local' z:flag='keep'/>TAIL");
    let c = "<alias:p xmlns:alias='http://www.hancom.co.kr/hwpml/2011/paragraph' id='3'/>";
    let (mut reader, graph, path, xml) = opened(&(a.clone()+&b+c))?;
    let operation = intent(&path, &xml, &paragraphs(&xml), &[2, 0, 1])?;
    assert_eq!(format!("{operation:?}"), "PermuteSiblingElements(<redacted>)");
    let result = apply(&mut reader, &graph, &[operation], PatchLimits::default())?;
    let output = section(&result)?;
    assert_eq!(output, format!("<q:section xmlns:q='{PARAGRAPH_NS}' xml:lang='ko' xml:space='preserve'>{c}{a}{b}</q:section>"));
    assert_eq!(result.changed_parts(), 1); assert_eq!(result.intent_count(), 1); Ok(())
}

#[test]
fn permutation_nonselected_elements_comments_pi_and_gaps_remain_positional() -> TestResult {
    let a=paragraph(1,"FIRST"); let b=paragraph(2,"UNCHANGED"); let c=paragraph(3,"LAST-LONG");
    assert!(matches!(PreservingXmlDocument::parse(b"<root><?keep yes?></root>"),
        Err(hwpx_package::PreservingXmlError::Safe(hwpx_package::SafeXmlError::ProcessingInstructionForbidden))));
    let body=format!("PRE{a}\n<!--KEEP-->{b}<!--SECOND--> \t{c}POST");
    let (mut reader,graph,path,xml)=opened(&body)?;let p=paragraphs(&xml);
    let result=apply(&mut reader,&graph,&[intent(&path,&xml,&[p[0],p[2]],&[1,0])?],PatchLimits::default())?;
    let expected=format!("PRE{c}\n<!--KEEP-->{b}<!--SECOND--> \t{a}POST");
    assert!(section(&result)?.contains(&expected));Ok(())
}

#[test]
fn permutation_fixed_slot_is_not_copied_or_charged_to_moved_byte_budget() -> TestResult {
    let a=paragraph(1,"A");let b=paragraph(2,&"L".repeat(4096));let c=paragraph(3,"C");
    let (mut reader,graph,path,xml)=opened(&(a.clone()+&b+&c))?;
    let limits=PatchLimits::new(PatchLimitConfig{max_fragment_bytes:a.len()+c.len(),..PatchLimitConfig::default()})?;
    let result=apply(&mut reader,&graph,&[intent(&path,&xml,&paragraphs(&xml),&[2,1,0])?],limits)?;
    assert!(section(&result)?.contains(&(c+&b+&a)));Ok(())
}

#[test]
fn permutation_cardinality_rejects_empty_single_and_mismatched_lists() -> TestResult {
    let (mut reader,graph,path,xml)=opened(&(paragraph(1,"A")+&paragraph(2,"B")))?;let p=paragraphs(&xml);
    for (indexes,order) in [(vec![],vec![]),(vec![p[0]],vec![0]),(p.clone(),vec![1]),(p.clone(),vec![0,1,2])] {
        assert!(matches!(apply(&mut reader,&graph,&[intent(&path,&xml,&indexes,&order)?],PatchLimits::default()),Err(PatchError::ValueInvalid)));
    }Ok(())
}

#[test]
fn permutation_order_rejects_duplicates_out_of_range_and_identity() -> TestResult {
    let (mut reader,graph,path,xml)=opened(&(paragraph(1,"A")+&paragraph(2,"B")))?;let p=paragraphs(&xml);
    for order in [[1,1],[2,0],[usize::MAX,0],[0,1]] {
        assert!(matches!(apply(&mut reader,&graph,&[intent(&path,&xml,&p,&order)?],PatchLimits::default()),Err(PatchError::ValueInvalid)));
    }Ok(())
}

#[test]
fn permutation_targets_reject_reverse_duplicate_nested_and_different_parents() -> TestResult {
    let (mut reader,graph,path,xml)=opened(&(paragraph(1,"A")+&paragraph(2,"B")))?;let p=paragraphs(&xml);
    let run=element(&xml,"run",0)?;let other_run=element(&xml,"run",1)?;
    for indexes in [[p[1],p[0]],[p[0],p[0]],[p[0],run],[run,other_run]] {
        assert!(matches!(apply(&mut reader,&graph,&[intent(&path,&xml,&indexes,&[1,0])?],PatchLimits::default()),Err(PatchError::ValueInvalid)));
    }
    assert!(matches!(apply(&mut reader,&graph,&[intent(&path,&xml,&[xml.root_element(),p[0]],&[1,0])?],PatchLimits::default()),Err(PatchError::RootMutation)));Ok(())
}

#[test]
fn permutation_stale_source_and_cross_part_selectors_are_rejected() -> TestResult {
    let (mut reader,graph,path,xml)=opened(&(paragraph(1,"A")+&paragraph(2,"B")))?;let p=paragraphs(&xml);
    let (_,_,_,foreign)=opened(&(paragraph(1,"ALTERED")+&paragraph(2,"B")))?;
    let mut operation=intent(&path,&xml,&p,&[1,0])?;
    if let PatchIntent::PermuteSiblingElements{targets,..}=&mut operation {targets[1]=XmlElementSelector::bind(&path,&foreign,p[1])?;}
    assert!(matches!(apply(&mut reader,&graph,&[operation],PatchLimits::default()),Err(PatchError::SelectorStale)));
    let (other_path,other)=part_document(&mut reader,&graph,"Contents/header.xml")?;
    let operation=PatchIntent::PermuteSiblingElements{targets:vec![XmlElementSelector::bind(&path,&xml,p[0])?,XmlElementSelector::bind(&other_path,&other,other.root_element())?],source_order:vec![1,0]};
    assert!(matches!(apply(&mut reader,&graph,&[operation],PatchLimits::default()),Err(PatchError::SelectorStale)));Ok(())
}

#[test]
fn permutation_overlapping_delete_attribute_and_second_permutation_keep_conflict_guard() -> TestResult {
    let (mut reader,graph,path,xml)=opened(&(paragraph(1,"A")+&paragraph(2,"B")))?;let p=paragraphs(&xml);
    let operation=intent(&path,&xml,&p,&[1,0])?;
    let other=[PatchIntent::DeleteSubtree{target:XmlElementSelector::bind(&path,&xml,p[0])?},
        PatchIntent::ReplaceAttribute{target:XmlAttributeSelector::bind(&path,&xml,p[0],attribute(&xml,p[0],"id")?)?,value:PatchAttributeValue::Text(PatchText::new("9")?)},operation.clone()];
    for conflict in other {assert!(matches!(apply(&mut reader,&graph,&[operation.clone(),conflict],PatchLimits::default()),Err(PatchError::Conflict)));}Ok(())
}

#[test]
fn permutation_target_limit_is_aggregate_across_intents() -> TestResult {
    let body=(1..=4).map(|i|paragraph(i,"X")).collect::<String>();let (mut reader,graph,path,xml)=opened(&body)?;let p=paragraphs(&xml);
    let operations=[intent(&path,&xml,&p[..2],&[1,0])?,intent(&path,&xml,&p[2..],&[1,0])?];
    let limits=PatchLimits::new(PatchLimitConfig{max_intents:3,..PatchLimitConfig::default()})?;
    assert!(matches!(apply(&mut reader,&graph,&operations,limits),Err(PatchError::LimitExceeded{limit:"permutation_targets"})));
    let limits=PatchLimits::new(PatchLimitConfig{max_intents:4,..PatchLimitConfig::default()})?;
    section(&apply(&mut reader,&graph,&operations,limits)?)?;Ok(())
}

#[test]
fn permutation_copied_bytes_are_aggregate_and_exact_boundary_is_accepted() -> TestResult {
    let body=(1..=4).map(|i|paragraph(i,"X")).collect::<String>();let (mut reader,graph,path,xml)=opened(&body)?;let p=paragraphs(&xml);
    let operations=[intent(&path,&xml,&p[..2],&[1,0])?,intent(&path,&xml,&p[2..],&[1,0])?];
    let limits=PatchLimits::new(PatchLimitConfig{max_fragment_bytes:body.len()-1,..PatchLimitConfig::default()})?;
    assert!(matches!(apply(&mut reader,&graph,&operations,limits),Err(PatchError::LimitExceeded{limit:"permutation_bytes"})));
    let limits=PatchLimits::new(PatchLimitConfig{max_fragment_bytes:body.len(),..PatchLimitConfig::default()})?;
    section(&apply(&mut reader,&graph,&operations,limits)?)?;Ok(())
}

#[test]
fn permutation_preserves_ids_and_references_without_bypassing_final_validation() -> TestResult {
    let body=paragraph(1,"A")+&paragraph(2,"B");let (mut reader,graph,path,xml)=opened(&body)?;let p=paragraphs(&xml);
    let operation=intent(&path,&xml,&p,&[1,0])?;
    let result=apply(&mut reader,&graph,&[operation.clone()],PatchLimits::default())?;
    let output=section(&result)?;assert_eq!(output.matches("styleIDRef='1'").count(),2);assert_eq!(output.matches("charPrIDRef='1'").count(),2);
    let header=graph.parts.iter().find(|p|p.path.as_str()=="Contents/header.xml").ok_or("header")?.path.clone();
    let (_,head)=part_document(&mut reader,&graph,header.as_str())?;let style=element(&head,"style",0)?;
    let deletion=PatchIntent::DeleteSubtree{target:XmlElementSelector::bind(&header,&head,style)?};
    assert!(matches!(apply(&mut reader,&graph,&[operation,deletion],PatchLimits::default()),Err(PatchError::IdIndex(_))));Ok(())
}

#[test]
fn permutation_thousand_siblings_one_transaction_is_deterministic() -> TestResult {
    let body=(1..=1000).map(|i|paragraph(i,"X")).collect::<String>();let (mut reader,graph,path,xml)=opened(&body)?;let p=paragraphs(&xml);
    let order=(0..p.len()).rev().collect::<Vec<_>>();let operation=intent(&path,&xml,&p,&order)?;
    let a=apply(&mut reader,&graph,&[operation.clone()],PatchLimits::default())?;
    let b=apply(&mut reader,&graph,&[operation],PatchLimits::default())?;
    assert_eq!(part_output_hash(&a,"Contents/section0.xml")?,part_output_hash(&b,"Contents/section0.xml")?);
    let expected=(1..=1000).rev().map(|i|paragraph(i,"X")).collect::<String>();assert!(section(&a)?.contains(&expected));Ok(())
}
