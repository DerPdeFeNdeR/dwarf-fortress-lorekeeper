import copy
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chronicles import CHRONICLE_CONTEXT, chapter_input, process_chronicles, chapter_key
from process_queue import write_results, load_results
from fortress_calendar import MONTHS, MONTH_TICKS
from story_coverage import CoverageError, validate
from test_chronicles import request
from test_cultural_events import telling


class ChronicleProseTests(unittest.TestCase):
    def setUp(self):
        self.data = request('draft', year=102)
        self.data['captured_tick'] = 180000
        rows = []
        for index, teller in enumerate(('Othdo ò', 'Urist', 'Doren')):
            row = telling()
            row.update(id=index+1, tick=MONTHS.index('Hematite')*MONTH_TICKS+index)
            row['performance'].update(tick=row['tick'],
                performers=[dict(name=teller, reference_status='resolved')])
            rows.append(row)
        self.data['cultural_events'] = rows
        self.required = chapter_input(self.data)['required_event_coverage']

    def test_shared_month_context_inline_classification_and_varied_transitions(self):
        text = ('Hematite brought tales. Othdo ò recounted a tale about Laka Elmcloak '
                'taking the office of lord in The Copper League, a human government, in year 77. '
                'Urist told a tale of Laka Elmcloak taking the office of lord in The Copper League in 77. '
                'Doren recounted the story of Laka Elmcloak taking the office of lord in The Copper League in year 77.')
        result = validate(text, self.required)
        self.assertEqual(result['checked_event_ids'], ['incident:1','incident:2','incident:3'])
        self.assertEqual(result['method'], 'bounded_factual_clauses')
        self.assertEqual(text.count('Hematite'), 1)

    def test_missing_or_wrong_teller_subject_and_topic_date_fail(self):
        text = self.required[0]['sentence']
        for wrong in (text.replace('Othdo ò', 'Stranger'), text.replace('lord', 'king'),
                      text.replace('77', '78'), text.replace('taking', 'refusing')):
            with self.assertRaises(CoverageError):
                validate(wrong, self.required[:1])

    def test_scattered_names_and_a_different_tellers_sentence_are_not_coverage(self):
        row = self.required[0]
        for separator in ('. ', '\n\n'):
            text = ('Othdo ò told a story about something else' + separator +
                    'Urist told a story about Laka Elmcloak taking the office of lord '
                    'in The Copper League in year 77.')
            with self.assertRaises(CoverageError):
                validate(text, [row])

    def test_all_tellings_remain_required_even_when_topics_repeat(self):
        with self.assertRaises(CoverageError):
            validate(self.required[0]['sentence'], self.required)

    def test_qwen_storytelling_transitions_keep_all_roles_and_dates(self):
        text = ('Othdo ò told a story about Laka Elmcloak becoming lord of The Copper League in 77. '
                'Urist followed with a tale of Laka Elmcloak becoming lord of The Copper League in 77. '
                'Doren, too, recounted the story of Laka Elmcloak becoming lord of The Copper League in 77.')
        validate(text, self.required)
        for old, new in [('Urist followed', 'Stranger followed'),
                         ('Doren, too,', 'Doren, never,'),
                         ('becoming lord', 'refusing to become lord'),
                         ('in 77', 'in 78')]:
            with self.subTest(new=new), self.assertRaises(CoverageError):
                validate(text.replace(old, new), self.required)

    def test_history_clause_keeps_slayer_and_victim_roles(self):
        data = copy.deepcopy(self.data)
        data['cultural_events'] = []
        data['events'] = [dict(id=9, kind='death', site_id=745, year=102,
            tick=MONTHS.index('Hematite')*MONTH_TICKS,
            participants=[dict(role='slayer', name='Feb', reference_status='resolved'),
                          dict(role='victim', name='Child', reference_status='resolved')])]
        required = chapter_input(data)['required_event_coverage']
        validate('By Hematite, Feb killed Child; grief followed.', required)
        with self.assertRaises(CoverageError):
            validate('By Hematite, Child killed Feb.', required)

    def test_prompt_does_not_reinstate_verbatim_sentence_templates(self):
        self.assertIn('one natural month-setting phrase', CHRONICLE_CONTEXT)
        self.assertIn('At FIRST mention', CHRONICLE_CONTEXT)
        self.assertIn('NOT mandatory wording', CHRONICLE_CONTEXT)
        self.assertNotIn('sentence verbatim', CHRONICLE_CONTEXT)

    @unittest.skipUnless(os.environ.get('LOREKEEPER_LIVE_CHRONICLE_PROSE_TEST') == '1',
                         'Explicit opt-in: one live grouped-month chronicle')
    def test_live_grouped_month_with_inline_subject_context(self):
        from test_narration import voice
        data = copy.deepcopy(self.data)
        data.update(schema_version=2, narrator=voice())
        for index, row in enumerate(data['cultural_events']):
            row['performance']['topic']['entity_name'] = (
                'The Copper League', 'The Silver League', 'The Granite League')[index]
        self.assertTrue(all(e['month']=='Hematite' for e in chapter_input(data)['cultural_events']))
        with tempfile.TemporaryDirectory() as root:
            save = Path(root)
            directory = save / 'lorekeeper-chronicles'
            write_results(directory/'a.request.json', data)
            process_chronicles(save)
            state = load_results(directory/(chapter_key(data)+'.chapter.json'))
            if state.get('rejected_draft_file'):
                print(load_results(directory/state['rejected_draft_file']), flush=True)
            self.assertEqual(state['state'], 'ready', state.get('error'))
            text = state['story']
            print('Grouped-month chronicle seconds:', state['generation_seconds'], flush=True)
            print(text, flush=True)
            self.assertIn('Hematite', text)
            # Editorial preferences are review signals, not factual failures.
            style_notes = []
            if len(re.findall(r'(?im)(?:^|[.!?]\s+)In Hematite\b', text)) > 1:
                style_notes.append('Repeated month opening')
            for entity in ('The Copper League', 'The Silver League', 'The Granite League'):
                position = text.index(entity)
                nearby = text[max(0, position-60):position+len(entity)+160].lower()
                if not all(word in nearby for word in ('human', 'government')):
                    style_notes.append('Missing nearby classification for ' + entity)
            print('Editorial review notes:', style_notes, flush=True)
            self.assertEqual(len(state['story_coverage']['checked_event_ids']), 3)
            with patch('chronicles.run_batch') as model:
                process_chronicles(save)
                model.assert_not_called()
