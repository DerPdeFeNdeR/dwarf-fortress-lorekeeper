import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from chronicles import chapter_input,load_request,process_chronicles,chapter_key
from process_queue import write_results,load_results


def request(kind='final',branch='1-2',year=101):
    return dict(schema_version=1,site_id=745,site_name='Testfort',branch=branch,
                year=year,kind=kind,captured_year=102,captured_tick=100,
                events=[],nonce='1',coverage={'midyear_start':True})


class ChronicleTests(unittest.TestCase):
    def test_filters_other_sites_years_future_draft_events_and_duplicates(self):
        data=request('draft',year=102)
        base=dict(kind='battle',site_id=745,year=102,tick=50,id=1)
        data['events']=[base,base,dict(base,id=2,site_id=999),dict(base,id=3,year=101),dict(base,id=4,tick=101)]
        self.assertEqual([e['id'] for e in chapter_input(data)['events']],[1])

    def test_final_year_and_safe_branch_are_validated(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'request.json'
            for data in (request(year=102),request(branch='../bad'),[]):
                write_results(path,data)
                with self.assertRaises(ValueError): load_request(path)
            write_results(path,request())
            self.assertEqual(load_request(path)['year'],101)

    def test_final_is_immutable_even_if_new_request_changes_content(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            data=request(); write_results(directory/'a.request.json',data)
            process_chronicles(save)
            output=directory/(chapter_key(data)+'.chapter.json')
            before=output.read_bytes()
            write_results(directory/'b.request.json',dict(data,nonce='2',site_name='Changed'))
            process_chronicles(save)
            self.assertEqual(output.read_bytes(),before)

    def test_branches_and_drafts_do_not_overwrite_final(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            for i,data in enumerate((request(),request(branch='2-3'),request('draft',year=102))):
                write_results(directory/f'{i}.request.json',data)
                process_chronicles(save)
            self.assertEqual(len(list(directory.glob('*.chapter.json'))),3)
            self.assertEqual(len(load_results(directory/'index.json')['chapters']),3)

    def test_draft_can_update_and_empty_evidence_does_not_call_model(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'; data=request('draft',year=102)
            write_results(directory/'a.request.json',data)
            with patch('chronicles.run_batch') as model:
                process_chronicles(save)
                output=directory/(chapter_key(data)+'.chapter.json')
                before=load_results(output)['request_digest']
                write_results(directory/'b.request.json',dict(data,nonce='2'))
                process_chronicles(save)
                self.assertNotEqual(load_results(output)['request_digest'],before)
                self.assertTrue(load_results(output)['empty'])
                model.assert_not_called()

    def test_missing_killing_is_not_published_and_failure_does_not_spin(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'; data=request()
            data['events']=[dict(id=1,site_id=745,year=101,tick=1,kind='death',participants=[
                dict(role='slayer',name='Urist',reference_status='resolved'),
                dict(role='victim',name='Domas',reference_status='resolved')])]
            write_results(directory/'a.request.json',data)
            with patch('chronicles.run_batch',return_value={'results':[dict(text='A pleasant year.')]}) as model:
                process_chronicles(save); process_chronicles(save)
                self.assertEqual(model.call_count,1)
            self.assertEqual(load_results(directory/(chapter_key(data)+'.chapter.json'))['state'],'failed')

    def test_explicit_retry_can_recover_a_failed_final(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'; data=request()
            data['events']=[dict(id=1,site_id=745,year=101,tick=1,kind='battle')]
            write_results(directory/'a.request.json',data)
            with patch('chronicles.run_batch',side_effect=RuntimeError('offline')):
                process_chronicles(save)
            output=directory/(chapter_key(data)+'.chapter.json')
            self.assertEqual(load_results(output)['state'],'failed')
            write_results(directory/'b.request.json',dict(data,retry_nonce='2'))
            with patch('chronicles.run_batch',return_value={'results':[dict(text='A battle was recorded.')]}):
                process_chronicles(save)
            self.assertEqual(load_results(output)['state'],'ready')

    def test_invalid_request_does_not_block_valid_chapter(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'; data=request()
            write_results(directory/'a.request.json',[])
            write_results(directory/'b.request.json',data)
            process_chronicles(save)
            self.assertEqual(load_results(directory/(chapter_key(data)+'.chapter.json'))['state'],'ready')

    def test_live_protocol_success_and_name_preservation(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'; data=request()
            data['events']=[dict(id=1,site_id=745,year=101,tick=1,kind='artifact_creation',naming_only=False,
                artifact_name='Ûrist',participants=[dict(role='creator',name='Dòmas',reference_status='resolved')])]
            write_results(directory/'a.request.json',data)
            def generate(items,**kwargs):
                payload=json.loads(items[0]['raw'])
                return {'results':[dict(text=payload['required_event_coverage'][0]['sentence'])]}
            with patch('chronicles.run_batch',side_effect=generate): process_chronicles(save)
            state=load_results(directory/(chapter_key(data)+'.chapter.json'))
            self.assertEqual(state['state'],'ready')
            self.assertIn('Ûrist',state['story'])
            self.assertEqual(state['story_coverage']['checked_event_ids'],[1])
