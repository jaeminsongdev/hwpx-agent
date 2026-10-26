"""Current direct target-cursor observations, never hyperlink activation or SaveAs."""
import prepared_bookmark755_evidence as prior
import bookmark_cursor_preparation768 as prep
r=prior.r;producer=prior.producer

def require(ok,code):
    if not ok:raise ValueError('XREF_CURSOR768_EVIDENCE_'+code)

def captured(reader,folder,index,profiles):
    trace=reader.json(folder+'/case-trace.json');manifest=reader.json(prep.PREPARED);case=manifest['cases'][index-1]
    require(trace['schema_version']=='hwpx-agent.private.prepared-bookmark768-trace/v1'and type(trace['case_index'])is int
        and trace['case_index']==trace['source_case_index']==case['case_index']==index
        and trace['state']=='capture_returned_semantics_unqualified'and trace['error_code']is None and trace['cleanup_error']is None
        and trace['source_identity_preserved']is True and trace['input_leases_closed']is True
        and trace['SaveAs_invoked']is False and trace['direct_bookmark_cursor_only']is True and trace['SDK_insertion_invoked']is False
        and trace['artifacts']=={},'QUERY_ONLY_CLOSED_TRACE')
    producer(trace,profiles)
    require(len(trace['navigation'])==2,'EXACT_TWO_QUERIES')
    for row,label,pin in zip(trace['navigation'],('initial','reopened'),(case['output'],case['reopened']),strict=True):
        require(row['stage']==label and row['source_sha256']==pin['sha256']and row['complete']is True and type(row['bookmark_command'])is int and row['bookmark_command']==1
            and row['target_name_sha256']==manifest['target_name_sha256']and row['selected_text_sha256']==manifest['target_content_sha256']
            and row['selected_UTF8_bytes']==row['selected_characters']==10 and row['whole_text_before_sha256']==row['whole_text_after_sha256']
            and row['source_bytes_rewritten']is False and row['hyperlink_activation_invoked']is False,'CURRENT_TARGET_SELECTION_NOT_LINK_OR_EDIT')
        require(type(row['origin'])is list and len(row['origin'])==3 and all(type(n)is int and n>=0 for n in row['origin'])and row['origin'][:2]==[0,0],'OBSERVED_ORIGIN')
        a=row['selection_positions'];b=row['confirmation_selection_positions']
        require(type(a)is list and type(b)is list and len(a)==len(b)==6 and a==b and all(type(n)is int and n>=0 for n in a+b)
            and a[:2]==[0,0]and a[3:5]==[0,0]and a[2]>=row['origin'][2]and a[5]-a[2]==10,'EXACT_STABLE_NATIVE_SELECTION_AND_CONTENT_EXTENT')
        require(reader.pin(pin['path'])==pin,'CURRENT_UNCHANGED_SOURCE')
    return dict(source_case_index=index,artifacts={'case-trace.json':reader.pin(folder+'/case-trace.json')},sources=dict(initial=case['output'],reopened=case['reopened']),
        native_capture_bound=True,direct_bookmark_cursor_observations=trace['navigation'],hyperlink_activation_qualified=False,reference_semantics_qualified=False,P09_complete=False)

def current_artifacts(guard,host,directory):
    reader=r.a.AcceptanceReader(r.c.ROOT,guard.check)
    rows=[captured(reader,directory(i),i,host.scope.sessions[(i-1)*2:i*2])for i in range(1,9)]
    reader.finish()
    return dict(cases=rows,fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,field_readback_semantics_qualified=False,render_diff_qualified=False,hyperlink_activation_qualified=False,P09_complete=False)
