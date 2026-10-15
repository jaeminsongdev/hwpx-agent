import copy
import unittest


class Tests(unittest.TestCase):
    def data(self):
        CHECKPOINT()
        prior=[]; rows=[]
        for i in range(1,69):
            old=dict(path=f"implementation/p09/evidence/p09-361-case112-current-runtime-run{i:03}.v1.json",bytes=100,sha256="a"*64)
            new=dict(path=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case112-runtime-run{i:03}.envelope.v1.json",bytes=50,sha256="b"*64)
            prior.append(dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=164,semantic_original_pin=old,physical_envelope_pin=new))
            rows.append(dict(prior[-1],next_case=165,physical_envelope_pin=dict(new,
                path=new["path"].replace(".envelope.v1.json",".level6.envelope.v1.json"),bytes=40,sha256="c"*64) if i<=61 else new))
        spec=dict(MODULE.SPEC,mapping_sha256=MODULE.fingerprint(rows[:61]))
        module,_=BINDINGS_API.connect(ROOT,LOADER,SCOPE,165,{},prior)
        pin=dict(path="implementation/p09/evidence/test-manifest.v1.json",bytes=1,sha256="d"*64)
        return module,prior,rows,spec,pin

    def test_full_binding_and_every_original_method(self):
        m,prior,rows,spec,pin=self.data(); methods={n:f for n,f in vars(m.Binding).items() if n!="__init__"}
        MODULE.install(m,prior,spec); bound=m.Binding(rows,pin,next_case=165)
        self.assertEqual(bound.descriptors(),rows)
        self.assertTrue(all(vars(m.Binding)[n] is f for n,f in methods.items()))
        projection,_=bound.project(SCOPE.pins([r["semantic_original_pin"] for r in rows]+[pin]),CHECKPOINT)
        self.assertEqual(len(projection.physical_pins),69)

    def test_original_table_still_uses_original_predicate(self):
        m,prior,rows,spec,pin=self.data(); MODULE.install(m,prior,spec)
        old=[dict(r,next_case=165) for r in prior]
        self.assertEqual(m.Binding(old,pin,next_case=165).descriptors(),old)
        bad=copy.deepcopy(old);bad[0]["physical_envelope_pin"]["sha256"]="e"*64
        with self.assertRaises(ValueError):m.Binding(bad,pin,next_case=165)

    def test_modified_new_hash_rejected_by_whole_digest(self):
        m,prior,rows,spec,pin=self.data(); MODULE.install(m,prior,spec)
        rows[0]["physical_envelope_pin"]["sha256"]="e"*64
        with self.assertRaises(ValueError):m.Binding(rows,pin,next_case=165)

    def test_partial_table_and_changed_original_rejected(self):
        for field in ("partial","original"):
            m,prior,rows,spec,pin=self.data(); MODULE.install(m,prior,spec)
            if field=="partial": rows.pop()
            else: rows[0]["semantic_original_pin"]=dict(rows[0]["semantic_original_pin"],sha256="f"*64)
            with self.assertRaises(ValueError):m.Binding(rows,pin,next_case=165)

    def test_current_and_failed_new_paths_rejected(self):
        for kind in ("current","failed"):
            m,prior,rows,spec,pin=self.data(); MODULE.install(m,prior,spec)
            if kind=="current":rows[0]["semantic_original_pin"]=dict(rows[0]["semantic_original_pin"],path="implementation/p09/evidence/p09-361-case165-current-runtime-run002.v1.json")
            else:rows[0]["physical_envelope_pin"]=dict(rows[0]["physical_envelope_pin"],path=rows[0]["physical_envelope_pin"]["path"].replace(".level6.",".failed.level6."))
            with self.assertRaises(ValueError):m.Binding(rows,pin,next_case=165)

    def test_private_namespace_and_profile_context(self):
        from types import SimpleNamespace
        class Projection:
            def __init__(self):pass
        with self.assertRaises(ValueError):MODULE.install(SimpleNamespace(source=SimpleNamespace(Projection=Projection)),[],MODULE.SPEC)
        m,prior,rows,spec,pin=self.data()
        with self.assertRaises(ValueError):MODULE.install(m,prior,dict(spec,index=True))

    def test_one_idempotent_profile(self):
        m,prior,rows,spec,pin=self.data(); MODULE.install(m,prior,spec); original=m.Binding.__init__
        MODULE.install(m,prior,spec);self.assertIs(original,m.Binding.__init__)
        with self.assertRaises(ValueError):MODULE.install(m,prior,dict(spec,mapping_sha256="f"*64))

    def test_independent_selection_rejects_changed_semantics(self):
        m,prior,rows,spec,pin=self.data(); old=[dict(r,next_case=165) for r in prior]
        # Ordinary projection is exact and table-complete, not a partial cache.
        allnew=[dict(r,physical_envelope_pin=dict(r["physical_envelope_pin"],path=r["physical_envelope_pin"]["path"].replace(".envelope.v1.json",".level6.envelope.v1.json"))) for r in old]
        selectedspec=dict(spec,count=68,mapping_sha256=MODULE.fingerprint(allnew))
        self.assertEqual(MODULE.choose(old,allnew,selectedspec),allnew)
        allnew[0]["semantic_original_pin"]=dict(allnew[0]["semantic_original_pin"],bytes=99)
        with self.assertRaises(ValueError):MODULE.choose(old,allnew,selectedspec)

    def test_one_scoped_seed_then_only_full_binding(self):
        m,prior,rows,spec,pin=self.data();MODULE.install(m,prior,spec)
        full=m.Binding.__init__
        with MODULE.bootstrap_seed(m,rows[0],pin):
            self.assertEqual(len(m.Binding([rows[0]],pin,next_case=165).descriptors()),1)
            with self.assertRaises(ValueError):m.Binding([rows[0]],pin,next_case=165)
            self.assertEqual(len(m.Binding(rows,pin,next_case=165).descriptors()),68)
        self.assertIs(m.Binding.__init__,full)
        with self.assertRaises(ValueError):m.Binding([rows[0]],pin,next_case=165)

    def test_wrong_seed_or_unused_seed_fails_and_restores(self):
        for wrong in (True,False):
            m,prior,rows,spec,pin=self.data();MODULE.install(m,prior,spec);full=m.Binding.__init__
            with self.assertRaises(ValueError):
                with MODULE.bootstrap_seed(m,rows[0],pin):
                    if wrong:m.Binding([rows[1]],pin,next_case=165)
            self.assertIs(m.Binding.__init__,full)
