"""Preserve209 compile/test0. Change only helper visibility/generic types; execute the original50."""
import run_style_splice_inventory_components as base
OUTPUT='implementation/p09/evidence/p09-361-style-splice-inventory-recovery210.v1.json'
FAILED=base.OUTPUT
DRIVER='tools/p09/run_style_splice_inventory_recovery.py'
ORIGINAL_INVERSE=base.inverse
NEW_SIGNATURE='''fn take<R,B,S,V,T>(out:&Operation,p:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&Inventory)->T)->Result<T,Box<dyn Error>>
where R:artifact_service::ArtifactMetadataRepository,B:artifact_service::EncryptedBlobStore,S:artifact_service::ArtifactScanner,V:rev::RevisionRepository {
'''
OLD_SIGNATURE='fn take<T>(out:&Operation,p:&Provider<\'_>,now:u64,consume:impl FnOnce(&Inventory)->T)->Result<T,Box<dyn Error>> {\n'
OLD_ZIP='    let mut old_zip=hwpx_package::BoundedZipReader::open(Cursor::new(bytes),Default::default())?;\n'
NEW_ACCESS='''        let old_index=old_zip.entries().iter().position(|e|e.path.as_str()==path).ok_or("source part")?;let old=old_zip.read_entry(old_index)?;
        let _xml=part.xml().ok_or("xml")?;let(mut a,mut b)=(0,0);
'''
OLD_ACCESS='        part.xml().ok_or("xml")?.with_source_bytes(|old|->TestResult {let(mut a,mut b)=(0,0);\n'
NEW_END='            }assert_eq!(old.get(a..),new.get(b..));\n'
OLD_END='            }assert_eq!(old.get(a..),new.get(b..));Ok(())})?;\n'


def inverse(q,old):
    ORIGINAL_INVERSE(q,old)
    failed=q.json(FAILED)
    base.c.require(q.snapshots[FAILED]['sha256']=='cb2d80233f4634c37407640ac84ccec6dd1862816b698db9841ce61ab9bdf38e'
        and failed['cleanup']and failed['steps'][0]['exit_code']==101 and failed['steps'][0]['tests']==[],
        'ORIGINAL209_COMPILE_FAILURE_TEST0_AND_TERMINAL_CLEANUP_PRESERVED')
    before={p['path']:p for p in failed['source_pins']}
    for name in sorted(before):
        if name==base.TEST:continue
        q.pin(name);base.c.require(q.snapshots[name]==before[name],'ALL209_PRODUCTION_CODE_AND_OTHER_TEST_FIXTURES_UNCHANGED')
    text=q.text(base.TEST)
    for marker in (NEW_SIGNATURE,OLD_ZIP,NEW_ACCESS,NEW_END):base.c.require(text.count(marker)==1,'ONLY_TWO_TEST_HELPER_REPAIRS_UNIQUE')
    restored=text.replace(NEW_SIGNATURE,OLD_SIGNATURE).replace(OLD_ZIP,'').replace(NEW_ACCESS,OLD_ACCESS).replace(NEW_END,OLD_END)
    base.audit.inverse(restored,before[base.TEST],'ALL12_NEW_AND38_OLD_REQUIREMENTS_AND_TEST_BODIES_PRESERVED_EXCEPT_PUBLIC_READER_AND_REPOSITORY_GENERIC_HELPERS')


base.OUTPUT=OUTPUT
base.NEW=base.NEW|{DRIVER}
base.inverse=inverse
if __name__=='__main__':raise SystemExit(base.main())
