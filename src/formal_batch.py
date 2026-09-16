"""Formal blocks: immutable plan, prepare while healthy, run after human gate.

Usage: python -m src.formal_batch {plan,prepare,execute,summarize} ...
No database faults or recovery are automated here.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import sys

from .checkers import CHECKERS
from .run import SCENARIO_ROUTES

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ('normal', 'node_stop', 'partition_cross_side')
MODELS = ('ryw', 'mr', 'mw', 'wfr')
IPS = {'n1': '10.20.0.11', 'n2': '10.20.0.12', 'n3': '10.20.0.13'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def fingerprint():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / 'src').glob('*.py'))}


def read_rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def conditions(run_id, scenario, seed):
    rows = []
    for model in MODELS:
        for cl in ('ONE', 'QUORUM'):
            for repeat in range(1, 6):
                label = f'{model}-{cl.lower()}-{repeat:02}'
                rows.append(dict(model=model, write_cl=cl,
                                 read_cl='ONE' if model == 'mw' else cl,
                                 read_cl_applicable=model != 'mw', repeat=repeat,
                                 history=f'{run_id}-{label}', scenario=scenario))
    random.Random(seed).shuffle(rows)
    return rows


def assess(rows, item, run_id):
    """Keep availability separate from checker results; reject contaminated logs."""
    if not rows:
        return 'invalid', 'empty history'
    ids = [r.get('operation_id') for r in rows]
    if len(ids) != len(set(ids)):
        return 'invalid', 'duplicate operation_id'
    for r in rows:
        if (r.get('run_id'), r.get('history_id'), r.get('model')) != (run_id, item['history'], item['model']):
            return 'invalid', 'mixed run/history/model'
    if any(r.get('phase') == 'setup' for r in rows):
        return 'setup_error', 'connection initialization failed; see raw log'
    observed = [r for r in rows if r.get('phase') in ('workload', 'diagnostic')]
    if not observed:
        return 'invalid', 'no workload operations'
    routes = SCENARIO_ROUTES[item['scenario']]
    model = item['model']
    # Exact operation metadata for the supported, fixed workloads.
    specs = {
        'ryw': [('write','x','source','U'), ('read','x','target','U')],
        'mr': [('write','x','source','P'), ('read','x','source','R'), ('read','x','target','R')],
        'mw': [('write','a','source','U'), ('write','b','target','U'),
               ('read','b','target','observer'), ('read','a','target','observer')],
        'wfr': [('write','a','source','P'), ('read','a','source','U'), ('write','b','target','U'),
                ('read','b','target','observer'), ('read','a','target','observer')],
    }[model]
    if [r.get('operation_id') for r in observed] != list(range(1, len(observed)+1)) or len(observed) > len(specs):
        return 'invalid', 'operation order/number mismatch'
    for r, (operation, key, role, session) in zip(observed, specs):
        diagnostic = session == 'observer'
        cl = 'ONE' if diagnostic else (item['write_cl'] if operation == 'write' else item['read_cl'])
        expected = {'operation': operation, 'key': key, 'session_id': session,
                    'phase': 'diagnostic' if diagnostic else 'workload',
                    'scenario': item['scenario'], 'routing': routes,
                    'requested_coordinator': IPS[routes[role]], 'actual_statement_cl': cl}
        if any(r.get(k) != v for k, v in expected.items()):
            return 'invalid', 'operation metadata/routing/CL mismatch'
        if r.get('status') == 'ok' and r.get('actual_coordinator') != IPS[routes[role]]:
            return 'inconclusive', 'successful operation coordinator not verified'
        if operation == 'read' and r.get('status') == 'ok':
            allowed = {'x': ('v0','v1'), 'a': ('first-write','original-post'),
                       'b': ('second-write;depends-on=a','reply;depends-on=a')}[key]
            returned = r.get('returned')
            if 'returned' not in r or (returned is not None and
                    (not isinstance(returned, dict) or returned.get('value') not in allowed)):
                return 'invalid', 'missing or unexpected read payload'
        if operation == 'write' and key == 'b' and r.get('dependency') != 'a':
            return 'invalid', 'dependent write lacks predecessor'
    result, reason = CHECKERS[model](rows)
    if model in ('mw', 'wfr') and result == 'witness':
        return 'candidate_dependency_witness', reason + '; A/C evidence and model interpretation require review'
    return result, reason


def call_runner(command, item, run_id, folder, verified=False):
    args = [sys.executable, '-m', 'src.run', command, '--model', item['model'],
            '--history', item['history'], '--run-id', run_id,
            '--log', str(folder / (item['history'] + '.jsonl'))]
    if command == 'run':
        args += ['--scenario', item['scenario'], '--write-cl', item['write_cl'], '--read-cl', item['read_cl']]
        if verified:
            args += ['--partition-verified']
    with (folder / (item['history'] + f'.{command}.txt')).open('x', encoding='utf-8') as out:
        out.write(json.dumps({'argv': args, 'started_utc': utc()}) + '\n')
        out.flush()
        try:
            code = subprocess.run(args, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, timeout=180).returncode
        except subprocess.TimeoutExpired:
            out.write('\nPROCESS TIMEOUT: batch aborted; preserve partial log.\n')
            raise RuntimeError('runner exceeded 180 seconds; restore fault and archive this block')
        out.write(json.dumps({'exit_code': code, 'ended_utc': utc()}) + '\n')
    return code


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('plan','prepare','execute','summarize'))
    p.add_argument('--run-id', required=True)
    p.add_argument('--scenario', choices=SCENARIOS)
    p.add_argument('--seed', type=int, default=5208)
    p.add_argument('--gate', type=Path, help='human-written verified gate record, required to execute')
    a = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{7,119}', a.run_id):
        p.error('run-id must be a new safe time+UUID identifier')
    folder = ROOT / 'results' / 'raw' / a.run_id / 'member-b'
    folder.mkdir(parents=True, exist_ok=True)
    plan_path = folder / 'batch-plan.json'
    if a.command == 'plan':
        if not a.scenario:
            p.error('--scenario required for plan')
        commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
        save(plan_path, dict(run_id=a.run_id, scenario=a.scenario, seed=a.seed,
                            created_utc=utc(), commit=commit, source_sha256=fingerprint(),
                            sample_size_per_condition=5, diagnostic_cl='ONE',
                            items=conditions(a.run_id, a.scenario, a.seed)))
        print(f'PLAN: 8 conditions, 40 histories. {plan_path}')
        return
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    if a.command in ('prepare','execute') and plan['source_sha256'] != fingerprint():
        raise RuntimeError('source changed after plan: use a new block')
    if a.command == 'prepare':
        save(folder / 'prepare-started.json', {'utc': utc()})
        for i, item in enumerate(plan['items'], 1):
            path = folder / (item['history'] + '.jsonl')
            if path.exists():
                raise RuntimeError(f'preexisting history: {path}')
            if item['model'] in ('ryw','mr'):
                code = call_runner('prepare', item, a.run_id, folder)
                rows = read_rows(path)
                if code or len(rows) != 1 or rows[0].get('status') != 'ok' or rows[0].get('actual_statement_cl') != 'ALL':
                    raise RuntimeError('prepare failed: NO DATA_READY; preserve this block and use new ID after diagnosis')
            print(f'prepare {i}/40 {item["history"]}', flush=True)
        save(folder / 'data-ready.json', {'utc': utc(), 'histories': 40})
        print('DATA_READY: all initializations passed. Wait for the human fault gate.')
        return
    if a.command == 'execute':
        if not (folder / 'data-ready.json').exists() or not a.gate:
            p.error('successful prepare and --gate required')
        gate = json.loads(a.gate.read_text(encoding='utf-8'))
        if (gate.get('run_id') != a.run_id or gate.get('scenario') != plan['scenario']
                or gate.get('verified') is not True or any(not gate.get(k) for k in ('a_evidence','b_evidence','c_evidence','verified_utc'))):
            raise RuntimeError('gate missing identity, actual verification time or A/B/C evidence references')
        save(folder / 'execute-started.json', {'utc': utc(), 'gate': gate})
        for i, item in enumerate(plan['items'], 1):
            rows = read_rows(folder / (item['history'] + '.jsonl'))
            expected = 1 if item['model'] in ('ryw','mr') else 0
            if len(rows) != expected or any(r.get('phase') != 'prepare' for r in rows):
                raise RuntimeError('history has unexpected operations: never resume/replay this block')
            code = call_runner('run', item, a.run_id, folder, plan['scenario'] == 'partition_cross_side')
            if code:
                raise RuntimeError('runner process failed: restore fault, retain partial block; do not replay')
            print(f'run {i}/40 {item["history"]}', flush=True)
        save(folder / 'workload-done.json', {'utc': utc(), 'histories': 40})
        print('WORKLOAD_DONE: restore the fault now. Run summarize separately.')
        return
    output = ROOT / 'results' / 'processed' / a.run_id
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for item in plan['items']:
        path = folder / (item['history'] + '.jsonl')
        try:
            rows = read_rows(path)
            result, reason = assess(rows, item, a.run_id)
        except (ValueError, KeyError, TypeError) as e:
            rows, result, reason = [], 'invalid', str(e)
        statuses = Counter(r.get('status','missing') for r in rows if r.get('phase') == 'workload')
        records.append(dict(history=item['history'], model=item['model'], scenario=item['scenario'],
                            write_cl=item['write_cl'], read_cl=item['read_cl'] if item['read_cl_applicable'] else 'N/A',
                            result=result, reason=reason, workload_status_counts=json.dumps(statuses),
                            raw_path=str(path.relative_to(ROOT))))
    with (output / 'histories.csv').open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    counts = Counter((r['model'],r['write_cl'],r['read_cl'],r['result']) for r in records)
    save(output / 'counts.json', {'planned_histories': 40,
         'complete_block': (folder / 'workload-done.json').exists(),
         'counts': [dict(model=k[0],write_cl=k[1],read_cl=k[2],result=k[3],n=v) for k,v in sorted(counts.items())]})
    print(output)


if __name__ == '__main__':
    main()
