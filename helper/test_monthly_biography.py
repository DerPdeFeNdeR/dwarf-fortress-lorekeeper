import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from monthly_biography import month_key, partition, title, process, read_json, chapter_text
from test_history_view import record
from history_view import process_views
from process_queue import write_results


class MonthlyBiographyTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.directory = Path(self.root.name)
        self.records = [record(10, 0)]
        self.state = dict(request=dict(unit_id=1, year=102, tick=120000), revision='revision',
                          generation={}, timings={}, story='Legacy memoire')
        self.payload = dict(identity=dict(id=1, name='Elda ò'), biography_profile={}, events=[],
                            historical_episodes=dict(events=[]), life_events=dict(events=[]), heard_stories=[])
        self.calls = []

    def generate(self, items, **kwargs):
        import json
        raw = json.loads(items[0]['raw'])
        self.calls.append(raw)
        text = 'Elda ò found much to ponder. ' + ' '.join(r['sentence'] for r in raw['required_event_coverage'])
        return dict(results=[dict(text=text, id=items[0]['id'])])

    def run_book(self):
        process(self.directory, self.state, self.payload, self.records, {}, self.generate)

    def event(self, year=102, tick=34000, identity=1):
        return dict(id=identity, source_key=f'history_event:{identity}', kind='mood_change',
                    time=dict(year=year, tick=tick), subject_roles=['subject'])

    def test_calendar_boundaries_and_unknown_dates(self):
        self.assertEqual(month_key(dict(year=102, tick=33599)), '000102-00')
        self.assertEqual(month_key(dict(year=102, year_tick=33600)), '000102-01')
        self.assertEqual(title('000102-11'), 'Year 102 / Obsidian')
        self.assertEqual(month_key(dict(year=103, tick=0)), '000103-00')
        for value in ({'year':102}, {'year':102,'tick':403200}, {'year':102,'tick':-1}):
            self.assertIsNone(month_key(value))

    def test_month_is_one_paragraph_without_losing_accents_or_facts(self):
        prose = 'Elda ò remembered.\r\n\r\nMomuz died.\n\tShe persevered.\u2029Life continued.'
        self.assertEqual(chapter_text('000102-01', prose),
                         'Elda ò remembered. Momuz died. She persevered. Life continued.')
        self.assertEqual(chapter_text('intro', prose), prose)

    def test_introduction_then_months_descending_across_years(self):
        self.payload['historical_episodes']['events'] = [self.event(), self.event(year=101,identity=2)]
        self.run_book()
        self.assertEqual(self.calls[0]['chapter_title'], 'Introduction')
        self.run_book(); self.run_book()
        self.assertEqual([c['key'] for c in self.state['chapters']], ['intro','000102-01','000101-01'])

    def test_heard_story_uses_listening_date_not_subject_date(self):
        self.payload['heard_stories'] = [dict(subject_key='history_event:9',
            heard_time=dict(year=102,tick=110000), topic=dict(year=83,tick=100))]
        groups = partition(self.payload, self.state['request'])
        self.assertIn('000102-03', groups)
        self.assertNotIn('000083-00', groups)

    def test_undated_and_future_events(self):
        self.payload['historical_episodes']['events'] = [self.event(tick=130000), self.event(tick=None,identity=2)]
        # Unknown ticks are not compared against valid integers.
        groups = partition(self.payload, self.state['request'])
        self.assertEqual(list(groups), ['intro'])
        self.assertEqual(len(groups['intro']), 1)

    def test_quiet_month_and_reopen_make_no_extra_calls(self):
        self.run_book()
        self.assertEqual(len(self.calls), 1)
        self.run_book()
        self.state['request']['tick'] += 33600
        self.run_book()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual([c['key'] for c in self.state['chapters']], ['intro'])

    def test_weather_reference_alone_does_not_rewrite_or_create_a_chapter(self):
        self.run_book()
        self.state['request']['environment']=dict(file='new-weather-log',bytes=999)
        self.run_book()
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.state['biography_update']['reason'],'no_significant_developments')

    def test_writer_upgrade_revises_once_and_keeps_old_revision(self):
        with patch('monthly_biography.HISTORIAN_CONTEXT','Old third-person historian'):
            self.run_book()
        old=self.state['chapters'][0]['file']
        self.run_book()
        self.assertEqual(len(self.calls),2)
        self.assertTrue((self.directory/old).exists())
        self.run_book()
        self.assertEqual(len(self.calls),2)

    def test_one_chapter_per_pass_and_same_month_replaced(self):
        self.payload['historical_episodes']['events'] = [self.event()]
        self.run_book()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.state['state'], 'processing')
        first_file = self.state['chapters'][0]['file']
        self.run_book()
        self.assertEqual(self.state['state'], 'ready')
        self.payload['historical_episodes']['events'].append(self.event(tick=35000,identity=2))
        self.run_book()
        self.assertEqual(len(self.state['chapters']), 2)
        self.assertTrue((self.directory / first_file).exists())
        book = read_json(self.directory / '1.monthly-book.json')
        self.assertEqual(len(book['chapters']['000102-01']['written']), 2)

    def test_closed_month_stable_when_profile_event_evicted(self):
        self.payload['historical_episodes']['events'] = [self.event()]
        self.run_book(); self.run_book()
        before = copy.deepcopy(self.state['chapters'])
        self.payload['historical_episodes']['events'] = []
        self.run_book()
        self.assertEqual(self.state['chapters'], before)
        self.assertEqual(len(self.calls), 2)

    def test_failed_generation_does_not_advance_written_checkpoint(self):
        self.run_book()
        self.payload['historical_episodes']['events'] = [self.event()]
        def fail(*args, **kwargs):
            raise RuntimeError('offline')
        with self.assertRaises(RuntimeError):
            process(self.directory,self.state,self.payload,self.records,{},fail)
        book = read_json(self.directory / '1.monthly-book.json')
        self.assertEqual(book['chapters']['000102-01']['written'], {})
        self.assertTrue(book['chapters']['intro']['file'])
        self.run_book()
        self.assertEqual(self.state['state'], 'ready')

    def test_reversal_archives_book_without_merging(self):
        self.run_book()
        self.state['request']['tick'] = 5
        self.records.append(record(5, 0))
        self.run_book()
        self.assertEqual(len(list(self.directory.glob('*.monthly-archive.*.json'))), 1)
        self.assertEqual(len(self.calls), 2)

    def test_old_knowledge_book_is_archived_without_seeding_new_prose(self):
        self.run_book()
        path = self.directory / '1.monthly-book.json'
        book = read_json(path)
        book['version'] = 1
        write_results(path, book)
        self.run_book()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(list(self.directory.glob('*.monthly-archive.*.json'))), 1)
        self.assertNotIn('Elda ò found much to ponder.', json.dumps(self.calls[-1], ensure_ascii=False))

    def test_same_story_next_month_is_not_new_chapter(self):
        self.payload['heard_stories'] = [dict(subject_key='history_event:9',
            heard_time=dict(year=102,tick=34000), topic=dict(year=83,tick=100))]
        self.run_book(); self.run_book()
        self.payload['heard_stories'][0]['heard_time']['tick'] = 70000
        self.run_book()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(self.state['chapters']), 2)

    def test_worker_protocol_resumes_chapters_and_reuses_finished_request(self):
        save = self.directory
        views = save / 'lorekeeper-views'
        later = record(34000, 0)
        later['snapshot']['thoughts'] = [dict(thought_id='WitnessDeath',emotion_id='HORROR')]
        (save / 'lorekeeper-history.jsonl').write_text('\n'.join(json.dumps(r) for r in [self.records[0],later])+'\n')
        request = dict(self.state['request'], monthly_version=1)
        write_results(views / '1.request.json', request)
        with patch('history_view.run_batch', side_effect=self.generate) as model:
            process_views(save)
            self.assertEqual(read_json(views/'1.json')['state'],'processing')
            process_views(save)
            self.assertEqual(read_json(views/'1.json')['state'],'ready')
            process_views(save)
            write_results(views/'1.request.json', dict(request, nonce=2))
            process_views(save)
            self.assertEqual(model.call_count, 2)
        state = read_json(views/'1.json')
        self.assertEqual([c['title'] for c in state['chapters']], ['Introduction','Year 102 / Slate'])

    @unittest.skipUnless(os.environ.get('LOREKEEPER_LIVE_MONTHLY_TEST') == '1',
                         'Explicit opt-in: two authenticated model calls in an isolated save')
    def test_live_monthly_generation_and_cached_reopen(self):
        save = self.directory
        views = save / 'lorekeeper-views'
        first, later = record(10, 0), record(34000, 0)
        first['snapshot']['thoughts'] = [dict(thought_id=1,emotion_id=1,
            thought_name='SatisfiedAtWork',emotion_name='SATISFACTION')]
        later['snapshot']['thoughts'] = first['snapshot']['thoughts'] + [dict(thought_id=2,
            emotion_id=2,thought_name='WitnessDeath',emotion_name='HORROR')]
        (save/'lorekeeper-history.jsonl').write_text('\n'.join(json.dumps(r) for r in [first,later])+'\n')
        request = dict(unit_id=1,year=102,tick=35000,nonce=1,monthly_version=1)
        write_results(views/'1.request.json', request)
        process_views(save)
        state=read_json(views/'1.json')
        self.assertEqual(state['state'],'processing',state.get('error'))
        self.assertEqual(state['chapters'][0]['key'],'intro')
        self.assertRegex(state['story'], r'\b(I|my|My)\b')
        print('Introduction generation seconds:',state['timings']['generation_seconds'],flush=True)
        process_views(save)
        state=read_json(views/'1.json')
        self.assertEqual(state['state'],'ready',state.get('error'))
        self.assertEqual(len(state['chapters']),2)
        self.assertEqual([c['key'] for c in state['chapters']],['intro','000102-01'])
        chapter=read_json(views/state['chapters'][1]['file'])
        self.assertNotIn('\n',chapter['text'])
        self.assertRegex(chapter['text'], r'\b(I|my|My)\b')
        print('Monthly generation seconds:',state['timings']['generation_seconds'],flush=True)
        write_results(views/'1.request.json',dict(request,nonce=2))
        with patch('history_view.run_batch') as model:
            process_views(save)
            model.assert_not_called()
