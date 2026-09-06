import json
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch
from history_view import build_timeline, process_views
from process_queue import load_queue, load_results, process_queue, write_results
from codex_batch import run_process
from worker_runtime import worker_runtime


def record(tick, stress):
    return dict(record_type='dwarf_snapshot', ingame_time=dict(year=102,year_tick=tick),
                snapshot=dict(identity=dict(id=1,name='Test ò',profession='Miner'),
                              mental_state=dict(stress=stress),thoughts=[],personality_facets=[]))


class HistoryViewTests(unittest.TestCase):
    def test_process_timeout_is_bounded(self):
        with self.assertRaisesRegex(RuntimeError, 'time limit'):
            run_process([sys.executable, '-c', 'import time; time.sleep(5)'],
                        input='', timeout=0.05, encoding='utf-8')

    def test_duplicate_worker_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with worker_runtime(Path(root)):
                with self.assertRaisesRegex(RuntimeError, 'already owns'):
                    with worker_runtime(Path(root)):
                        self.fail('duplicate worker started')

    def test_stress_trends_coalesce(self):
        events=build_timeline([record(1,0),record(2,-10),record(3,-20)])
        self.assertEqual(len(events),2)
        self.assertEqual(events[1]['count'],2)
        self.assertEqual(events[1]['to_stress'],-20)

    def test_mixed_encodings_and_incomplete_tail(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'q'
            path.write_bytes(b'{"name":"\x95"}\n'+ '{"name":"ò"}\n'.encode()+b'{"partial":')
            self.assertEqual([x['name'] for x in load_queue(path)],['ò','ò'])

    def test_completed_queue_does_not_hit_batch_limit(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'q'
            result=Path(root)/'r'
            path.write_text(''.join(json.dumps(dict(id=str(i),kind='x',raw=str(i)))+'\n' for i in range(70)))
            write_results(result,{str(i):{'text':'done'} for i in range(70)})
            self.assertEqual(process_queue(path,result),0)

    def test_equivalent_requests_each_receive_result(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'q'
            result=Path(root)/'r'
            path.write_text(''.join(json.dumps(dict(id=i,kind='x',raw='same'))+'\n' for i in ('a','b')))
            with patch('process_queue.run_batch',return_value={'results':[dict(id='a',text='done')]}):
                self.assertEqual(process_queue(path,result),2)
            self.assertEqual(load_results(result)['b']['id'],'b')

    def test_model_failure_leaves_timeline_readable(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root)
            views=save/'lorekeeper-views'
            write_results(views/'1.request.json',dict(unit_id=1,year=102,tick=3))
            (save/'lorekeeper-history.jsonl').write_text(json.dumps(record(1,0))+'\n')
            with patch('history_view.run_batch',side_effect=TimeoutError('deadline exceeded')):
                process_views(save)
            self.assertEqual(load_results(views/'1.json')['state'],'failed')
            self.assertTrue(list(views.glob('1.*.0.json')))

    def test_prepares_page_before_model_and_deduplicates_request(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root)
            views=save/'lorekeeper-views'
            write_results(views/'1.request.json',dict(unit_id=1,year=102,tick=3))
            (save/'lorekeeper-history.jsonl').write_text(json.dumps(record(1,0))+'\n')
            def generate(items):
                self.assertTrue(list(views.glob('1.*.0.json')))
                self.assertEqual(load_results(views/'1.json')['state'],'processing')
                return {'results':[dict(id=items[0]['id'],text='Test ò was a miner.')]}
            with patch('history_view.run_batch',side_effect=generate) as model:
                process_views(save)
                process_views(save)
                self.assertEqual(model.call_count,1)
            self.assertEqual(load_results(views/'1.json')['state'],'ready')
