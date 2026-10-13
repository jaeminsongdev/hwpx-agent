"""P161 single declared Rust delta; invert optimization to whole P160 source."""
import base64
import hashlib
import run_current_graph_cost as prior

p=prior.p
s=p.s
SELF='tools/p09/source_xml_reuse_binding.py'
SOURCE='crates/hwpx-package/src/document_import.rs'
ARCHIVE='implementation/p09/source-archive/p09-161-pre-source-xml-reuse-r42/source-preimages.v1.json'
PARENT=dict(path='implementation/p09/evidence/p09-160-current-graph-cost.terminal-audit-run01.v1.json',
    bytes=298999,sha256='c2aaebe924f1e2c5da90b79c259594144dbe776c66310c4be241f104a2c216a5')
TEST_MARKER='\n#[cfg(test)]\n#[path = "../tests/support/document_import_settings_inputs.rs"]\nmod source_xml_reuse_inputs;'

def require(ok,code):prior.require(ok,'XML_'+code)

def inverse(current,old):
    require(current.count(TEST_MARKER)==1,'TEST_EXTENSION')
    core,tests=current.split(TEST_MARKER)
    require(tests.count('#[test]')==4 and 'assert_eq!(count, 36)' in tests
        and 'assert!(reused == original' in tests and 'assert_eq!(new, old)' in tests,'ADDED_FOUR_ORACLES')
    wrapper='''        // One import call only: fresh ZIP/CRC/digest/profile/round-trip checks
        // still run. Move an already parsed model only after exact fresh bytes
        // match; no source read, service authorization or cross-call cache.
        let mut documents = crate::call_local_xml::CallLocalXmlDocuments::default();
        Self::import_with_documents(
            source,
            document_id,
            expected_sha256,
            limits,
            Some(&mut documents),
        )
    }

    fn import_with_documents(
        source: &[u8],
        document_id: DocumentId,
        expected_sha256: [u8; 32],
        limits: SourceImportLimits,
        mut documents: Option<&mut crate::call_local_xml::CallLocalXmlDocuments>,
    ) -> Result<Self, SourceImportError> {
'''
    preservation='''        let preservation = match documents.as_deref_mut() {
            Some(documents) => PreservationReport::build_with_call_local_xml(
                &mut reader,
                &graph,
                PackageGraphLimits::default(),
                PreservationRuleProfile::Hangul2020PreviewTextV2,
                documents,
            ),
            None => PreservationReport::build_with_profile(
                &mut reader,
                &graph,
                PreservationRuleProfile::Hangul2020PreviewTextV2,
            ),
        }
'''
    original_preservation='''        let preservation = PreservationReport::build_with_profile(
            &mut reader,
            &graph,
            PreservationRuleProfile::Hangul2020PreviewTextV2,
        )
'''
    call='''            builder.part(
                record.path(),
                record.role(),
                record.class(),
                &bytes,
                documents.as_deref_mut(),
            )?;'''
    parse='''            let xml = match documents {
                Some(documents) => documents.take_document(path.collision_key(), bytes),
                None => PreservingXmlDocument::parse(bytes),
            }
            .map_err(|_| SourceImportError::Xml)?;'''
    for added,original in (
        (wrapper,''), (preservation,original_preservation),
        (call,'            builder.part(record.path(), record.role(), record.class(), &bytes)?;'),
        ('        documents: Option<&mut crate::call_local_xml::CallLocalXmlDocuments>,\n',''),
        (parse,'            let xml = PreservingXmlDocument::parse(bytes).map_err(|_| SourceImportError::Xml)?;')):
        require(core.count(added)==1,'CLOSED_INVERSE_PATTERN');core=core.replace(added,original,1)
    require(core.rstrip('\n')==old.rstrip('\n'),'WHOLE_ORIGINAL_CORE')
    return True

def bind(q,resources):
    require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_PARENT')
    parent=q.json(PARENT['path'])
    require(parent['state']=='PASS_CURRENT_GRAPH_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE'
        and parent['source_closing_exact'] and parent['contract_tests_passed']==80
        and parent['current_Rust_input_count']==785 and parent['protected_EXE_inputs_exact']==62
        and not parent['full249_current_qualified'] and not parent['signed16_current_qualified']
        and not parent['product_complete'] and parent['P09_gate']=='OPEN','PARENT_SCOPE')
    expected=s.inputs.inventory(parent['bound_input_pins'],1272)
    archive=q.json(ARCHIVE);require(archive['baseline_closing_pin']==PARENT and len(archive['files'])==1,'ARCHIVE_SCOPE')
    item=archive['files'][0];raw=base64.b64decode(item['base64'],validate=True)
    require({k:item[k] for k in ('path','bytes','sha256')}==expected[SOURCE]
        and len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'WHOLE_PREIMAGE')
    inverse(q.text(SOURCE),raw.decode('utf-8'));expected[SOURCE]=q.pin(SOURCE)
    for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_PARENT_EXCEPT_ONE_DELTA')
    rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==785 and s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
    names,modules=p.source_scope(q,expected)
    require(names==parent['case_progress']['expected_test_names'] if 'expected_test_names' in parent['case_progress'] else len(names)==249,'SOURCE249')
    for n in (SELF,ARCHIVE,PARENT['path']):expected[n]=q.pin(n)
    return expected,names,modules
