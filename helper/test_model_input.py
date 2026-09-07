import json
import unittest
from model_input import compact_raw


def expand(value):
    if isinstance(value, dict):
        if set(value) == {'record_schemas', 'record_rows'}:
            return [dict(zip(value['record_schemas'][row[0]], [expand(v) for v in row[1:]]))
                    for row in value['record_rows']]
        if set(value) == {'record_columns', 'record_rows'}:
            return [dict(zip(value['record_columns'], [expand(v) for v in row]))
                    for row in value['record_rows']]
        return {k: expand(v) for k, v in value.items()}
    return [expand(v) for v in value] if isinstance(value, list) else value


class ModelInputTests(unittest.TestCase):
    def test_compaction_preserves_all_facts_nulls_counts_and_names(self):
        data = {'events': [dict(person_name='Minkot ò', event_year=102,
                                reference_status='resolved', count=i, missing=None)
                            for i in range(12)]}
        raw = json.dumps(data, ensure_ascii=False)
        result = compact_raw(raw)
        self.assertLess(len(result), len(raw) * .7)
        self.assertEqual(expand(json.loads(result)), data)

    def test_distinct_shapes_and_plain_text_remain_supported(self):
        value = [{'reference_status': None, 'event_name': 'Test'},
                 {'reference_status': 'resolved', 'figure_name': 'Urist ò'},
                 {'event_name': 'Death', 'event_year': -1}] * 12
        packed = compact_raw(json.dumps(value))
        self.assertIn('record_schemas', packed)
        self.assertEqual(expand(json.loads(packed)), value)
        self.assertEqual(compact_raw('A dwarf enjoyed a meal.'), 'A dwarf enjoyed a meal.')
