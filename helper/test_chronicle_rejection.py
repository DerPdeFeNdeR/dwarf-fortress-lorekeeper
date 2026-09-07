import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chronicles import chapter_input, chapter_key, process_chronicles, recheck_rejected
from process_queue import write_results, load_results
from story_coverage import CoverageError, validate
from test_chronicles import request
from test_cultural_events import telling


class ChronicleRejectionTests(unittest.TestCase):
    def setUp(self):
        self.request = request('draft', year=102)
        event = telling()
        event['performance']['topic']['year'] = 1
        self.request['cultural_events'] = [event]
        self.required = chapter_input(self.request)['required_event_coverage']
        self.text = ('Othdo ò told the story of Laka Elmcloak, a traveller, who became lord of '
                     'The Copper League, a human government, in year one.')

    def test_natural_office_wording_apposition_and_spelled_year(self):
        validate(self.text, self.required, label='Chronicle')
        validate(self.text.replace('told the story of','later told a story about'),self.required,label='Chronicle')

    def test_wrong_or_negated_facts_still_fail(self):
        for text in (self.text.replace('lord','monarch'), self.text.replace('one','eleven'),
                     self.text.replace('one','11'), self.text.replace('became','never became'),
                     self.text.replace('Othdo ò','Laka Elmcloak'),
                     self.text.replace('Copper','Silver')):
            with self.subTest(text=text), self.assertRaises(CoverageError):
                validate(text, self.required, label='Chronicle')

    def test_failed_draft_preserves_candidate_and_previous_story_after_one_correction(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            target=directory/(chapter_key(self.request)+'.chapter.json')
            write_results(target,dict(story='Last good draft.',story_narrator={'name':'Old narrator'}))
            write_results(directory/'request.request.json',self.request)
            candidate='An incomplete tale.'
            with patch('chronicles.run_batch',return_value={'results':[{'text':candidate}]}) as model:
                process_chronicles(save)
                process_chronicles(save)
                self.assertEqual(model.call_count,2)
            state=load_results(target)
            self.assertEqual(state['state'],'failed')
            self.assertEqual(state['story'],'Last good draft.')
            self.assertEqual(state['story_narrator'],{'name':'Old narrator'})
            self.assertIn('Chronicle coverage check',state['error'])
            rejected=load_results(directory/state['rejected_draft_file'])
            self.assertEqual(rejected['text'],candidate)
            self.assertEqual(rejected['missing_event_ids'],['incident:1'])
            self.assertEqual(rejected['status'],'rejected_not_for_display')
            self.assertTrue(rejected['correction_attempted'])
            # An explicitly changed request replaces the bounded diagnostic file,
            # rather than accumulating one file per failed attempt.
            updated=copy.deepcopy(self.request); updated['nonce']='retry'
            write_results(directory/'request.request.json',updated)
            with patch('chronicles.run_batch',return_value={'results':[{'text':'Still incomplete.'}]}):
                process_chronicles(save)
            self.assertEqual(len(list(directory.glob('*.rejected.json'))),1)

    def test_natural_candidate_publishes_successfully(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            write_results(directory/'request.request.json',self.request)
            with patch('chronicles.run_batch',return_value={'results':[{'text':self.text}]}):
                process_chronicles(save)
            state=load_results(directory/(chapter_key(self.request)+'.chapter.json'))
            self.assertEqual(state['state'],'ready')
            self.assertEqual(state['story'],self.text)
            self.assertNotIn('rejected_draft_file',state)

    def test_crash_after_attempt_marker_does_not_restart_generation(self):
        import hashlib
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            path=directory/'request.request.json'
            write_results(path,self.request)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            key=chapter_key(self.request)
            target=directory/(key+'.chapter.json')
            write_results(target,dict(state='processing',request_digest=digest,story='Saved draft.',
                key=key,year=102,kind='draft',site_id=745,updated_at=0))
            write_results(directory/(key+'.rejected.json'),
                          dict(request_digest=digest,correction_attempted=True))
            with patch('chronicles.run_batch') as model:
                process_chronicles(save); process_chronicles(save)
                model.assert_not_called()
            state=load_results(target)
            self.assertEqual(state['state'],'failed')
            self.assertEqual(state['story'],'Saved draft.')

    def test_failed_generation_corrects_once_then_reopen_is_cached(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            write_results(directory/'request.request.json',self.request)
            old=self.text.replace(' in year one','')
            response=json.dumps([dict(event_id='incident:1',sentence_id=0,new=self.text)])
            with patch('chronicles.run_batch',side_effect=[{'results':[{'text':old}]},
                        {'results':[{'text':response}]}]) as model:
                process_chronicles(save); process_chronicles(save)
                self.assertEqual(model.call_count,2)
            state=load_results(directory/(chapter_key(self.request)+'.chapter.json'))
            self.assertEqual(state['state'],'ready')
            self.assertEqual(state['correction_status'],'passed')
            self.assertEqual(state['story'],self.text)

    def test_explicit_recheck_revalidates_candidate_without_model_or_stale_request(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            write_results(directory/'request.request.json',self.request)
            with patch('chronicles.run_batch',return_value={'results':[{'text':self.text}]}), \
                 patch('chronicles.validate_coverage',side_effect=CoverageError(['incident:1'],'Chronicle')):
                process_chronicles(save)
            with patch('chronicles.run_batch') as model:
                result=recheck_rejected(save,chapter_key(self.request))
                model.assert_not_called()
            self.assertEqual(result['status'],'passed')
            state=load_results(directory/(chapter_key(self.request)+'.chapter.json'))
            self.assertEqual(state['story'],self.text)
            self.assertTrue(state['recovered_from_diagnostic'])
            with self.assertRaises(ValueError):
                recheck_rejected(save,chapter_key(self.request))  # Ready chapters are immutable here.
            state['state']='failed'
            write_results(directory/(chapter_key(self.request)+'.chapter.json'),state)
            write_results(directory/'request.request.json',dict(self.request,nonce='changed'))
            with self.assertRaises(ValueError):
                recheck_rejected(save,chapter_key(self.request))

    def test_explicit_victim_first_death_frame_keeps_roles_local(self):
        from story_coverage import requirements
        event=dict(id=7,kind='death',site_name='Testfort',participants=[
            dict(role='victim',name='Urist',reference_status='resolved'),
            dict(role='slayer',name='Feb',reference_status='resolved')])
        required=requirements({'events':[event]},annual=True)
        validate('In Slate, death came to Urist at Testfort when Feb killed him.',required)
        validate('Urist was killed by Feb at Testfort.',required)
        for text in ('Death came to Feb at Testfort when Urist killed him.',
                     'Urist waited. Feb killed him at Testfort.',
                     'death came to Urist at Testfort when Feb never killed him.'):
            with self.assertRaises(CoverageError): validate(text,required)
