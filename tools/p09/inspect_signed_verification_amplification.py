"""Fresh-source-bound static call amplification, NOT a runtime profiler or Gate.

현재 signed consumer의 닫힌 함수/호출 증거만 읽는다. 조건부 성공 경로의
호출 모델을 실제 횟수·CPU 비용으로 승격하거나 fresh 검사를 제거하지 않는다.
"""
import argparse
import collections
import io
import json
import re
import unittest
from unittest.mock import patch

from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from conservative_maintenance import require

SELF = 'tools/p09/inspect_signed_verification_amplification.py'
TEST = 'tools/p09/tests/test_signed_verification_amplification.py'
RAW_START = re.compile(r'r(#{0,16})"')
CHAR_LITERAL = re.compile(r"'(?:[^'\\\r\n]|\\[^\r\n])'")
PARENT = {'path':'implementation/p09/evidence/p09-149-signed-artifact-compute.summary-run01.v1.json',
    'bytes':11037,'sha256':'080ccd35959d4c5745fa9eb801ae17f5baa46081e06a38286e7b519dd15b40b7'}
ISSUER = 'crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/product.rs'
POLICY = 'crates/product-cli/src/form_product_request/stored_operations/policy.rs'
FORMULA = 'crates/product-cli/src/form_product_request/stored_operations/formula.rs'
DATA = 'crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs'
SIGNED = 'crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/provider.rs'
OUTPUT = 'crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output.rs'
SOURCE = 'crates/product-cli/src/form_stored_provider/actual_import.rs'
FORMS = 'crates/hwpx-package/src/document_import/forms.rs'

# edge: exact whitespace-normalized direct call, target, lexical multiplicity.
# P.route -> D.verify is AFTER the currently denied original route. It is recorded
# but excluded from the conditional Changed/current-denial model, not deleted.
SPECS = {
    'I.consume':(ISSUER,'with_verified_bytes',(('self.verify(','I.verify',1),('self.product.with_verified_bytes(','P.consume',1))),
    'I.route':(ISSUER,'require_current_product_route',(('self.verify(','I.verify',1),('self.product.require_current_product_route(','P.route',1))),
    'I.verify':(ISSUER,'verify',(('self.product.verify(','P.verify',1),)),
    'P.consume':(POLICY,'with_verified_bytes',(('self.verify(','P.verify',1),('self.product.with_verified_bytes(','F.consume',1),('self.policy.verify(','D.verify',1))),
    'P.route':(POLICY,'require_current_product_route',(('self.verify(','P.verify',1),('self.product.require_current_product_route(','F.route',1),('self.policy.verify(','D.verify',1))),
    'P.verify':(POLICY,'verify',(('self.product.verify(','F.verify',1),('self.policy.verify(','D.verify',2))),
    'F.consume':(FORMULA,'with_verified_bytes',(('self.verify(','F.verify',1),)),
    'F.route':(FORMULA,'require_current_product_route',(('self.verify(','F.verify',1),)),
    'F.verify':(FORMULA,'verify',(('build(','F.build',1),)),
    'F.build':(FORMULA,'build',()),
    'D.verify':(DATA,'verify',(('source.bind_stored_formula_policy(','D.bind',1),)),
    'D.bind':(DATA,'bind_stored_formula_policy',(('repository.read_current_formula_policy(','S.read',2),)),
    'S.read':(SIGNED,'read_current_formula_policy',(('self.read_signed(','S.signature',1),)),
    'S.signature':(SIGNED,'read_signed',()),
}
SOURCE_NAMES = {row[0] for row in SPECS.values()}|{OUTPUT,SOURCE,FORMS}


def code_mask(text):
    """Mask literals/comments without moving offsets; reject unterminated inputs.

    This is a bounded lexical extractor for the closed sources, not a Rust AST.
    Character literals are distinguished from lifetimes; raw strings and nested
    block comments cannot introduce fake fn/call/braces into the observation.
    """
    require(isinstance(text,str) and len(text.encode()) <= 16*1024*1024,'CALL_MODEL_TEXT_BUDGET')
    chars=list(text);i=0
    def hide(a,b):
        chars[a:b]=['\n' if c=='\n' else ' ' for c in text[a:b]]
    while i<len(text):
        start=i
        if text.startswith('//',i):
            end=text.find('\n',i);i=len(text) if end<0 else end;hide(start,i);continue
        if text.startswith('/*',i):
            depth=1;i+=2
            while i<len(text) and depth:
                if text.startswith('/*',i):depth+=1;i+=2
                elif text.startswith('*/',i):depth-=1;i+=2
                else:i+=1
            require(depth==0,'CALL_MODEL_UNTERMINATED_COMMENT');hide(start,i);continue
        raw=RAW_START.match(text,i) if text[i]=='r' else None
        if raw:
            end=text.find('"'+raw[1],i+len(raw[0]));require(end>=0,'CALL_MODEL_UNTERMINATED_RAW')
            i=end+1+len(raw[1]);hide(start,i);continue
        if text[i]=='"':
            i+=1;closed=False
            while i<len(text):
                if text[i]=='\\':i+=2
                elif text[i]=='"':i+=1;closed=True;break
                else:i+=1
            require(closed,'CALL_MODEL_UNTERMINATED_STRING');hide(start,i);continue
        if text[i]=="'":
            char=CHAR_LITERAL.match(text,i)
            if char:i+=len(char[0]);hide(start,i);continue
        i+=1
    return ''.join(chars)


def function(text,name):
    require(isinstance(name,str) and re.fullmatch(r'[a-z_]+',name),'CALL_MODEL_FUNCTION_NAME')
    masked=code_mask(text)
    matches=list(re.finditer(r'\bfn\s+'+name+r'\b',masked))
    require(len(matches)==1,'CALL_MODEL_FUNCTION_AMBIGUOUS_OR_MISSING')
    start=matches[0].start();opening=masked.find('{',matches[0].end())
    semicolon=masked.find(';',matches[0].end())
    require(opening>=0 and (semicolon<0 or opening<semicolon),'CALL_MODEL_BODY_REQUIRED')
    depth=1;end=opening+1
    while end<len(masked) and depth:
        depth += (masked[end]=='{')-(masked[end]=='}');end+=1
    require(depth==0,'CALL_MODEL_UNTERMINATED_BODY')
    return {'start':start,'end':end,'line':text.count('\n',0,start)+1,
        'code':masked[opening+1:end-1]}


def call_count(body,needle):
    require(isinstance(needle,str) and needle.endswith('('),'CALL_MODEL_CALL_SHAPE')
    # Receiver/function tokens are closed; identifier substrings cannot match.
    boundary='' if needle.startswith('.') else r'(?<![a-zA-Z0-9_])'
    pattern=re.escape(needle).replace(r'\.',r'\s*\.\s*').replace(r'\(',r'\s*\(')
    return len(re.findall(boundary+pattern,body))


def expand(graph,root):
    require(type(graph) is dict and 1<=len(graph)<=32 and root in graph,'CALL_MODEL_GRAPH_SCOPE')
    total=collections.Counter();steps=0
    def walk(node,weight,ancestors):
        nonlocal steps
        steps+=1
        require(steps<=4096 and node in graph and node not in ancestors and len(ancestors)<32,'CALL_MODEL_CYCLE_OR_BUDGET')
        total[node]+=weight
        require(type(graph[node]) is list,'CALL_MODEL_EDGE_SHAPE')
        for target,multiplicity in graph[node]:
            require(type(multiplicity) is int and 1<=multiplicity<=8,'CALL_MODEL_MULTIPLICITY')
            walk(target,weight*multiplicity,(*ancestors,node))
    walk(root,1,())
    return dict(sorted(total.items()))


def inspect(texts):
    require(type(texts) is dict and set(texts)==SOURCE_NAMES,'CALL_MODEL_SOURCE_SET')
    graph={};observations=[];bodies={}
    for node,(path,name,edges) in SPECS.items():
        body=function(texts[path],name);bodies[node]=body['code'];graph[node]=[]
        observed=[]
        for needle,target,count in edges:
            require(call_count(body['code'],needle)==count,'CALL_MODEL_DIRECT_CALL_DRIFT')
            observed.append({'call':needle,'target':target,'lexical_sites':count})
            graph[node].append((target,count))
        observations.append({'node':node,'path':path,'function':name,'line':body['line'],'direct_calls':observed})
    # Closed source witnesses for the route's further Changed pipeline and denial.
    for needle in ('.import_field_ranges(','.import_semantics(','.evaluate_table_formulas(','.prepare_results(','results.compile(','plan.require_current_product_route('):
        require(call_count(bodies['F.route'],needle)==1,'CALL_MODEL_CHANGED_ROUTE_PIPELINE_DRIFT')
    denied=function(texts[OUTPUT],'require_current_product_route')['code']
    require('Err(StoredFormulaOutputError::RouteUnqualified)' in re.sub(r'\s+','',denied),'CALL_MODEL_ROUTE_DENIAL_DRIFT')
    require(call_count(bodies['S.signature'],'UnparsedPublicKey::new(')==1,'CALL_MODEL_SIGNATURE_SITE_DRIFT')
    # The only excluded edge is witnessed below the ?-propagated current denial.
    route=re.sub(r'\s+','',bodies['P.route'])
    require(route.index('self.product.require_current_product_route(')<route.index('self.policy.verify('),'CALL_MODEL_POST_DENIAL_EDGE_ORDER')
    graph['P.route']=[edge for edge in graph['P.route'] if edge[0]!='D.verify']
    consume=expand(graph,'I.consume');route_counts=expand(graph,'I.route')
    require(consume['F.build']==3 and consume['S.signature']==10 and route_counts['F.build']==3 and route_counts['S.signature']==8,'CALL_MODEL_DERIVATION_DRIFT')
    reconstruction=function(texts[SOURCE],'fresh_source_reconstructed')
    form_reconstruction=function(texts[FORMS],'reconstruct_source_for_verification')
    form_rebuild=function(texts[FORMS],'rebuild_for_verification')
    for body,needle in ((reconstruction['code'],'provider.source('),(reconstruction['code'],'.reconstruct_source_for_verification('),
            (reconstruction['code'],'provider.check_head('),(form_reconstruction['code'],'self.rebuild_for_verification('),
            (form_rebuild['code'],'ImportedSourcePackage::import('),(form_rebuild['code'],'Self::import('),(form_rebuild['code'],'self.verify_rebuilt(')):
        require(call_count(body,needle)==1,'CALL_MODEL_FRESH_RECONSTRUCTION_WITNESS_DRIFT')
    return {'qualification':'CONDITIONAL_STATIC_CALL_MODEL_NOT_RUNTIME_COUNT_OR_CPU_PROFILE',
        'assumptions':['All preceding fresh verification checks succeed',
            'consume callback is reached exactly once','Changed plan reaches current output route denial'],
        'functions':observations,'candidate_consume':consume,'changed_route_denial':route_counts,
        'excluded_post_denial_edge':{'from':'P.route','to':'D.verify','lexical_sites':1,'source_not_modified':True},
        'extra_changed_route_pipeline_is_not_in_F_build_count':True,
        'runtime_call_counts_proven':False,'CPU_hot_function_proven':False,
        'fresh_checks_can_be_removed':False,'authority_cache_authorized':False,
        'reconstruction_source_witness':{'source_path':SOURCE,'source_function':'fresh_source_reconstructed','source_line':reconstruction['line'],
            'fresh_service_source_call':1,'whole_bytes_reconstruction_call':1,'head_check_call':1,
            'forms_path':FORMS,'form_rebuild_function':'rebuild_for_verification','form_rebuild_line':form_rebuild['line'],
            'fresh_package_import_call':1,'form_import_call':1,'whole_rebuilt_comparison_call':1,
            'sealed_IR_JSON_decode_proven_selected_here':False,'runtime_multiplicity_of_reconstruction_unmeasured':True},
        'next_measurement_targets':['F.build actual source/ranges/semantics/evaluation/output/compiler',
            'D.bind source reconstruction/target semantic binding versus S.signature',
            'F.route extra Changed result/compiler verification']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--light',action='store_true');args=parser.parse_args()
    suffix='light' if args.light else 'actual'
    destination=scoped_path(f'implementation/p09/evidence/p09-149-signed-call-model.{suffix}-run{args.run:02}.v1.json',fresh=True)
    resources=SQLRuntimeResources();resources.admit();reader=LiveSQLReader(resources)
    row={'schema_version':1,'product_complete':False,'P09_gate':'OPEN','goal_status':'active',
        'Cargo_SQL_native_or_new_thread_started':False,'source_or_auth_checks_changed':False}
    try:
        with patch('subprocess.Popen',side_effect=AssertionError('CALL_MODEL_CHILD_FORBIDDEN')),patch('subprocess.run',side_effect=AssertionError('CALL_MODEL_CHILD_FORBIDDEN')),patch('threading.Thread.start',side_effect=AssertionError('CALL_MODEL_THREAD_FORBIDDEN')):
            row['helper_pins']=[reader.pin(n) for n in (SELF,TEST)]
            if args.light:
                from tests.test_signed_verification_amplification import SignedVerificationAmplificationTests
                result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(SignedVerificationAmplificationTests))
                failed=sorted({test.id().split('.')[-1] for test,_ in result.failures+result.errors+result.skipped})
                passed=result.testsRun==21 and result.wasSuccessful() and not result.skipped
                row.update(state='PASS_CALL_MODEL_CONTRACT_ONLY' if passed else 'FAILED_NOT_ACCEPTED',tests_run=result.testsRun,tests_passed=result.testsRun-len(failed),failed_tests=failed)
            else:
                require(reader.pin(PARENT['path'])==PARENT,'CALL_MODEL_PARENT_PIN_DRIFT')
                parent=reader.json(PARENT['path'])
                require(parent['source_closing_exact'] is True and parent['execution_source_freezes_current_exact'] is True
                    and parent['P09_gate']=='OPEN' and parent['product_complete'] is False,'CALL_MODEL_PARENT_SCOPE')
                actual_pin=next(p for p in parent['support_pins'] if p['path'].endswith('.actual-run01.v1.json'))
                require(reader.pin(actual_pin['path'])==actual_pin,'CALL_MODEL_RUNTIME_PIN_DRIFT')
                prior=reader.json(actual_pin['path']);frozen={p['path']:p for p in prior['source_freeze']}
                require(prior['state']=='STOPPED_NOT_ACCEPTED' and prior['stop_reason']=='STOP_DURATION_LIMIT','CALL_MODEL_RUNTIME_NOT_COMPLETE')
                row['source_pins']=[];texts={}
                for name in sorted(SOURCE_NAMES):
                    pin=reader.pin(name);require(pin==frozen[name],'CALL_MODEL_SOURCE_DRIFT')
                    row['source_pins'].append(pin);texts[name]=reader.text(name)
                row.update(state='PASS_CURRENT_SOURCE_STATIC_CALL_MODEL_ONLY_NOT_RUNTIME_OR_GATE',parent_pin=PARENT,
                    prior_actual_pin=actual_pin,model=inspect(texts),runtime_replayed=False)
            reader.finish();row['source_closing_exact']=True;row['IO']=reader.summary()
    finally:
        row['resource_stop']=resources.reason;finish_watcher(resources,row)
    require(row['resource_stop'] is None and row['resource_watcher_cleanup_confirmed'],'CALL_MODEL_RESOURCE_STOP')
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','P09_gate','source_closing_exact')}))
    return 0 if row['state'].startswith('PASS_') else 2


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[A-Z_]+',str(error)) else 'CALL_MODEL_OPERATION_FAILED'
        print(json.dumps({'state':'FAILED_NOT_ACCEPTED','error_code':code}))
        raise SystemExit(2) from None
