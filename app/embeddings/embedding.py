import os
from functools import lru_cache
from app.embeddings.embedding_records import EmbeddingRecords
class Embedding:
    def __init__(self, model_name=None):
        self.__name = model_name or os.getenv(
            'LOCAL_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    def encode(self, texts=None, *, chunks=None):
        model = self.__load_model(self.__name)
        if chunks is not None:
            records, skipped = self.__prepare(model, chunks)
            return {'records': records, 'skipped': skipped, 'model': self.__name}
        texts = [texts] if isinstance(texts, str) else texts
        if not texts or any(not isinstance(t, str) or not t.strip() for t in texts): raise ValueError('Supply nonempty text strings')
        if any(len(model.tokenizer.encode(t, add_special_tokens=True)) > model.max_seq_length for t in texts): raise ValueError('Text exceeds embedding model limit; split before encoding')
        vectors = model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()
        return {'vectors': vectors, 'model': self.__name}
    @staticmethod
    @lru_cache(maxsize=2)
    def __load_model(name):
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(name, device='cpu')
    def __prepare(self, model, chunks):
        class TokenCounter:
            def encode(self, text, **kwargs):
                return model.tokenizer.encode(text, add_special_tokens=False)
        pattern = os.getenv('CK27_CODE_PATTERN') or r'(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9]*-\d+[A-Za-z0-9]*(?![A-Za-z0-9_-])'
        import json
        return EmbeddingRecords.adapt(chunks, os.getenv('CK27_SOURCE_NAMESPACE') or 'local',
                     json.loads(os.getenv('CK27_REQUIRED_METADATA', '{}')),
                     pattern, TokenCounter(),
                     model.max_seq_length - model.tokenizer.num_special_tokens_to_add(pair=False))
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('text', nargs='?', default='High pressure alarm')
    result = Embedding().encode(parser.parse_args().text)
    print({'model': result['model'], 'dimensions': len(result['vectors'][0])})
