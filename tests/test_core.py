import unittest
from app.utils.record_utils import RecordUtils
from app.embeddings.embedding_records import EmbeddingRecords

PATTERN = r'(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9]*-\d+[A-Za-z0-9]*(?![A-Za-z0-9_-])'

class Tests(unittest.TestCase):
    def test_one_record_per_chunk_and_locator(self):
        chunk = {'content': ['P-001 pressure ≥ 10; do not open'], 'section': 'Alarm',
                 'sheet_name': 'Sheet', 'row_number': 4,
                 'document_metadata': {'document_name': 'a.xlsm'}}
        records, skipped = EmbeddingRecords.adapt([chunk], 'test', {}, PATTERN)
        self.assertFalse(skipped)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['content'], 'Alarm\n' + chunk['content'][0])
        self.assertIn('"row_number": 4', records[0]['payload'])
        self.assertEqual(records[0]['equipment_codes'], ['P-001'])

    def test_empty_and_required(self):
        chunk = {'document_metadata': {'document_name': 'image.pptx'}, 'content': []}
        records, skipped = EmbeddingRecords.adapt([chunk], 'x', {}, PATTERN)
        self.assertFalse(records)
        self.assertEqual(len(skipped), 1)
        with self.assertRaises(ValueError):
            EmbeddingRecords.adapt([chunk], 'x', {'revision': 'document_metadata.revision'}, PATTERN)

    def test_codes_and_filters(self):
        self.assertEqual(RecordUtils.codes('P-101 P-1010 P-001 P-101', PATTERN), ['P-001', 'P-101', 'P-1010'])
        self.assertEqual(RecordUtils.literal("a'b"), "'a''b'")

    def test_vectors(self):
        self.assertTrue(RecordUtils.vector_valid([0.1, 0.2], 2))
        for value in ([float('nan'), 1], [0, 0], [True, 1], [1]):
            self.assertFalse(RecordUtils.vector_valid(value, 2))

    def test_tables_metadata_and_source_preserved(self):
        import copy, json
        chunk = {'content': 'P-101 | 10', 'tables': [{'data': [['P-101', 10], [None, 'high']]}],
                 'document_metadata': {'document_name': 'a.xlsx', 'revision': 2}}
        original = copy.deepcopy(chunk)
        args = ([chunk], 'test', {'revision': 'document_metadata.revision'}, PATTERN)
        records, skipped = EmbeddingRecords.adapt(*args)
        self.assertEqual(''.join(r['content'] for r in records), 'a.xlsx\nP-101 | 10\nP-101 | 10\n | high')
        self.assertEqual(len(records), 1)
        self.assertEqual(json.loads(records[0]['payload'])['ck18'], {'revision': 2})
        self.assertEqual(EmbeddingRecords.adapt(*args), (records, skipped))
        self.assertEqual(chunk, original)

    def test_invalid_configuration_and_chunks(self):
        chunk = {'content': 'text', 'document_metadata': {'document_name': 'a'}}
        for required, chunks in [([], [chunk]), ({'x': ''}, [chunk]),
                ({}, [None]), ({}, [{}]), ({}, [dict(chunk, content=[1])])]:
            with self.subTest(required=required, chunks=chunks), self.assertRaises(ValueError):
                EmbeddingRecords.adapt(chunks, 'test', required, PATTERN)

    def test_long_multiline_chunk_stays_whole(self):
        chunk = {'content': 'first line\n' + 'x' * 3000 + '\nP-101',
                 'document_metadata': {'document_name': 'long.txt'}}
        records, skipped = EmbeddingRecords.adapt([chunk], 'test', {}, PATTERN)
        self.assertFalse(skipped)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['content'], 'long.txt\n' + chunk['content'])
        self.assertEqual(records[0]['equipment_codes'], ['P-101'])
