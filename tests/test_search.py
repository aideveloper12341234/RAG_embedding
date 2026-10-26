import json
import unittest

from app.retrieval.search import Search


class EmbeddingStub:
    def encode(self, text):
        return {'vectors': [[1.0, 0.0]]}


class StoreStub:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, *args, **kwargs):
        return self.rows


class SearchTests(unittest.TestCase):
    def test_exact_code_survives_candidate_limit(self):
        rows = []
        for i in range(60):
            record = {'source_id': str(i), 'title': 'Alarm', 'content': 'P 101 pressure',
                      'equipment_codes': ['P-101'] if i == 59 else [],
                      'payload': json.dumps({'document_metadata': {}, 'locator': {},
                                             'ck18': {}, 'segment': 0})}
            rows.append((record, [1.0, 0.0]))
        result = Search(EmbeddingStub(), StoreStub(rows)).search('P-101')
        self.assertEqual(result['documents'][0]['source_id'], '59')
        self.assertTrue(result['documents'][0]['exact_code'])

    def test_dimension_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            Search(EmbeddingStub(), StoreStub([({}, [1.0])])).search('pressure')
