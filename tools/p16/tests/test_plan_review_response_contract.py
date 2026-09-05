"""Check the actual TS consumer against the unchanged P15 Draft 2020-12 schemas.

Requires the normal widget build first; missing output is a failure, never a skip.
All inputs below are synthetic metadata. No server, browser or Hangul is launched.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
PROBE = """
import { readFileSync } from 'node:fs';
import { parseDocumentEditResult, parsePlanReviewRenderRequest, parsePlanReviewSnapshot } from './web/plugin-widget/dist/plan-review-model.js';
import { PLAN_REVIEW_RENDER_INPUT_SCHEMA, PLAN_REVIEW_RENDER_OUTPUT_SCHEMA } from './web/plugin-widget/dist/plan-review-resource.js';
const input = JSON.parse(readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify({
  results: input.results.map(value => parseDocumentEditResult(value) !== null),
  requests: input.requests.map(value => parsePlanReviewRenderRequest(value) !== null),
  snapshots: input.snapshots.map(value => parsePlanReviewSnapshot(value) !== null),
  inputSchema: PLAN_REVIEW_RENDER_INPUT_SCHEMA,
  outputSchema: PLAN_REVIEW_RENDER_OUTPUT_SCHEMA,
}));
"""


class PlanReviewResponseContractTests(unittest.TestCase):
    def test_runtime_acceptance_matches_authoritative_schema_boundaries(self) -> None:
        catalog = json.loads((ROOT / 'protocol/mcp/p15-public-tools-v1.json').read_text(encoding='utf-8'))
        tool = next(item for item in catalog['tools'] if item['name'] == 'document_edit')
        artifact = {'artifact_id': 'art_abcdefgh', 'media_type': 'application/hwp+zip', 'bytes': 1234, 'sha256': 'b' * 64}
        base = {'schema_version': 'hwpx-agent.tool-result/v1', 'request_id': 'req_abcdefgh', 'outcome': 'succeeded', 'safe_summary': 'ok', 'warnings': [], 'job_id': None, 'revision_id': 'rev_newvalue1', 'artifact': artifact, 'commit_state': 'committed', 'validation_state': 'verified'}
        results = [deepcopy(base), {**base, 'artifact': None}]
        for field, values in {
            'artifact_id': ['art_abcdefg', 'art_abcdefgh', 'art_' + 'x' * 120, 'art_' + 'x' * 121],
            'media_type': ['', 'a/b', 'a/' + 'b' * 125, 'a/' + 'b' * 126, 'text/plain; charset=utf-8'],
            'bytes': [-1, 0, 1.5, 10737418240, 10737418241, '1', True],
            'sha256': ['a' * 63, 'a' * 64, 'A' * 64, 'a' * 65],
        }.items():
            results.extend({**base, 'artifact': {**artifact, field: value}} for value in values)
        results.extend({**base, 'artifact': {key: value for key, value in artifact.items() if key != missing}} for missing in artifact)
        results.append({**base, 'artifact': {**artifact, 'url': 'private'}})
        results.extend({**base, 'outcome': outcome, 'validation_state': state} for outcome in ['accepted', 'succeeded', 'partial', 'unverified'] for state in ['not_run', 'verified', 'partial', 'failed'])
        for text in ['😀' * 1000, '😀' * 1001, 'a' * 999 + '😀', 'a' * 1000 + '😀']:
            results.append({**base, 'safe_summary': text})
            results.append({**base, 'warnings': [{'code': 'SAFE_WARNING', 'message': text}]})
        request = {'schema_version': 'hwpx-agent.plan-review-render-request/v1', 'client_surface': 'codex_local', 'locale': 'ko-KR', 'project_id': 'prj_abcdefgh', 'source_revision_id': 'rev_abcdefgh', 'plan_id': 'plan_abcdefgh'}
        requests = [{**request, 'plan_id': 'plan_' + 'a' * length} for length in [7, 8, 118, 119, 120, 1000]]
        snapshot = {**request, 'schema_version': 'hwpx-agent.plan-review/v1', 'risk_level': 'low', 'estimated_page_effect': 'local', 'route': [{'capability_id': 'paragraph.text_replace', 'selected_backend': 'direct_hwpx', 'support_level': 'verified', 'supported': True}], 'route_digest': 'a' * 64, 'diff': {'added': 0, 'modified': 0, 'removed': 0, 'categories': []}, 'warnings': [], 'signature_impact': 'none', 'dry_run_state': 'verified', 'execution_allowed': True}
        snapshots = [{**snapshot, 'plan_id': item['plan_id']} for item in requests]
        completed = subprocess.run(['node', '--input-type=module', '-e', PROBE], cwd=ROOT, input=json.dumps({'results': results, 'requests': requests, 'snapshots': snapshots}), text=True, capture_output=True, timeout=30, check=True)
        observed = json.loads(completed.stdout)
        for key, values, schema in [('results', results, tool['outputSchema']), ('requests', requests, observed['inputSchema']), ('snapshots', snapshots, observed['outputSchema'])]:
            validator = Draft202012Validator(schema)
            Draft202012Validator.check_schema(schema)
            self.assertEqual(observed[key], [validator.is_valid(value) for value in values], key)
        plan_validator = Draft202012Validator(tool['inputSchema']['$defs']['plan_id'])
        self.assertEqual(observed['requests'], [plan_validator.is_valid(value['plan_id']) for value in requests])


if __name__ == '__main__':
    unittest.main()
