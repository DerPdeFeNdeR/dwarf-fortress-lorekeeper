import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from environment import calendar, observations, annual, personal, _read
from chronicles import process_chronicles, chapter_key
from process_queue import write_results, load_results
from test_chronicles import request


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.save = Path(self.temporary.name)
        self.reference = dict(version=1, site_id=745, branch='123-456', year=102,
                              file='745-123-456-102.jsonl')
        self.header = dict(schema_version=1, kind='geography', site_id=745,
                           branch='123-456', year=102, captured_tick=100,
                           geography=dict(status='available', biome='SHRUBLAND_TEMPERATE',
                               region_name='The Quiet Hills', scope='site_anchor_world_tile'))
        self.rows = [dict(kind='weather',year=102,tick=100,weather='None'),
                     dict(kind='weather',year=102,tick=220,weather='Rain'),
                     dict(kind='weather',year=102,tick=33800,weather='Snow')]
        self.path = self.save / 'lorekeeper-environment' / self.reference['file']
        self.path.parent.mkdir()
        self.write_log()

    def write_log(self):
        self.path.write_text(''.join(json.dumps(row)+'\n' for row in [self.header]+self.rows),encoding='utf-8')
        self.reference['bytes'] = self.path.stat().st_size

    def test_calendar_boundaries_no_season_from_invalid_dates(self):
        for tick, month, season in ((0,'Granite','spring'), (100800,'Hematite','summer'),
                                     (201600,'Limestone','autumn'), (302400,'Moonstone','winter')):
            self.assertEqual(calendar(102,tick),dict(year=102,month=month,season=season,day=1))
        for tick in (-1,403200,None,True):
            self.assertIsNone(calendar(102,tick))

    def test_observations_are_dated_not_intervals_and_stop_at_capture(self):
        result = observations(self.save,self.reference,102,300)
        self.assertEqual(len(result['weather']),1)
        self.assertEqual(result['weather'][0]['tick'],220)
        self.assertEqual(result['weather'][0]['weather'],'rain observed')
        self.assertNotIn('duration',result['weather'][0])
        self.assertEqual(result['moon_phase'],'unavailable_unverified')

    def test_high_water_mark_excludes_later_appends(self):
        old = copy.deepcopy(self.reference)
        self.rows.append(dict(kind='weather',year=102,tick=67000,weather='Rain'))
        self.write_log()
        self.assertEqual(observations(self.save,old,102,403199)['weather'][-1]['tick'],33800)

    def test_shared_prefix_cache(self):
        _read.cache_clear()
        observations(self.save,self.reference,102,403199)
        observations(self.save,self.reference,102,403199)
        self.assertEqual(_read.cache_info().hits,1)

    def test_personal_chapters_never_receive_shared_weather(self):
        data=dict(year=102,tick=40000,environment=self.reference)
        intro=personal(self.save,data,'intro')
        self.assertEqual(intro['current_setting']['region_name'],'The Quiet Hills')
        self.assertNotIn('weather',intro)
        old=personal(self.save,data,'000101-11')
        self.assertEqual(old,dict(calendar=dict(year=101,month='Obsidian',season='winter')))
        self.assertNotIn('current_setting',old)

    def test_bad_references_and_other_branches_fail_closed(self):
        for change in (dict(file='../secret'),dict(bytes=2000001),dict(bytes=True),dict(year=101),
                       dict(branch='999-999'),dict(site_id=3)):
            ref=dict(self.reference,**change)
            self.assertNotEqual(observations(self.save,ref,102,403199)['status'],'available')
        data=dict(year=102,captured_year=102,captured_tick=40000,site_id=745,
                  branch='other',environment=self.reference)
        self.assertEqual(annual(self.save,data)['status'],'provenance_mismatch')
        data['environment']=['invalid']
        self.assertEqual(annual(self.save,data)['status'],'provenance_mismatch')

    def test_truncated_malformed_or_backward_rows_do_not_block_generation(self):
        for row in (dict(kind='weather',year=102,tick=10,weather='Rain'),[],{'bad':True}):
            self.rows.append(row); self.write_log()
            self.assertNotEqual(observations(self.save,self.reference,102,403199)['status'],'available')
            self.rows.pop()
        self.write_log(); self.reference['bytes']-=1
        self.assertNotEqual(observations(self.save,self.reference,102,403199)['status'],'available')

    def test_no_retroactive_weather_when_year_has_no_log(self):
        self.assertNotEqual(observations(self.save,self.reference,101,403199)['status'],'available')

    def test_annual_observations_are_bounded_to_one_per_month(self):
        self.rows=[dict(kind='weather',year=102,tick=month*33600+120*i,weather='Rain')
                   for month in range(12) for i in range(10)]
        self.write_log()
        self.assertEqual(len(observations(self.save,self.reference,102,403199)['weather']),12)

    @unittest.skipUnless(os.environ.get('LOREKEEPER_LIVE_ENVIRONMENT_TEST')=='1',
                         'Explicit opt-in: one live atmospheric chronicle')
    def test_live_atmosphere_generation_and_cached_reopen(self):
        data=request('draft',year=102)
        data.update(branch='123-456',captured_tick=40000,environment=self.reference)
        data['events']=[dict(id=1,kind='death',site_id=745,year=102,tick=34000,
            participants=[dict(role='victim',name='Urist',reference_status='resolved')],
            method=dict(death_cause='THIRST'))]
        directory=self.save/'lorekeeper-chronicles'
        write_results(directory/'environment.request.json',data)
        process_chronicles(self.save)
        state=load_results(directory/(chapter_key(data)+'.chapter.json'))
        self.assertEqual(state['state'],'ready',state.get('error'))
        self.assertTrue(state['story'])
        self.assertEqual(state['story_coverage']['checked_event_ids'],[1])
        self.assertNotRegex(state['story'].lower(),r'moonlight|full moon|clear skies|blizzard')
        print('Atmospheric chronicle seconds:',state['generation_seconds'],flush=True)
        print(state['story'],flush=True)
        with patch('chronicles.run_batch') as model:
            process_chronicles(self.save)
            model.assert_not_called()
