import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.document_processing.indexer import Indexer
from app.utils.record_utils import RecordUtils
from app.embeddings.embedding_records import EmbeddingRecords
from app.retrieval.search import Search
from app.storage.vector_store import VectorStore


class Tokens:
    def encode(self, text, **kwargs):
        return list(text)


class LocalEmbeddingStub:
    def encode(self, texts=None, *, chunks=None):
        if chunks is not None:
            records, skipped = EmbeddingRecords.adapt(chunks, 'test', {}, r'P-\d+', Tokens(), 1000)
            return {'records': records, 'skipped': skipped, 'model': 'test'}
        return {'vectors': [[1.0, 0.0]], 'model': 'test'}


class IntegrationTests(unittest.TestCase):
    def test_local_vectors_to_search_without_model_download(self):
        from app.embeddings.embedding import Embedding
        with TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / 'chunks.json'
            path.write_text(json.dumps({'chunks': [
                {'content': 'High pressure alarm pump',
                 'document_metadata': {'document_name': 'pressure.txt'}},
                {'content': 'Office holiday calendar',
                 'document_metadata': {'document_name': 'calendar.txt'}}]}), encoding='utf-8')
            store = VectorStore(Path(directory) / 'vectors.sqlite')
            embedding = Embedding()
            Indexer(embedding, store).index(path, authoritative=True)
            result = Search(embedding, store).search('pressure alarm')
            self.assertEqual(result['documents'][0]['title'], 'pressure.txt')
            self.assertEqual(len(embedding.encode('pressure')['vectors'][0]), 1024)
            self.assertEqual(embedding.encode('pressure'), Embedding().encode('pressure'))

    def test_existing_chunks_to_search_without_modifying_source(self):
        from unittest.mock import patch
        with TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / 'chunks.json'
            raw = json.dumps({'chunks': [{'content': ['P-101 pressure alarm'],
                'sheet_name': 'PJM', 'row_number': 36,
                'cells': [{'column': 1, 'header': 'Alarm', 'value': 'P-101'}],
                'document_metadata': {'document_name': 'alarms.xlsx'}}]}).encode()
            path.write_bytes(raw)
            store = VectorStore(Path(directory) / 'vectors.sqlite')
            embedding = LocalEmbeddingStub()
            Indexer(embedding, store).index(path, authoritative=True)
            with patch.dict('os.environ', {'LOCAL_EMBEDDING_MODEL': 'test'}):
                result = Search(embedding, store).search('P-101')
            self.assertTrue(result['documents'][0]['exact_code'])
            self.assertEqual(result['documents'][0]['locator']['row_number'], 36)
            self.assertEqual(path.read_bytes(), raw)
