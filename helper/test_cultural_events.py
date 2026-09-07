import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cultural_events import collect, requirements
from heard_stories import anchor
from chronicles import chapter_input, process_chronicles, chapter_key
from process_queue import write_results, load_results
from test_chronicles import request


def telling():
    topic=dict(status='resolved',kind='entity_link_added',link_type='POSITION',year=77,tick=10,
        entity_name='The Copper League',entity_details=dict(entity_type='SiteGovernment',race='human'),
        participants=[dict(role='subject',name='Laka Elmcloak',reference_status='resolved')],
        office=dict(status='resolved',name='lord'))
    performance=dict(performance_type='STORYTELLING_EVENT',year=102,tick=50,site_id=745,
        topic=topic,performers=[dict(name='Othdo ò',reference_status='resolved')])
    return dict(id=1,source_kind='incident',kind='storytelling',site_id=745,year=102,tick=50,
                reference_status='resolved',performance=performance)


class CulturalEventTests(unittest.TestCase):
    def test_deduplicates_local_performance_not_topic_or_listener(self):
        data=request('draft',year=102)
        row=telling()
        data['events']=[dict(id=1,kind='battle',site_id=745,year=102,tick=40)]
        data['cultural_events']=[row,copy.deepcopy(row)]
        payload=chapter_input(data)
        self.assertEqual(len(payload['cultural_events']),1)
        self.assertEqual(len(payload['events']),1) # Same ID, different namespace.
        sentence=payload['required_event_coverage'][0]['sentence']
        self.assertIn('In year 102, Othdo ò told a story',sentence)
        self.assertIn('Laka Elmcloak taking the office of lord',sentence)
        self.assertIn('in year 77',sentence)

    def test_filters_wrong_site_year_future_and_poetry(self):
        for field,value in [('site_id',999),('year',101),('tick',101),('source_kind','history_event')]:
            data=request('draft',year=102); row=telling(); row[field]=value
            data['cultural_events']=[row]
            self.assertEqual(collect(data),[])
        row=telling(); row['performance']['performance_type']='POETRY_RECITAL'
        self.assertEqual(collect(dict(request('draft',year=102),cultural_events=[row])),[])

    def test_no_fabricated_teller_when_lookup_missing(self):
        row=telling(); row['performance']['performers']=[dict(name='Wrong',reference_status='missing')]
        events=collect(dict(request('draft',year=102),cultural_events=[row]))
        sentence=requirements(events)[0]['sentence']
        self.assertIn('unidentified storyteller',sentence)
        self.assertNotIn('Wrong',sentence)

    def test_biography_anchor_includes_resolved_storyteller(self):
        row=telling()['performance']
        story=dict(row,subject_key='history_event:9')
        sentence=anchor({'name':'Brow'},[story])[0]['sentence']
        self.assertIn('Brow heard a story from Othdo ò about Laka Elmcloak',sentence)

    def test_cultural_only_year_calls_model_and_checks_teller(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            data=dict(request('draft',year=102),cultural_events=[telling()])
            write_results(directory/'a.request.json',data)
            def model(items,**kwargs):
                raw=json.loads(items[0]['raw'])
                self.assertEqual(raw['cultural_events'][0]['topic']['entity_details']['race'],'human')
                return dict(results=[dict(text=raw['required_event_coverage'][0]['sentence'])])
            with patch('chronicles.run_batch',side_effect=model): process_chronicles(save)
            result=load_results(directory/(chapter_key(data)+'.chapter.json'))
            self.assertEqual(result['state'],'ready')
            self.assertEqual(result['cultural_event_ids'],['incident:1'])
            self.assertIn('Othdo ò',result['story'])
