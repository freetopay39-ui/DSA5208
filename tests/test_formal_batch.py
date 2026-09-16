import unittest
import json
from pathlib import Path
from unittest.mock import patch
import uuid
from src import formal_batch as batch
from src.formal_batch import conditions, assess


class FormalBatchTests(unittest.TestCase):
    def test_matrix_is_24_conditions_120_unique_histories(self):
        all_items = []
        for i, scenario in enumerate(('normal','node_stop','partition_cross_side')):
            items = conditions(f'formal-block-{i}', scenario, 5208)
            self.assertEqual(len(items), 40)
            self.assertEqual(items, conditions(f'formal-block-{i}', scenario, 5208))
            self.assertEqual(sum(x['model'] == 'mw' and x['read_cl'] == 'ONE' for x in items), 10)
            all_items.extend(items)
        self.assertEqual(len({x['history'] for x in all_items}), 120)

    def row(self, n, operation, value, ip, session='R', status='ok'):
        return dict(run_id='formal-block-0', history_id='h', model='mr',
                    operation_id=n, operation=operation, key='x', session_id=session,
                    phase='workload', scenario='partition_cross_side',
                    routing={'source':'n1','target':'n3'}, requested_coordinator=ip,
                    actual_coordinator=ip if status == 'ok' else None,
                    actual_statement_cl='ONE', status=status, returned=value)

    def item(self):
        return dict(history='h',model='mr',scenario='partition_cross_side',write_cl='ONE',read_cl='ONE')

    def history(self):
        return [self.row(1,'write',None,'10.20.0.11','P'),
                self.row(2,'read',{'value':'v1'},'10.20.0.11'),
                self.row(3,'read',{'value':'v0'},'10.20.0.13')]

    def test_true_regression_and_failed_read_are_distinct(self):
        rows = self.history()
        self.assertEqual(assess(rows,self.item(),'formal-block-0')[0], 'witness')
        rows[2].update(status='unavailable',returned=None,actual_coordinator=None)
        self.assertEqual(assess(rows,self.item(),'formal-block-0')[0], 'blocked')

    def test_mixed_and_replayed_logs_are_invalid(self):
        rows = self.history()
        self.assertEqual(assess(rows+rows,self.item(),'formal-block-0')[0], 'invalid')
        rows[0]['run_id'] = 'other'
        self.assertEqual(assess(rows,self.item(),'formal-block-0')[0], 'invalid')

    def test_wrong_route_and_unknown_payload_not_success(self):
        rows = self.history()
        rows[2]['requested_coordinator'] = '10.20.0.11'
        self.assertEqual(assess(rows,self.item(),'formal-block-0')[0], 'invalid')
        rows = self.history()
        rows[2]['returned'] = {'value':'unexpected'}
        self.assertEqual(assess(rows,self.item(),'formal-block-0')[0], 'invalid')

    def test_prewrite_failure_is_not_mr_witness(self):
        rows = [self.row(1,'write',None,'10.20.0.11','P','unavailable')]
        self.assertEqual(assess(rows,self.item(),'formal-block-0')[0], 'inconclusive')

    def test_block_lifecycle_and_replay_guards_without_database(self):
        root = Path(__file__).resolve().parent / ('_batch_' + uuid.uuid4().hex)
        root.mkdir()
        self.addCleanup(self.clean_tree, root)
        run_id = 'formal-block-test'
        folder = root / 'results/raw' / run_id / 'member-b'

        def invoke(*args):
            with patch('sys.argv', ['formal_batch', *args, '--run-id', run_id]):
                batch.main()

        def fake_runner(command, item, run, output, verified=False):
            path = output / (item['history'] + '.jsonl')
            with path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(dict(run_id=run, history_id=item['history'], model=item['model'],
                    operation_id=0 if command == 'prepare' else -1,
                    phase='prepare' if command == 'prepare' else 'setup',
                    actual_statement_cl='ALL',status='ok' if command == 'prepare' else 'connection_error'))+'\n')
            return 0

        with patch.object(batch,'ROOT',root), patch.object(batch,'fingerprint',return_value={'x':'hash'}), \
                patch.object(batch.subprocess,'check_output',return_value='test-commit\n'), \
                patch.object(batch,'call_runner',side_effect=fake_runner):
            invoke('plan','--scenario','node_stop')
            with self.assertRaises(FileExistsError):
                invoke('plan','--scenario','node_stop')
            invoke('prepare')
            self.assertTrue((folder/'data-ready.json').exists())
            with self.assertRaises(FileExistsError):
                invoke('prepare')
            gate = folder/'gate.json'
            batch.save(gate, dict(run_id=run_id,scenario='node_stop',verified=True,
                                verified_utc='test',a_evidence='a',b_evidence='b',c_evidence='c'))
            invoke('execute','--gate',str(gate))
            self.assertTrue((folder/'workload-done.json').exists())
            with self.assertRaises(FileExistsError):
                invoke('execute','--gate',str(gate))
            invoke('summarize')
            self.assertTrue((root/'results/processed'/run_id/'histories.csv').exists())

    @staticmethod
    def clean_tree(root):
        parent = Path(__file__).resolve().parent
        assert root.resolve().parent == parent and root.name.startswith('_batch_')
        for p in sorted(root.rglob('*'), key=lambda x: len(x.parts), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
        root.rmdir()

    def test_dependency_witness_is_retained_as_candidate(self):
        item = dict(history='h',model='mw',scenario='partition_cross_side',write_cl='ONE',read_cl='ONE')
        rows = []
        for i,(operation,key,ip,value) in enumerate([
            ('write','a','10.20.0.11',None),('write','b','10.20.0.13',None),
            ('read','b','10.20.0.13',{'value':'second-write;depends-on=a'}),
            ('read','a','10.20.0.13',None)],1):
            r = self.row(i,operation,value,ip,'U' if i < 3 else 'observer')
            r.update(model='mw',key=key,phase='workload' if i<3 else 'diagnostic',
                     dependency='a' if i==2 else None,fault_verified=True)
            rows.append(r)
        self.assertEqual(assess(rows,item,'formal-block-0')[0], 'candidate_dependency_witness')


if __name__ == '__main__':
    unittest.main()
