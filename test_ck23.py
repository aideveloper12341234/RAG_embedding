"""Check CK-23 against a temporary local index with sample alarm documents."""

import asyncio
import json
import os
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.document_processing.indexer import Indexer
from app.retrieval.search_service import SearchService


class CK23Tests(unittest.TestCase):
    def test_documentation_gaps_and_search_failure(self):
        with TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            index = root / 'search.sqlite'
            gaps = root / 'gaps.sqlite'
            chunks = root / 'chunks.json'
            chunks.write_text(json.dumps({'chunks': [{
                'content': 'P-101 high pressure alarm. Inspect the pump.',
                'document_metadata': {'document_name': 'pump.txt'},
            }]}), encoding='utf-8')
            guidance = 'Sample escalation guidance for the test.'
            with patch.dict(os.environ, {
                'LOCAL_SEARCH_DB': str(index),
                'LOCAL_SEARCH_TOP': '5',
                'CK27_CODE_PATTERN': r'[A-Z]+-\d+',
                'CK27_REQUIRED_METADATA': '{}',
                'CK23_GAP_DB': str(gaps),
                'CK23_ESCALATION_GUIDANCE': guidance,
            }):
                Indexer().index(chunks, authoritative=True)
                service = SearchService()
                found = asyncio.run(service.search('P-101 pressure alarm', alarm_id='incident-1'))
                self.assertTrue(found['documents'][0]['exact_code'])
                self.assertNotIn('message', found)
                self.assertFalse(gaps.exists())

                for query, alarm_id in [('P-999 pressure alarm', 'incident-2'),
                                        ('What is the frost alarm?', None)]:
                    with self.subTest(query=query):
                        result = asyncio.run(service.search(query, alarm_id=alarm_id))
                        self.assertEqual(result['documents'], [])
                        self.assertEqual(result['message'], 'Details not available')
                        self.assertEqual(result['escalation_guidance'], guidance)
                        self.assertGreaterEqual(result['response_time_ms'], 0)

                with patch.dict(os.environ, {'LOCAL_SEARCH_DB': str(root / 'missing.sqlite')}):
                    with self.assertRaises(FileNotFoundError):
                        asyncio.run(service.search('another alarm', alarm_id='incident-3'))

                with closing(sqlite3.connect(gaps)) as database:
                    rows = database.execute(
                        'SELECT alarm_id, query FROM documentation_gaps ORDER BY id'
                    ).fetchall()
                self.assertEqual(rows, [('incident-2', 'P-999 pressure alarm'),
                                        (None, 'What is the frost alarm?')])


if __name__ == '__main__':
    unittest.main(verbosity=2)
