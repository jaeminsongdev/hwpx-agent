"""P304: 수용101 exact compound anchor 뒤 미수용102부터 한 사례씩.
이미통과한 본체/Native source 재실행 없음. 기존1486 계약은 불변 pin으로 재사용(이번 실행횟수 아님).
원 Job/CPU/RAM/600/720/두전체 byte/Nativeidentity/cleanup 보존.
"""
import argparse
import copy
import hashlib
import io
import json
import re
import sys
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch
import accept_completed101_leading_metadata_compound as accepted
import leading_metadata_entry_pressure as leading
m=accepted.m;p=m.p;g=m.g;r=m.r
profile=m.profile;connection=m.connection;review=m.review;early_review=m.early_review
SELF='tools/p09/resume_completed101_compound_runtime.py'
TEST='tools/p09/tests/test_completed101_compound_runtime.py'
ANCHOR={"path":"implementation/p09/evidence/locked-r07/p302-case101-leading-metadata-compound-run01.v1.json","bytes":144055,"sha256":"173d2e27a1b93ee3a2312a61f33298e5e53fd779d04bb2cc59523dad3e0b41d8"}
RETAINED_QUALIFIER={"path":"implementation/p09/evidence/locked-r07/p291-light-run001.v1.json","bytes":52978,"sha256":"6e9131e24aefc275d98adb1932ec3e3b942143de04875f6e0fe03aaec4308037"}
FROZEN66=[{"path":"tools/p09/sync_monotonic_compound_runtime_documents.py","bytes":10144,"sha256":"51d62391ac25127dc74e4dfea4a0c0251e61aa531d1dca37d649a0c9491d39ee"},{"path":"tools/p09/tests/test_monotonic_compound_runtime_documents.py","bytes":4379,"sha256":"a4ea2694b3865ea687ced73fbb5276f5351d9e7d9614ae3185e19828d46902de"},{"path":"tools/p09/review_rejected_parent_diagnostic.py","bytes":17531,"sha256":"3c16e19b45ab0b596f1bf6d98fab627922ca936ed91d5495ebb2768186012d19"},{"path":"tools/p09/tests/test_rejected_parent_diagnostic.py","bytes":9476,"sha256":"d467245eb018e2a38677d8d70ba4b847d8b22bea9ab8916bcacc829592345f59"},{"path":"tools/p09/qualify_rejected_parent_connection.py","bytes":16511,"sha256":"2d8a4d5c1eca7177ac739175dfb800c10d7ac8ee8c00f63cb93119004d8d3fea"},{"path":"tools/p09/tests/test_rejected_parent_connection.py","bytes":12764,"sha256":"4307cf4de757cb0776a5574843f2f425d4e991494a3c469e667733ed79cf324f"},{"path":"tools/p09/qualify_rejected_parent_connection_r2.py","bytes":22123,"sha256":"aa5eedf38ba1c816bb85d5b23cb584320a48fbdbdfb12d66da965302c05c4efe"},{"path":"tools/p09/tests/test_rejected_parent_connection_r2.py","bytes":4220,"sha256":"26b4e247a4f03fdbdf1a5be24f14c1f7949fba6c63ab8dfcf9c7226cd76f5f95"},{"path":"tools/p09/qualify_early_metadata_pressure.py","bytes":9146,"sha256":"f11f1ffee387d026d26dc3e6bb95aa12a75793dd0ce10b30bd4b85a6a98368d0"},{"path":"tools/p09/tests/test_early_metadata_pressure.py","bytes":7347,"sha256":"9791d2fe4de3df7a6dfca3848b80379c3f092a455b8ecd079ae7c21731801b9b"},{"path":"tools/p09/resume_diagnostic_guarded_runtime.py","bytes":28992,"sha256":"1349828826373ac0c8cdb520fcf96010ec2b9f60a10ab8bee9976a5d3fb82bde"},{"path":"tools/p09/tests/test_diagnostic_guarded_runtime.py","bytes":3058,"sha256":"28dbfb74efdbc147996a4d57e2927b67bd1fc7a57eb409a3f6adc9119523de04"},{"path":"tools/p09/resume_diagnostic_guarded_runtime_r2.py","bytes":31309,"sha256":"7e25e6a576cdb55961f4a89bd3894ce200ead4803446588cd960c7b3e752cce2"},{"path":"tools/p09/tests/test_diagnostic_guarded_runtime_r2.py","bytes":4537,"sha256":"5617f036d15bfe1339278284adda5fe4de7483c7896b83898ac869891d94f109"},{"path":"tools/p09/resume_diagnostic_guarded_runtime_r3.py","bytes":33681,"sha256":"bb63c8268ba9e5549e9e848ddabc2818d679ce735b33f32e3cccb17802314a64"},{"path":"tools/p09/tests/test_diagnostic_guarded_runtime_r3.py","bytes":5945,"sha256":"5f62854da975611ba4b281713ccaad650b924a6b0d83996e679daf37e6315425"},{"path":"tools/p09/qualify_acquisition_phase_pressure.py","bytes":17050,"sha256":"b9fd030f1b4d1526b5d7bd21bf095ebf906e2cce0d4cd4e11919a147fd3b2813"},{"path":"tools/p09/tests/test_acquisition_phase_pressure.py","bytes":8666,"sha256":"c5db68b6e5aae547da1536e0c4bd758435cbc091c81b5a0ca2c9246ea0ee5912"},{"path":"tools/p09/qualify_acquisition_phase_pressure_r2.py","bytes":14022,"sha256":"5eef3170b4541e4978447c47056aa3bc4e733e7e7f83899144cb22237dade897"},{"path":"tools/p09/tests/test_acquisition_phase_pressure_r2.py","bytes":2595,"sha256":"06e4ca875ec375fcb01aaed8d6561b8c987503b7c7966ffaf81ecb603105512e"},{"path":"implementation/p09/evidence/preflight-controller-snapshots/p276-literal-reader-interface-run01/qualify_acquisition_phase_pressure_r2.py","bytes":11370,"sha256":"fa7a56d3421251e850e2115818f18b83f650f2805b14d1847c8795390b8c3a4f"},{"path":"implementation/p09/evidence/preflight-controller-snapshots/p276-literal-reader-interface-run01/test_acquisition_phase_pressure_r2.py","bytes":1991,"sha256":"26892e96827b12d3f8bedb7b14b748f54f1ef33dae19714a7c78268207e39641"},{"path":"tools/p09/resume_acquisition_phased_runtime.py","bytes":32873,"sha256":"ccc4a5a37758aa6f258a556f141aa654d80cdad1e17865de5989d0d5eb0f8f86"},{"path":"tools/p09/tests/test_acquisition_phased_runtime.py","bytes":8073,"sha256":"8fe6de5cea32d6a9ed5d9181f1356b6216471c2984386d181bb37516287f1488"},{"path":"tools/p09/qualify_metadata_entry_early_pressure.py","bytes":11263,"sha256":"335aea52c483a0d89c8ea07cd89e1b6a1e0f9c0ffd989186fd2c292fbd5429d2"},{"path":"tools/p09/tests/test_metadata_entry_early_pressure.py","bytes":7250,"sha256":"21039b0483318fd05394ca0c4c763ab8a43d547ba2755e776a258a76378a8dc9"},{"path":"tools/p09/resume_shared_entry_pressure_runtime.py","bytes":33268,"sha256":"e9d6d5525efc6545ab1d8e012749f308d2e687e5b0ebd4e78b856e651c6ba01b"},{"path":"tools/p09/tests/test_shared_entry_pressure_runtime.py","bytes":10012,"sha256":"a6c68fbb22c49cee23c883647884c562234e1d7e6d1a86ebd0a88751c3ae2b64"},{"path":"tools/p09/resume_reviewed_shared_entry_runtime.py","bytes":35239,"sha256":"ded2e00a4cf64564928e02a9ca34f63bf7431195495a9b7a57e39eba32a2a9a3"},{"path":"tools/p09/tests/test_reviewed_shared_entry_runtime.py","bytes":10311,"sha256":"55535107ba5795161dfe03c0f9bd5bb53a68aba397d13ceaf7e8b7192638da24"},{"path":"tools/p09/resume_post97_stop_runtime.py","bytes":37570,"sha256":"4cde33b63c7a72e3788a6a781bd4ec8c749d1f7d6c72cbffb3f8588659edbdfb"},{"path":"tools/p09/tests/test_post97_stop_runtime.py","bytes":10595,"sha256":"2c30f776a3eac749331fabd45c60264d0300460490ffa05b3b50dbf6456a183d"},{"path":"tools/p09/resume_no_work_deferral_runtime.py","bytes":38204,"sha256":"e637d4af60423ddbfde7165a1b83caf778fb62b3bbdeb7fc695795cbb5464267"},{"path":"tools/p09/tests/test_no_work_deferral_runtime.py","bytes":14756,"sha256":"2084e58009f57dddbababf5dd62ad78f9c6c18c8855849c2e1684bf39d8816ed"},{"path":"tools/p09/resume_reviewed_anchor_runtime.py","bytes":45495,"sha256":"1967bcd50c673cb6b48a7e1e3169899a95ac5d792bd7adbd55b94cf80440271e"},{"path":"tools/p09/tests/test_reviewed_anchor_runtime.py","bytes":3866,"sha256":"d8e209bb0b4d81bcfeb6965fb8ff3a5824fa15170d95ace872652e48a963f22d"},{"path":"tools/p09/review_completed101_stop.py","bytes":8471,"sha256":"0a5b1b898813b582a8a5d3df3052b18fc9e616808666636d42e5be0bf7635c41"},{"path":"tools/p09/tests/test_completed101_stop.py","bytes":4297,"sha256":"9727f3de024de20d95a662fd96e712355a0fd79c14511a94dc3546d92813541d"},{"path":"tools/p09/close_completed101_source_frame.py","bytes":15129,"sha256":"f447b4b186e7e5925b5cbfbf2823fdb42ab6b5b648f9c9dec8076ec0662a4e46"},{"path":"tools/p09/tests/test_completed101_source_frame.py","bytes":8637,"sha256":"fd4707951bef8c2d635448ff89578fcfeb9cc019dad5d146cae20d1089464b77"},{"path":"tools/p09/accept_completed101_compound.py","bytes":10665,"sha256":"f06ca339b9ebe87cd961e102ee8eab9a07d1a7964164cc413924ee8a44a63fa3"},{"path":"tools/p09/tests/test_completed101_compound.py","bytes":3855,"sha256":"65fbf8a81cd3c0454018536540c28c0c6c66b8934b4436f8d9cbb400432eb0cc"},{"path":"tools/p09/close_completed101_source_frame_r2.py","bytes":17877,"sha256":"ec506450782799770aa0658fbd1536013c33863ea350a8c756b0aeb872e2caab"},{"path":"tools/p09/tests/test_completed101_source_frame_r2.py","bytes":8980,"sha256":"0bf6dd6790d473fc149a4f4a1b4c8187b2165277e837cdfd7a6bef657e02e729"},{"path":"tools/p09/accept_completed101_compound_r2.py","bytes":10689,"sha256":"87c839c6adc565790349763ed0e067e0d7198217278cd1bbcd03a04e5ff6c58b"},{"path":"tools/p09/tests/test_completed101_compound_r2.py","bytes":3858,"sha256":"6eab9b3b82e94f77c325abdb13abbe3a367d1f911114634cac36c21e13d49196"},{"path":"tools/p09/close_completed101_source_frame_r3.py","bytes":20211,"sha256":"887548629156bed419845d2136466b8983d87bb8670c1bc33f2e4a1d2289a21e"},{"path":"tools/p09/tests/test_completed101_source_frame_r3.py","bytes":9089,"sha256":"844f864afaabb79c7fa257736cba8c0744d5073f0d8a3a2514ba7e750e723f1d"},{"path":"tools/p09/accept_completed101_compound_r3.py","bytes":10689,"sha256":"e790edf464c612ce98956664db342d5c5ac252473024ce0d74be2832f06f802e"},{"path":"tools/p09/tests/test_completed101_compound_r3.py","bytes":3858,"sha256":"01e17b8ecd9b4d76a3be1b7eb45c369d4a1b12223a4fc30cf5aa58d00e08e247"},{"path":"tools/p09/close_completed101_source_frame_r4.py","bytes":22565,"sha256":"ce7de74d7eb4e7ded75a124790b7a34e9edd709c622fe973673fc891a0643c91"},{"path":"tools/p09/tests/test_completed101_source_frame_r4.py","bytes":9198,"sha256":"e7925e84d80b31cc5266d4a952de46d4179ac54d9e2303c4fc3567216b37e29d"},{"path":"tools/p09/accept_completed101_compound_r4.py","bytes":10689,"sha256":"9c71c03f29d81b30fc7beb34e6d3a23404966193989aeaac9b8a219e344f86c4"},{"path":"tools/p09/tests/test_completed101_compound_r4.py","bytes":3858,"sha256":"93317f9b4259efda539bcb5cf9c82ae6847fbcfeef1be0008b6ba3957f033849"},{"path":"tools/p09/review_completed101_source_stop.py","bytes":8250,"sha256":"23438e624fe82c65013e2d103a88c9cdf6c20d81027cbe17c3918d78a829b084"},{"path":"tools/p09/tests/test_completed101_source_stop.py","bytes":2068,"sha256":"544311acea2b0180accc4ac078e94ed642de50a6405ba1f7d1ca37a36d412036"},{"path":"tools/p09/review_completed101_source_stop_r2.py","bytes":9770,"sha256":"5e48452ddfdf8d0a1906a26d87ffc64ef1fd49f50ba4ccc14332346cdb622321"},{"path":"tools/p09/tests/test_completed101_source_stop_r2.py","bytes":2071,"sha256":"bdc23a408b1c8f0091944d082f2add0216f188863b74d1c66bdef168351321d2"},{"path":"tools/p09/close_completed101_source_frame_r5.py","bytes":25189,"sha256":"07e083bb5d7e1011de3bb11683f7101ed49f20fabddf13d660118d9f909d3968"},{"path":"tools/p09/tests/test_completed101_source_frame_r5.py","bytes":9640,"sha256":"6e1e87295f2d01a1b354017202dbd8c68a13191ea80dbed6add0da40c709d260"},{"path":"tools/p09/accept_completed101_compound_r5.py","bytes":10692,"sha256":"78457f1c5ea5d85bbd4e04bdbff25cd83acf0866e22388debb75eb6681a8e6c3"},{"path":"tools/p09/tests/test_completed101_compound_r5.py","bytes":3861,"sha256":"7268ba51435f08d7bcb8bf97babc2a97844f320af04b13f9a7b49e98c428ed11"},{"path":"tools/p09/accept_completed101_leading_metadata_compound.py","bytes":12793,"sha256":"b062da357c0d4e2a01de67568a1be05dbecab6ff89ccd36f227b0535d7f80e21"},{"path":"tools/p09/tests/test_completed101_leading_metadata_compound.py","bytes":1826,"sha256":"dc81cd07b4be17c79a39f5248cddb82c7a1867a83985e6a140f7645ed5f07390"},{"path":"tools/p09/leading_metadata_entry_pressure.py","bytes":6377,"sha256":"2695334be227a307cfcc69921d6326fefc1bca073239942882e36c93e8c2d412"},{"path":"tools/p09/tests/test_leading_metadata_entry_pressure.py","bytes":4799,"sha256":"53b53677af556735efa181a3d9cc467daa744c2465713824d1113e26838c4e08"}]
NEW=(accepted.SELF,accepted.TEST,leading.SELF,leading.TEST,SELF,TEST)
N=1631
DIRECTORIES=308
SCHEMA='hwpx-agent.p09-completed101-anchor-runtime-pair/v1'
PASS='PASS_EXACT_R07_COMPLETED101_ANCHOR_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_COMPLETED101_ANCHOR_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p304-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=42
EXECUTED=2*COUNT+30+18

def require(ok,code):m.require(ok,'COMPLETED101_ANCHOR_'+code)

class Reader(leading.Reader):
    pass

def budget(required,baseline,added):
    require(len(baseline)==1625 and len(required)==N and len(added)==6
        and set(added)==set(NEW) and not set(baseline)&set(added) and required=={**baseline,**added}
        and baseline[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in baseline.values())==120247880
        and sum(x['bytes'] for x in added.values())<=1048576,'FULL_QUALIFIED1625_PLUS_SIX_NO_SUBSET')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(N+DIRECTORIES)/14+2*N/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<600,'NOMINAL_UNCHANGED600')
    return dict(full_runtime_inputs=N,baseline_full_source_inputs=1625,new_inputs=6,
        actual_ancestor_directory_count=DIRECTORIES,native_rate=20,acquisition_native_rate=14,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_new_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)

def anchor(q):
    doc=m.m.review.bound_json(q,ANCHOR)
    failed=m.m.review.bound_json(q,accepted.FAILURE_PIN)
    root=m.m.review.bound_json(q,accepted.review.ROOT);body=m.m.review.bound_json(q,accepted.review.BODY)
    source=m.m.review.bound_json(q,accepted.SOURCE_PIN)
    inventory=m.m.review.bound_json(q,root['binding']['compiled_inventory_pin']);names=inventory['source_test_names']
    prep=m.m.review.bound_json(q,p.b.BASE_PREP);expected=p.v.pins(prep['whole_inputs']);exe=p.m.EXE
    binding=p.v.identity(names,expected,exe)
    old=m.m.review.bound_json(q,m.OLD_PAIRS[-1][0]);bp=old['case_receipt_pin'];healthy_body=m.m.review.bound_json(q,bp)
    legacy=m.m.review.bound_json(q,g.old.PRIOR)['legacy_plan']
    prior94=m.previous.record(old,healthy_body,bp,p.v.pins(healthy_body['source_freeze']),binding,
        p.v.pins(old['extra_frame_controller_pins']),names,legacy,old['prior_runtime_plan'])
    original=p.v.pins(body['source_freeze'])
    source_extras={n:q.pin(n) for n in accepted.closing.EXTRAS}
    accepted.validate(doc,root,body,source,names,expected,exe,original,source_extras,legacy,prior94,previous_failed=failed)
    for pin in FROZEN66:require(q.pin(pin['path'])==pin,'ALL_FROZEN66_UNCHANGED')
    require(doc['post_source_metadata_executor_pins']==FROZEN66[-4:]
        and doc['runtime_plan']['runtime_source_qualified_individual_cases']==95
        and doc['runtime_plan']['next_runtime_index']==102,'EXACT_ACCEPTED95_NEXT102_NO_BODY_REPLAY')
    qualified=m.m.review.bound_json(q,RETAINED_QUALIFIER);m.closed_attempt(qualified)
    require(qualified['state']==m.LIGHT and qualified['runtime_contract_executions']==1486
        and qualified['prior_runtime_plan']==prior94
        and p.v.pins(qualified['extra_frame_controller_pins'])==p.v.pins(root['extra_frame_controller_pins']),
        'REUSED_1486_QUALIFIED_UNCHANGED_ORIGINAL1599_NOT_EXECUTED_NOW')
    baseline={**original,**source_extras}
    added={n:q.pin(n) for n in NEW};require(all(added[n]==doc['post_source_metadata_executor_pins'][i]
        for i,n in enumerate(NEW[:4])),'ORIGINAL_POST_SOURCE_FOUR_NOW_IN_NATIVE_SCOPE')
    required={**baseline,**added}
    extras={**p.v.pins(root['extra_frame_controller_pins']),**source_extras,**added}
    directories={PurePosixPath('.')}
    for n in required:directories.update(PurePosixPath(n).parents)
    require(len(directories)==DIRECTORIES and len(extras)==164 and set(extras)<=set(required),
        'ALL308_ANCESTORS_AND164_CONTROLLERS')
    require(sorted(x.name for x in (p.c.ROOT/p.DIR).glob('p291-*.v1.json'))==
        ['p291-case-101-run002.v1.json','p291-light-run001.v1.json'],'NO_UNKNOWN_OLD101_REPLAY')
    require(sorted(x.name for x in (p.c.ROOT/p.DIR/'cases').glob('p291-*.json'))==
        ['p291-case-101-run002.json','p291-failure-101-run002.json'],'ONLY_IMMUTABLE_OLD101_BODY')
    budget(required,baseline,added)
    return legacy,doc['runtime_plan'],names,expected,exe,required,extras,baseline,added,old,healthy_body

def leading_contract(row):
    x=row['leading_metadata_entry_pressure']
    require(x['pre_entry_warning_CPU_percent']==90 and x['original_entry_rate']==32
        and x['calls']==x['completed_original_reads']==row['read_passes'] and x['failed_calls']==0
        and x['leading_binding_active'] is False and x['original_inner95_and90_callbacks_unmodified'] is True
        and x['original_entry_pacer_and_reader_retained'] is True
        and x['original_hard_CPU_RAM_IO600_720_and_all_reads_preserved'] is True
        and x['new_sampler_or_thread_started'] is False and x['original_clock_credit_or_counter_reset'] is False
        and x['source_or_case_or_read_exclusions_added'] is False and x['cleanup_not_guarded_or_paced'] is True,
        'ORIGINAL_CALLBACKS_AND_NEW_PRE_ENTRY90')
    m.early_contract(x['early_pressure'])
    m.m.metadata_contract(row);m.metadata_contract(row['early_metadata_pressure'])
    m.entry_pressure.connection_contract(row['metadata_entry_early_pressure_connection'])

def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    f=component['source_frame'];h=f['handles'];dup=h['borrowed_byte_streams']
    require(len(required)==N and h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+DIRECTORIES
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==DIRECTORIES-1
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+DIRECTORIES
        and h['handle_metadata_checks']==4*N+2*DIRECTORIES
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and f['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=N,directory_count=DIRECTORIES),'FULL1631_NATIVE_TWO_BYTE_AND_CLEANUP')
    m.m.r.h.h.pressure_contract(h['native_open_backpressure']);m.m.lower_contract(h)
    m.timing_contract(h['lock_timing_diagnostic']);profile.phase_contract(h['acquisition_phase_pressure'],N+DIRECTORIES,True)

def closed_attempt(d):
    require(d['schema_version']==SCHEMA and d['state'] in (PASS,LIGHT)
        and d.get('error_code') is None and d['resource_stop_reason'] is None
        and d['resource_watcher_cleanup_confirmed'] is True and d['runtime_contract_executions']==EXECUTED
        and d['reused_retained_contract_executions']==1486 and d['retained_contract_qualification_pin']==RETAINED_QUALIFIER
        and d['compound_anchor_pin']==ANCHOR and d['original_successful_bodies_not_reexecuted'] is True,
        'CLOSED_EXACT_CURRENT_NO_FAILED_RETRY')

def record(doc,body,pin,required,binding,extras,names,legacy,base,baseline,added):
    closed_attempt(doc);index,name=g.old.select(base,names)
    require(doc['state']==PASS and doc['selected_test_index']==index and doc['selected_test_name']==name
        and name not in base['runtime_qualified_test_names'] and doc['binding']==binding and doc['prior_runtime_plan']==base
        and doc['case_receipt_pin']==pin and doc['receipt_serialization_policy']==r.policy()
        and doc['monotonic_binding_policy']==review.policy() and doc['scope_budget']==budget(required,baseline,added)
        and doc['scope_added_six_pins']==list(added.values()) and doc['extra_frame_controller_pins']==list(extras.values())
        and doc['accepted_exact_product_body_count']==1 and doc['runtime_plan']==g.advance(legacy,base,names,index),
        'EXACT_NEXT_ONE_QUALIFIED_NOT_DUPLICATE')
    require(doc['own_queue_contract_tests_passed']==doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['native_timing_connected'] is True and doc['early_source_guard_connected'] is True
        and doc['aggregate_post_reader_connection_verified'] is True and doc['diagnostic_parent_connection_selected'] is True
        and doc['original_parent_capture_adapter_selected'] is True and doc['acquisition_phase_connection_selected'] is True
        and doc['actual_product_child_executed'] is True and body['task']==f'p204-r07-case-{index:03}-tests'
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']
        and doc['preparation_IO']['read_passes']+doc['closing_component']['metadata_IO']['read_passes']<=720
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
        'ALL_CLOSED_BINDING_JOB_METADATA_GUARDS_NOT_GATE')
    leading_contract(doc['preparation_IO']);leading_contract(doc['closing_component']['metadata_IO'])
    m.job_contract(body);m.early_contract(doc['early_source_checkpoint'])
    native_pair(doc['closing_component'],body,pin,required,binding,extras);r.stats_contract(doc['packed_parent_write_statistics'],pin)
    return doc['runtime_plan']

def progress(q,legacy,base,names,required,binding,extras,baseline,added):
    folder=p.c.ROOT/p.DIR
    for path in sorted((*folder.glob('p304-light-run*.v1.json'),*folder.glob('p304-admission-run*.v1.json'))):
        closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    rows=sorted(folder.glob('p304-case-*-run*.v1.json'));require(len(rows)<=4096,'BOUNDED_NAMESPACE')
    plan=base
    for path in rows:
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        d=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(d)
        require(d['selected_test_index']==index and d['case_receipt_pin']['path']==
            f'{p.DIR}/cases/p304-case-{index:03}-run{number:03}.json','FILENAME_BODY_IDENTITY')
        bp=d['case_receipt_pin'];body=m.m.review.bound_json(q,bp)
        plan=record(d,body,bp,required,binding,extras,names,legacy,plan,baseline,added)
    return plan

def contracts(fixtures):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'));import test_completed101_compound_runtime as t
    with patch('subprocess.Popen',side_effect=AssertionError('NO_CONTRACT_CHILD')),patch('subprocess.run',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_CONTRACT_THREAD')):
        require(p.contracts()==30 and leading.contracts()==18,'ORIGINAL_NATIVE30_AND_LEADING18')
        for following in (False,True):
            with patch.object(t,'FIXTURES',fixtures),patch.object(t,'FOLLOWING',following):
                rr=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
            require(rr.wasSuccessful() and rr.testsRun==COUNT and not rr.skipped,'CURRENT42_AND_FOLLOWING42')
    return EXECUTED

def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p304-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
    class Output:
        def __init__(self,stream):self.stream=stream
        def write(self,block):
            nonlocal written
            count=self.stream.write(block);require(type(count) is int and count==len(block),'SIDECAR_ONCE')
            digest.update(block.encode('ascii'));written+=count;return count
    with path.open('x',encoding='utf-8') as stream:stats=capture.write_rejected(Output(stream),owner,out) if capture.rejected else capture.write_terminal(Output(stream),owner,out)
    out.update(terminal_parent_failure_sidecar_pin=dict(path=path.relative_to(p.c.ROOT).as_posix(),bytes=written,
        sha256=digest.hexdigest()),terminal_parent_failure_statistics=stats,original_failure_body_placeholder_preserved=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light');ap.add_argument('--run',type=int,required=True)
    args=ap.parse_args();require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p304-{args.mode if args.mode=="light" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=parent=proposed=None;body=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=ANCHOR,
        retained_contract_qualification_pin=RETAINED_QUALIFIER,reused_retained_contract_executions=1486,
        own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT,
        original_successful_bodies_not_reexecuted=True,compound_anchor_verified_without_body_reexecution=False,
        early_source_guard_connected=False,original_parent_capture_adapter_selected=False,
        packed_root_writer_selected=True,accepted_exact_product_body_count=0,receipt_serialization_policy=r.policy(),
        monotonic_binding_policy=review.policy(),aggregate_post_reader_connection_verified=False,diagnostic_parent_connection_selected=False,
        native_timing_connected=False,acquisition_phase_connection_selected=False,metadata_entry_pressure_connection_selected=False)
    stage='admission'
    try:
        owner.admit();stage='reader_constructor';q=Reader(owner,context)
        out['metadata_entry_pressure_connection_selected']=type(q.entry_early_binding) is m.entry_pressure.Binding and q.entry_binding.pacer.checkpoint is q.reader.checkpoint
        stage='anchor'
        legacy,base,names,expected,exe,required,extras,baseline,added,healthy,healthy_body=anchor(q)
        stage='selection';binding=p.v.identity(names,expected,exe);plan=progress(q,legacy,base,names,required,binding,extras,baseline,added);index,name=g.old.select(plan,names)
        stage='contract_tests'
        with context.scope('contract_tests'):
            out['runtime_contract_executions']=contracts((legacy,plan,names,required,extras,baseline,added,healthy,healthy_body))
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            extra_frame_controller_pins=list(extras.values()),scope_added_six_pins=list(added.values()),
            compound_anchor_verified_without_body_reexecution=True,scope_budget=budget(required,baseline,added))
        stage='final_fresh_preparation'
        if args.mode=='light':q.finish();proposed=dict(state=LIGHT)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p304-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            require(not list((p.c.ROOT/p.DIR/'cases').glob(f'p304-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p304-case-{index:03}-run{args.run:03}.json';q.finish()
            require(q.shared_budget['read_calls']<=m.m.META_READ_LIMIT-2,'POST_BODY_TWO_READS_RESERVED')
            early=early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=profile.InputLocks(p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'EXACT_OWNER_EARLY_NATIVE20')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held);counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(early_source_guard_connected=True,acquisition_phase_connection_selected=type(held) is profile.InputLocks,case_receipt_path=body_path.relative_to(p.c.ROOT).as_posix())
            stage='source_frame_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            parent=connection.ParentConnection(frame,writes,index,name,binding);capture=parent.capture
            out['original_parent_capture_adapter_selected']=isinstance(capture,m.m.support.candidate.Capture)
            out['diagnostic_parent_connection_selected']=type(parent) is connection.ParentConnection and type(capture) is m.a.Capture
            out['native_timing_connected']=isinstance(held,connection.TimedInputLocks)
            stage='owned_parent';held.mark('before_parent');code=parent.run(body_path,context);held.mark('after_parent')
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            stage='post_reader_constructor';meta=review.construct(Reader,owner,context,counter)
            require(context.reader is counter and counter.metadata==[meta.reader],'MONOTONIC_ORIGINAL_AGGREGATE')
            out['aggregate_post_reader_connection_verified']=True
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);m.job_contract(body);r.stats_contract(writes[0],pin);meta.finish()
            stage='source_frame_closing';held.mark('before_release')
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0],
                actual_product_child_executed=body.get('actual_product_child_executed') is True)
            proposed=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out['error_code']=p.b.run.original.closed_error(error);out['failure_diagnostic']=m.diagnostic(error,stage);proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            out['terminal_source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:out.update(preparation_IO=q.summary(),bound_preparation_input_pins=list(q.reader.snapshots.values()))
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan,baseline,added)
            else:
                require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True
                    and doc['runtime_contract_executions']==EXECUTED and doc['monotonic_binding_policy']==review.policy()
                    and doc['compound_anchor_pin']==ANCHOR and doc['reused_retained_contract_executions']==1486
                    and doc['retained_contract_qualification_pin']==RETAINED_QUALIFIER
                    and doc['metadata_entry_pressure_connection_selected'] is True,
                    'LIGHT_FULL_FRESH_CURRENT_CONTRACTS_NOT_REPLAY')
                leading_contract(doc['preparation_IO'])
        g.complete(out,owner,proposed,validate)
        if capture is not None and (capture.pending or capture.rejected):
            try:preserve_failure(capture,frame,owner,out,index,args.run)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:out.update(state='FAILED_NOT_ACCEPTED',terminal_failure_write_error=p.b.run.original.closed_error(error))
        try:
            with destination.open('x',encoding='utf-8') as stream:
                writer=r.packed.dump if out['state'] in (PASS,LIGHT) else r.compact.dump
                def terminal():require(owner.done.is_set(),'NO_RESOURCE_RESTART')
                writer(out,stream,checkpoint=terminal,indent=2)
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='MONOTONIC_RUNTIME_TERMINAL_SERIALIZATION_FAILED')));return 2
        print(json.dumps({k:out.get(k) for k in ('state','runtime_contract_executions','selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2


if __name__=='__main__':
    sys.modules.setdefault('resume_completed101_compound_runtime',sys.modules[__name__])
    raise SystemExit(main())
