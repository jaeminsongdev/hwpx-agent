import copy,json,sys,unittest
from pathlib import Path
from xml.etree import ElementTree as E
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import block_bookmark_xml672 as m

def fixture():
    root=E.Element('{'+m.HS+'}sec')
    for i,c in enumerate(m.cases()):
        p=E.SubElement(root,'{'+m.HP+'}p');r=E.SubElement(p,'{'+m.HP+'}run')
        s=c['selection'];prefix=c['seed_text'][:s['spos']];suffix=c['seed_text'][s['epos']:]
        E.SubElement(r,'{'+m.HP+'}t').text=prefix
        ctrl=E.SubElement(r,'{'+m.HP+'}ctrl')
        begin=E.SubElement(ctrl,'{'+m.HP+'}fieldBegin',id=str(i+1),type='BOOKMARK',name=c['bookmark_name'],editable='0',dirty='1',zorder='-1',fieldid='777')
        param=E.SubElement(begin,'{'+m.HP+'}parameters',cnt='1',name='')
        E.SubElement(param,'{'+m.HP+'}integerParam',name='Prop').text='2'
        E.SubElement(r,'{'+m.HP+'}t').text=c['selected_text']
        ctrl=E.SubElement(r,'{'+m.HP+'}ctrl');E.SubElement(ctrl,'{'+m.HP+'}fieldEnd',beginIDRef=str(i+1),fieldid='777')
        E.SubElement(r,'{'+m.HP+'}t').text=suffix
    return root

class Tests(unittest.TestCase):
    def setUp(self):self.root=fixture()
    def deny(self):
        with self.assertRaises(ValueError):m.read_section(E.tostring(self.root))
    def first(self,name):return next(e for e in self.root.iter()if e.tag=='{'+m.HP+'}'+name)
    def test_all_eight_including_hangul_escaping_and_shared_fieldid(self):
        rows=m.read_section(E.tostring(self.root));self.assertEqual(len(rows),8)
        self.assertEqual(len({v['native_fieldid']for v in rows}),1)
        self.assertEqual(len({v['native_begin_id']for v in rows}),8)
        self.assertTrue(all(not r['raw_text_present']for r in rows))
    def test_name_drift(self):self.first('fieldBegin').set('name','different');self.deny()
    def test_prop_drift(self):self.first('integerParam').text='1';self.deny()
    def test_shared_fieldid_cannot_replace_begin_binding(self):self.first('fieldEnd').set('beginIDRef','777');self.deny()
    def test_duplicate_begin(self):
        begins=[e for e in self.root.iter()if e.tag.endswith('fieldBegin')];begins[1].set('id','1');self.deny()
    def test_wrong_namespace(self):self.first('fieldBegin').tag='{wrong}fieldBegin';self.deny()
    def test_changed_selected_text(self):
        texts=[e for e in self.root[0].iter()if e.tag.endswith('}t')];texts[1].text='wrong';self.deny()
    def test_missing_paragraph(self):self.root.remove(self.root[-1]);self.deny()
    def test_missing_end(self):
        for ctrl in self.root[0][0]:
            if len(ctrl)and ctrl[0].tag.endswith('fieldEnd'):ctrl.remove(ctrl[0]);break
        self.deny()
    def test_extra_parameter(self):E.SubElement(self.first('parameters'),'{'+m.HP+'}integerParam',name='Extra').text='2';self.deny()
    def test_plaintext_child_control_rejected(self):E.SubElement(self.first('t'),'{'+m.HP+'}lineBreak');self.deny()
    def test_dtd_rejected(self):
        with self.assertRaises(ValueError):m.read_section(b'<!DOCTYPE x>'+E.tostring(self.root))

if __name__=='__main__':
    result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),
        failed_tests=[t.id()for t,_ in result.errors+result.failures],actual_native_started=False)))
    raise SystemExit(0 if result.wasSuccessful()else 2)
