import json
import math
import os
import re
from collections import Counter
from app.embeddings.embedding import Embedding
from app.storage.vector_store import VectorStore
from app.utils.record_utils import RecordUtils
PATTERN = "(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9]*-\\d+[A-Za-z0-9]*(?![A-Za-z0-9_-])"
class Search:
    def __init__(self, embedding=None, store=None):
        self.__embedding = embedding or Embedding()
        self.__store = store or VectorStore()
    def search(self, query, *, source_ids=None):
        if not isinstance(query, str) or not query.strip() or len(query) > 8000: raise ValueError('Query must contain 1–8000 characters')
        top = int(os.getenv('LOCAL_SEARCH_TOP', '5'))
        if not 1 <= top <= 50: raise ValueError('LOCAL_SEARCH_TOP must be between 1 and 50')
        name = os.getenv('LOCAL_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        rows = self.__store.execute('read', model=name, source_ids=source_ids)
        if not rows:
            return {'mode': 'local_hybrid', 'documents': []}
        vector = self.__embedding.encode(query)['vectors'][0]
        if not RecordUtils.vector_valid(vector, len(vector)): raise ValueError('Invalid query embedding')
        if any(not RecordUtils.vector_valid(v, len(vector)) for _, v in rows): raise ValueError('Stored embedding dimensions/values differ; rebuild the index')
        counts = [Counter(re.findall(r'\w+', p['content'].casefold())) for p,v in rows]
        terms = set(re.findall(r'\w+', query.casefold()))
        frequencies = {term: sum(term in count for count in counts) for term in terms}
        average = sum(sum(c.values()) for c in counts) / len(counts)
        lexical, semantic = [], []
        for i, ((p,v), c) in enumerate(zip(rows, counts)):
            score = 0.0
            for term in terms:
                frequency = frequencies[term]
                tf = c[term]
                score += math.log(1 + (len(rows)-frequency+0.5)/(frequency+0.5)) * tf * 2.2 / (tf + 1.2*(0.25+0.75*sum(c.values())/max(average,1)))
            lexical.append((i, score))
            semantic.append((i, sum(a*b for a,b in zip(vector,v))))
        fused = Counter()
        for ranking in (lexical, semantic):
            for rank, (i, score) in enumerate(sorted(ranking, key=lambda x:x[1], reverse=True)[:50], 1):
                if score > 0:
                    fused[i] += 1/(60+rank)
        exact = set(RecordUtils.codes(query, os.getenv('CK27_CODE_PATTERN') or PATTERN))
        for i, (record, _) in enumerate(rows):
            if exact.intersection(record['equipment_codes']):
                fused.setdefault(i, 0.0)
        ordered = sorted(fused, key=lambda i:(bool(exact.intersection(rows[i][0]['equipment_codes'])), fused[i]), reverse=True)
        documents, seen = [], set()
        for i in ordered:
            p = rows[i][0]
            if p['source_id'] in seen:
                continue
            seen.add(p['source_id'])
            documents.append({'source_id': p['source_id'], 'title': p['title'], 'passage': p['content'],
                              'match': 'unscored', 'fusion_score': fused[i],
                              'exact_code': bool(exact.intersection(p['equipment_codes'])), **json.loads(p['payload'])})
        return {'mode': 'local_hybrid', 'documents': documents[:top]}
