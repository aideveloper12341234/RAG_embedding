import json
from pathlib import Path
from app.embeddings.embedding import Embedding
from app.storage.vector_store import VectorStore
class Indexer:
    def __init__(self, embedding=None, store=None):
        self.__embedding = embedding or Embedding()
        self.__store = store or VectorStore()
    def index(self, path, *, authoritative=False):
        if not authoritative: raise ValueError('Confirm complete extraction with --authoritative')
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(raw, dict) or not isinstance(raw.get('chunks'), list): raise ValueError('Expected {"chunks": [...]}')
        chunks = raw['chunks']
        prepared = self.__embedding.encode(chunks=chunks)
        if not prepared['records'] or prepared['skipped']: raise ValueError('Coverage incomplete: empty corpus or textless chunks')
        return self.__store.execute('publish', model=prepared['model'],
                                   records=prepared['records'], embed=lambda text: self.__embedding.encode(text)['vectors'][0])
