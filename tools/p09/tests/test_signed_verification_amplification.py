import unittest
from unittest.mock import patch
import inspect_signed_verification_amplification as s


class SignedVerificationAmplificationTests(unittest.TestCase):
    def test_literal_scanners_use_original_text_and_offset_not_suffix_copies(self):
        text="fn call<'a>() { let raw=r#\"} fake();\"#; let c='}'; real(); }"
        seen=[]
        class Probe:
            def __init__(self,pattern):self.pattern=pattern
            def match(self,source,position):
                seen.append((source is text,position))
                return self.pattern.match(source,position)
        with patch.object(s,'RAW_START',Probe(s.RAW_START)),patch.object(s,'CHAR_LITERAL',Probe(s.CHAR_LITERAL)):
            body=s.function(text,'call')
        self.assertGreaterEqual(len(seen),3)
        self.assertTrue(all(same and position>0 for same,position in seen))
        self.assertEqual(s.call_count(body['code'],'fake('),0)
        self.assertEqual(s.call_count(body['code'],'real('),1)

    def fixtures(self):
        texts={name:'' for name in s.SOURCE_NAMES}
        for node,(path,name,edges) in s.SPECS.items():
            calls=[needle+');' for needle,_target,count in edges for _ in range(count)]
            if node=='F.route':
                calls += [needle+');' for needle in ('.import_field_ranges(','.import_semantics(','.evaluate_table_formulas(','.prepare_results(','results.compile(','plan.require_current_product_route(')]
            if node=='S.signature':calls.append('UnparsedPublicKey::new();')
            texts[path]+='fn '+name+'(){ '+ ' '.join(calls)+' }\n'
        texts[s.OUTPUT]='fn require_current_product_route(){ Err(StoredFormulaOutputError::RouteUnqualified) }'
        texts[s.SOURCE]='fn fresh_source_reconstructed(){ provider.source(); self.imported.reconstruct_source_for_verification(); provider.check_head(); }'
        texts[s.FORMS]='fn reconstruct_source_for_verification(){ self.rebuild_for_verification(); }\nfn rebuild_for_verification(){ ImportedSourcePackage::import(); Self::import(); self.verify_rebuilt(); }'
        return texts

    def test_complete_closed_model_derives_counts_without_runtime_claim(self):
        model=s.inspect(self.fixtures())
        self.assertEqual(model['candidate_consume']['F.build'],3)
        self.assertEqual(model['candidate_consume']['S.signature'],10)
        self.assertEqual(model['changed_route_denial']['F.build'],3)
        self.assertEqual(model['changed_route_denial']['S.signature'],8)
        self.assertFalse(model['runtime_call_counts_proven'])
        self.assertFalse(model['fresh_checks_can_be_removed'])

    def test_whole_model_rejects_missing_fresh_check(self):
        texts=self.fixtures();texts[s.SOURCE]=texts[s.SOURCE].replace('provider.check_head();','')
        with self.assertRaises(ValueError):s.inspect(texts)

    def test_extracts_one_generic_function_with_lifetimes(self):
        self.assertIn('self.verify',s.function("fn consume<'a,T>(&'a self) { self.verify(); }",'consume')['code'])

    def test_comments_do_not_create_functions_or_calls(self):
        body=s.function('// fn call() {}\nfn call() { /* fake(); */ real(); }','call')
        self.assertEqual(s.call_count(body['code'],'fake('),0)
        self.assertEqual(s.call_count(body['code'],'real('),1)

    def test_nested_comments_are_masked(self):
        self.assertEqual(s.code_mask('/* fn x() { /* } */ } */').strip(),'')

    def test_raw_string_braces_and_calls_are_not_code(self):
        body=s.function('fn call(){ let x=r##" } fake(); fn call(){} "##; real(); }','call')
        self.assertEqual(s.call_count(body['code'],'fake('),0)
        self.assertEqual(s.call_count(body['code'],'real('),1)

    def test_escaped_quotes_are_not_body_boundaries(self):
        body=s.function('fn call(){ let x="\\\" } fake();"; real(); }','call')
        self.assertEqual(s.call_count(body['code'],'fake('),0)

    def test_character_braces_do_not_change_depth(self):
        self.assertIn('real()',s.function("fn call(){ let x='}'; real(); }",'call')['code'])

    def test_duplicate_function_names_fail_closed(self):
        with self.assertRaises(ValueError):s.function('fn call(){} fn call(){}','call')

    def test_missing_function_fails_closed(self):
        with self.assertRaises(ValueError):s.function('fn other(){}','call')

    def test_trait_declaration_does_not_borrow_next_body(self):
        with self.assertRaises(ValueError):s.function('trait X { fn call(); } fn other(){}','call')

    def test_unterminated_body_fails_closed(self):
        with self.assertRaises(ValueError):s.function('fn call(){','call')

    def test_unterminated_literal_or_comment_fails_closed(self):
        for text in ('/*','"abc','r##"abc'):
            with self.assertRaises(ValueError):s.code_mask(text)

    def test_whitespace_normalized_call_count_has_token_boundary(self):
        self.assertEqual(s.call_count('myself.product.verify(); self\n .product\n .verify();','self.product.verify('),1)

    def test_method_suffix_matches_actual_named_receiver(self):
        self.assertEqual(s.call_count('source.import_field_ranges(); source.import_field_ranges_extra();','.import_field_ranges('),1)

    def test_keyword_boundary_is_preserved(self):
        body='let before = repository.read_current_formula_policy(); if repository\n .read_current_formula_policy() != before { return Err(()); }'
        self.assertEqual(s.call_count(body,'repository.read_current_formula_policy('),2)

    def test_static_edge_multiplicity_propagates(self):
        graph={'root':[('middle',3)],'middle':[('leaf',2)],'leaf':[]}
        self.assertEqual(s.expand(graph,'root'),{'leaf':6,'middle':3,'root':1})

    def test_cycles_and_missing_nodes_are_denied(self):
        for graph in ({'a':[('a',1)]},{'a':[('b',1)]}):
            with self.assertRaises(ValueError):s.expand(graph,'a')

    def test_boolean_zero_and_unbounded_multiplicity_are_denied(self):
        for count in (True,0,9):
            with self.assertRaises(ValueError):s.expand({'a':[('b',count)],'b':[]},'a')

    def test_unexpected_source_set_is_not_accepted(self):
        with self.assertRaises(ValueError):s.inspect({})
