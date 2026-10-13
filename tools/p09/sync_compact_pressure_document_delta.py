"""P220 큐의 문서 delta. 원 P216 스키마/원 문서 byte 보존 기준은 유지한다."""
import argparse
import json
import re
import sync_generic_runtime_document_delta as documents
import resume_compact_pressure_runtime as runtime

p = runtime.p
g = runtime.g
SELF = 'tools/p09/sync_compact_pressure_document_delta.py'


def require(ok, code):
    p.require(ok, 'COMPACT_DOCUMENT_' + code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--revision', type=int, required=True)
    ap.add_argument('--previous', required=True)
    ap.add_argument('--report', required=True)
    ap.add_argument('--run', type=int, required=True)
    args = ap.parse_args()
    history = documents.paths(args.revision, args.previous, args.report)
    require(p.c.Path.cwd().resolve() == p.c.ROOT and 1 <= args.run <= 99, 'CWD_RUN')
    destination = p.c.ROOT / f'{p.DIR}/p216-generic-doc-delta-r{args.revision:04}-run{args.run:02}.v1.json'
    require(not destination.exists(), 'FRESH_ONLY')
    context = g.observation.Context()
    owner = g.observation.Resources(context)
    q = candidate = None
    out = dict(schema_version=documents.SCHEMA, state='FAILED_NOT_ACCEPTED', **p.r.flags(),
        new_product_or_full_source_frame_executed=False, compact_pressure_document_provider=True)
    try:
        owner.admit()
        q = p.qualification.Reader(owner, context)
        previous = q.json(args.previous)
        old_pins = documents.prior(previous, args.revision)
        legacy, base, names, expected, exe, required, extras = runtime.anchor(q)
        binding = p.v.identity(names, expected, exe)
        plan = runtime.progress(q, legacy, base, names, required, binding, extras)
        require(plan['runtime_source_qualified_individual_cases'] > previous['runtime_plan']['runtime_source_qualified_individual_cases']
            and plan['runtime_successful_candidates_requiring_closing'] == 0, 'ACTUAL_NEW_PROGRESS')
        out.update(compact_pressure_runtime_contract_tests_passed=runtime.contracts((legacy, plan, names)),
            document_delta_contract_tests_passed=documents.contracts())
        prefixes = []
        for name, pin in old_pins.items():
            archived = history + name.split('/')[-1]
            require(q.pin(archived) == dict(pin, path=archived), 'EXACT_PREVIOUS_DOCUMENT_PIN')
            before = q.text(archived)
            after = q.text(name)
            require(after.endswith(before) and len(after) > len(before), 'OLD_DOCUMENT_HISTORY_PRESERVED')
            prefixes.append(after[:-len(before)])
            require(q.reader._read(name, parse=True)[1].endswith(q.reader._read(archived, parse=True)[1]), 'EXACT_OLD_BYTE_SUFFIX')
        require(prefixes[0] == prefixes[1]
            and re.match(r'^> [0-9]{4}-[0-9]{2}-[0-9]{2} P216 generic-runtime-r' + str(args.revision) + r' ', prefixes[0]),
            'IDENTICAL_CURRENT_PREFIX')
        require(all(text in prefixes[0] for text in documents.words(plan)), 'DERIVED_COUNTS_AND_NO_GATE')
        report = q.text(args.report)
        require(all(text in report for text in documents.words(plan))
            and 'CPU 보호 중단 시 자동 재시도 금지' in report
            and '실제 Native pressure frame 연결' in report
            and '실제 compact parent/root writer 연결' in report, 'REPORT_PROGRESS_AND_WRITER_BOUNDARIES')
        prior_names = set(previous['runtime_plan']['runtime_qualified_test_names'])
        new_receipts = []
        for family, expression in (('p218', runtime.h.FILE), ('p220', runtime.FILE)):
            for path in sorted((p.c.ROOT / p.DIR).glob(f'{family}-case-*-run*.v1.json')):
                match = expression.fullmatch(path.name)
                require(match is not None, 'EXACT_RUNTIME_FILENAME')
                index = int(match[1])
                require(1 <= index <= len(names), 'EXACT_INVENTORY_INDEX')
                if names[index - 1] in prior_names:
                    continue
                name = path.relative_to(p.c.ROOT).as_posix()
                pin = q.pin(name)
                require(pin['sha256'] in report, 'REPORTED_NEW_ACTUAL_SHA')
                new_receipts.append(pin)
        require(len(new_receipts) == plan['runtime_source_qualified_individual_cases']
            - previous['runtime_plan']['runtime_source_qualified_individual_cases'], 'EXACT_NEW_PAIR_COUNT')
        for name in (SELF, documents.SELF, documents.TEST, args.previous):
            q.pin(name)
        q.finish()
        candidate = dict(state=documents.PASS, document_revision=args.revision, runtime_plan=plan,
            previous_document_receipt_pin=q.reader.snapshots[args.previous], new_actual_runtime_pair_pins=new_receipts,
            exact_prior_document_bytes_preserved=True, original_failure_receipts_preserved=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED', error_code=p.b.run.original.closed_error(error))
        candidate = None
    finally:
        if q is not None:
            out.update(IO=q.summary(), bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation'] = g.observation.summary(owner)
        def validate(doc):
            require(doc['IO']['finished'] is True
                and doc['IO']['bound_inputs'] == doc['IO']['final_fresh_hashes'], 'FINAL_ALL_FRESH')
        g.complete(out, owner, candidate, validate)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'document_revision', 'error_code', 'resource_stop_reason')}))
    return 0 if out['state'] == documents.PASS else 2


if __name__ == '__main__':
    raise SystemExit(main())
