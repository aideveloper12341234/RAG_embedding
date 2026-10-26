import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from app.utils.record_utils import RecordUtils
class VectorStore:
    def __init__(self, path=None):
        self.__path = Path(path or os.getenv('LOCAL_SEARCH_DB', '.state/search.sqlite'))
    def execute(self, operation, *, model=None, records=None, embed=None, source_ids=None):
        if operation == 'read':
            return self.__read(model, source_ids)
        if operation == 'publish':
            if not model or not records or not callable(embed): raise ValueError('Publishing requires model, nonempty records and embedding callback')
            return self.__publish(model, records, embed)
        raise ValueError('Supported operations: read, publish')
    def __connect(self):
        self.__path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.__path, timeout=30)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, payload TEXT, vector TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS cache (id TEXT PRIMARY KEY, vector TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)')
        db.commit()
        return db
    def __read(self, model, source_ids):
        if not self.__path.exists(): raise FileNotFoundError('Run index_documents first')
        with closing(self.__connect()) as db:
            db.execute('BEGIN')
            stored = db.execute('SELECT value FROM metadata WHERE key=?', ('model',)).fetchone()
            rows = db.execute('SELECT payload, vector FROM records').fetchall()
        if not stored or stored[0] != model: raise ValueError('Embedding model changed; rebuild the local index')
        allowed = None if source_ids is None else set(source_ids)
        result = [(json.loads(p), json.loads(v)) for p, v in rows]
        return [(p, v) for p, v in result if allowed is None or p['source_id'] in allowed]
    def __publish(self, model, records, embed):
        reused = 0
        with closing(self.__connect()) as db:
            with db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('DELETE FROM records')
                dimensions = None
                for record in records:
                    key = RecordUtils.digest(model + '\n' + record['content'])
                    cached = db.execute('SELECT vector FROM cache WHERE id=?', (key,)).fetchone()
                    vector = json.loads(cached[0]) if cached else embed(record['content'])
                    dimensions = dimensions or len(vector)
                    if not RecordUtils.vector_valid(vector, dimensions): raise ValueError('Invalid embedding vector')
                    reused += int(cached is not None)
                    serialized = json.dumps(vector, allow_nan=False)
                    db.execute('INSERT OR REPLACE INTO cache VALUES (?, ?)', (key, serialized))
                    db.execute('INSERT INTO records VALUES (?, ?, ?)',
                               (record['id'], json.dumps(record), serialized))
                db.execute('INSERT OR REPLACE INTO metadata VALUES (?, ?)', ('model', model))
        return {'records': len(records), 'reused': reused, 'database': str(self.__path)}
if __name__ == '__main__':
    import argparse
    from dotenv import load_dotenv
    from app.document_processing.index_documents import IndexService
    load_dotenv(override=False)
    parser = argparse.ArgumentParser(description='Embed chunks.json and publish the local vector store')
    parser.add_argument('--chunks', default=os.getenv(
        'CK27_CHUNKS_PATH', 'app/document_processing/output/chunks.json'))
    args = parser.parse_args()
    print(json.dumps(IndexService().index(args.chunks, authoritative=True), indent=2))
