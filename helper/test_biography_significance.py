import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from biography_significance import assess
from history_view import process_views
from process_queue import write_results, load_results
from test_history_view import record


def addition(token='Talked', tick=1, count=1):
    return dict(kind='change', time=dict(year=102, year_tick=tick),
                thoughts_added=[dict(thought_name=token, emotion_name='INTEREST', count=count)])


class SignificanceTests(unittest.TestCase):
    def test_single_routine_thought_or_one_repeated_category_is_not_a_story(self):
        self.assertIsNone(assess({}, {}, [addition()], []))
        self.assertIsNone(assess({}, {}, [addition(tick=i) for i in range(100)], []))

    def test_varied_minor_developments_need_counts_and_multiple_observations(self):
        tokens = ['Talked', 'WatchPerform', 'AdmireArrangedBuilding']
        rows = [addition(tokens[i % 3], tick=i) for i in range(8)]
        self.assertIsNone(assess({}, {}, rows[:7], []))
        self.assertEqual(assess({}, {}, rows, []), 'accumulated_varied_developments')
        for row in rows: row['time']['year_tick'] = 1
        self.assertIsNone(assess({}, {}, rows, []))

    def test_familiar_death_thought_recall_and_removal_do_not_trigger(self):
        row = addition('WitnessDeath')
        self.assertEqual(assess({}, {}, [row], []), 'new_death_related_experience')
        old = {'events': [row]}
        self.assertIsNone(assess(old, {}, [addition('WitnessDeath', count=2)], []))
        self.assertIsNone(assess({}, {}, [{'thoughts_removed': row['thoughts_added']}], []))

    def test_consequential_events_bypass_routine_threshold(self):
        self.assertEqual(assess({}, {}, [], [{'kind': 'death'}]), 'historical_milestone')
        self.assertEqual(assess({}, {}, [], [{'kind': 'artifact_creation'}]), 'historical_milestone')
        self.assertIsNone(assess({}, {}, [], [{'kind': 'travel'}]))

    def test_stress_and_personality_thresholds_are_measured_from_written_baseline(self):
        self.assertIsNone(assess({'final_stress_band': 0}, {'final_stress_band': 9}, [], []))
        self.assertEqual(assess({'final_stress_band': 0}, {'final_stress_band': -10}, [], []), 'large_stress_change')
        old = {'biography_profile': {'personality_facets': {'BRAVERY': 40}}}
        current = {'biography_profile': {'personality_facets': {'BRAVERY': 49}}}
        self.assertIsNone(assess(old, current, [], []))
        current['biography_profile']['personality_facets']['BRAVERY'] = 50
        self.assertEqual(assess(old, current, [], []), 'personality_change')

    def test_process_defers_without_advancing_story_then_accumulates(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root); views = save/'lorekeeper-views'
            log = save/'lorekeeper-history.jsonl'
            base = record(0, 0)
            log.write_text(json.dumps(base) + '\n')
            write_results(views/'1.request.json', dict(unit_id=1, year=102, tick=0, nonce=0))
            with patch('history_view.run_batch', return_value={'results': [dict(text='An established biography.')]}):
                process_views(save)
            original = load_results(views/'1.json')
            memory = (views/'1.biography-memory.json').read_bytes()
            tokens = ['Talked', 'WatchPerform', 'AdmireArrangedBuilding']
            thoughts = []
            for i in range(1, 9):
                thoughts.append(dict(thought_id=i % 3, emotion_id=1, thought_name=tokens[i % 3], emotion_name='INTEREST'))
                current = record(i, 0)
                current['snapshot']['thoughts'] = list(thoughts)
                with log.open('a') as file: file.write(json.dumps(current) + '\n')
                write_results(views/'1.request.json', dict(unit_id=1, year=102, tick=i, nonce=i))
                with patch('history_view.run_batch', return_value={'results': [dict(text='Varied pleasures gradually filled the days.')]}) as model:
                    process_views(save)
                    result = load_results(views/'1.json')
                    if i < 8:
                        model.assert_not_called()
                        self.assertEqual(result['biography_update']['mode'], 'defer')
                        self.assertEqual(result['story_revision'], original['story_revision'])
                        self.assertEqual(result['story'], original['story'])
                        self.assertEqual((views/'1.biography-memory.json').read_bytes(), memory)
                        # Reopening adds neither evidence nor model calls.
                        write_results(views/'1.request.json', dict(unit_id=1, year=102, tick=i, nonce=i+100))
                        process_views(save)
                        model.assert_not_called()
                    else:
                        self.assertEqual(model.call_count, 1)
                        self.assertEqual(result['biography_update']['mode'], 'append')
                        self.assertTrue(result['story'].startswith(original['story'] + '\n\n'))
