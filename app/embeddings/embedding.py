import os
import hashlib
import math
import re
from collections import Counter
from app.embeddings.embedding_records import EmbeddingRecords
class Embedding:
    def __init__(self, model_name=None):
        self.model_name = model_name or 'local-hashed-words-v1'
    def encode(self, texts=None, *, chunks=None):
        if chunks is not None:
            records, skipped = self.__prepare(chunks)
            return {'records': records, 'skipped': skipped, 'model': self.model_name}
        texts = [texts] if isinstance(texts, str) else texts
        if not texts or any(not isinstance(t, str) or not t.strip() for t in texts): raise ValueError('Supply nonempty text strings')
        vectors = [self.__vector(text) for text in texts]
        return {'vectors': vectors, 'model': self.model_name}
    @staticmethod
    def __vector(text):
        # Temporary lexical vectors: replace with the Azure embedding endpoint call
        # and its model identity; rebuild the index when switching to Azure.
        vector = [0.0] * 1024
        terms = re.findall(r'\w+', text.casefold())
        for term, count in Counter(terms or [text.casefold()]).items():
            bucket = int.from_bytes(hashlib.sha256(term.encode('utf-8')).digest()[:8], 'big') % len(vector)
            vector[bucket] += count
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector]
    def __prepare(self, chunks):
        class TokenCounter:
            def encode(self, text, **kwargs):
                return list(text)
        pattern = os.getenv('CK27_CODE_PATTERN') or r'(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9]*-\d+[A-Za-z0-9]*(?![A-Za-z0-9_-])'
        import json
        return EmbeddingRecords.adapt(chunks, os.getenv('CK27_SOURCE_NAMESPACE') or 'local',
                     json.loads(os.getenv('CK27_REQUIRED_METADATA', '{}')),
                     pattern, TokenCounter(),
                     2000)
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('text', nargs='?', default='High pressure alarm')
    result = Embedding().encode(parser.parse_args().text)
    print({'model': result['model'], 'dimensions': len(result['vectors'][0])})
