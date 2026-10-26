import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.storage.vector_store import VectorStore


class StoreTests(unittest.TestCase):
    def test_cache_scope_and_rollback(self):
        with TemporaryDirectory(dir=Path.cwd()) as directory:
            store = VectorStore(Path(directory) / 'test.sqlite')
            record = {'id': '1', 'source_id': 'allowed', 'content': 'pressure'}
            result = store.execute('publish', model='test', records=[record], embed=lambda _: [1.0, 0.0])
            self.assertEqual(result['reused'], 0)
            def unexpected(_):
                raise AssertionError('Cache should be reused')
            result = store.execute('publish', model='test', records=[record], embed=unexpected)
            self.assertEqual(result['reused'], 1)
            with self.assertRaises(ValueError):
                store.execute('publish', model='test', records=[dict(record, content='changed')],
                              embed=lambda _: [float('nan'), 1])
            self.assertEqual(store.execute('read', model='test')[0][0]['content'], 'pressure')
            self.assertEqual(store.execute('read', model='test', source_ids=[]), [])
            with self.assertRaises(ValueError):
                store.execute('read', model='different')
