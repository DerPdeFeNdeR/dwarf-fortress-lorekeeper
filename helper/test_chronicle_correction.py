import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from chronicle_correction import apply_edits
from chronicles import repair_diagnostic
from story_coverage import CoverageError
from process_queue import load_results


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.old=['Fath told a story about Tholtig becoming monarch in The Letter.',
                  'Urist told a story about Philomena becoming manager in The Palace in year 100.']
        self.new=[self.old[0][:-1]+' in year 1.',self.old[1].replace('Urist','Urist Udiboltar',1)]
        self.ids=['incident:667','incident:680']
        self.required=[dict(event_id=identity,clauses=[[sentence[:-1]]])
                       for identity,sentence in zip(self.ids,self.new)]
        self.text='Other prose remains intact.\n\n'+' '.join(self.old)+'\n\nAn unchanged ending.'
        self.edits=[dict(event_id=i,old=o,new=n) for i,o,n in zip(self.ids,self.old,self.new)]

    def test_missing_topic_year_and_short_teller_are_repaired_locally(self):
        text,result=apply_edits(self.text,json.dumps(self.edits),self.ids,self.required)
        self.assertEqual(text,'Other prose remains intact.\n\n'+' '.join(self.new)+'\n\nAn unchanged ending.')
        self.assertEqual(result['checked_event_ids'],self.ids)

    def test_unrelated_duplicate_ambiguous_and_multisentence_edits_rejected(self):
        variants=[self.edits+[self.edits[0]],[],self.edits[:1],
            [dict(self.edits[0],event_id='other'),self.edits[1]],
            [dict(self.edits[0],old='not present.'),self.edits[1]],
            [dict(self.edits[0],new=self.new[0]+' Extra prose.'),self.edits[1]]]
        for edits in variants:
            with self.subTest(edits=edits),self.assertRaises(ValueError):
                apply_edits(self.text,json.dumps(edits),self.ids,self.required)

    def test_all_other_coverage_rechecked(self):
        required=self.required+[dict(event_id='other',clauses=[['A required unrelated fact']])]
        with self.assertRaises(CoverageError):
            apply_edits(self.text,json.dumps(self.edits),self.ids,required)

    def test_correction_cannot_drop_inline_classifications(self):
        text=self.text.replace('The Letter.','The Letter, a dwarf civilization.')
        edits=[dict(self.edits[0],old=self.old[0].replace('The Letter.','The Letter, a dwarf civilization.')),
               self.edits[1]]
        with self.assertRaisesRegex(ValueError,'removed or reordered'):
            apply_edits(text,json.dumps(edits),self.ids,self.required)

    def test_indexed_edits_do_not_depend_on_copying_source_names(self):
        edits=[dict(event_id=identity,sentence_id=i+1,new=new)
               for i,(identity,new) in enumerate(zip(self.ids,self.new))]
        text,result=apply_edits(self.text,json.dumps(edits),self.ids,self.required)
        self.assertIn(self.new[1],text)
        self.assertEqual(result['checked_event_ids'],self.ids)
        edits[0]['sentence_id']=True
        with self.assertRaises(ValueError):
            apply_edits(self.text,json.dumps(edits),self.ids,self.required)

    def test_attempt_persisted_before_call_and_never_repeated(self):
        with tempfile.TemporaryDirectory() as root:
            directory=Path(root)
            diagnostic=dict(text=self.text,missing_event_ids=self.ids,
                            required_event_coverage=self.required,generation={})
            def generate(*args,**kwargs):
                self.assertTrue(load_results(directory/'key.rejected.json')['correction_attempted'])
                return {'results':[{'text':json.dumps(self.edits)}]}
            with patch('chronicles.run_batch',side_effect=generate) as model:
                text,_=repair_diagnostic(directory,'key',diagnostic)
                self.assertIn('year 1',text)
                with self.assertRaises(ValueError):
                    repair_diagnostic(directory,'key',load_results(directory/'key.rejected.json'))
                self.assertEqual(model.call_count,1)

    def test_offline_correction_stays_bounded_and_original_is_retained(self):
        with tempfile.TemporaryDirectory() as root:
            directory=Path(root)
            diagnostic=dict(text=self.text,missing_event_ids=self.ids,
                            required_event_coverage=self.required,generation={})
            with patch('chronicles.run_batch',side_effect=RuntimeError('offline')):
                with self.assertRaises(RuntimeError): repair_diagnostic(directory,'key',diagnostic)
            stored=load_results(directory/'key.rejected.json')
            self.assertEqual(stored['text'],self.text)
            self.assertEqual(stored['correction_status'],'failed')
            self.assertTrue(stored['correction_attempted'])

    @unittest.skipUnless(os.environ.get('LOREKEEPER_LIVE_CORRECTION_TEST')=='1',
                         'Explicit opt-in: one live insertion-only correction')
    def test_live_indexed_correction(self):
        from codex_batch import run_batch, generation_settings
        from chronicle_correction import correct
        text,coverage=correct(self.text,self.ids,self.required,run_batch,generation_settings(),'test-correction')
        self.assertEqual(coverage['checked_event_ids'],self.ids)
        self.assertTrue(text.startswith('Other prose remains intact.\n\n'))
        self.assertTrue(text.endswith('\n\nAn unchanged ending.'))
        print(text,flush=True)
