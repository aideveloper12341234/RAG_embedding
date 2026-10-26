# Existing chunks to local search

Keep your existing chunk.py and its output format unchanged. Run commands from the project root, after merging requirements-ck27.txt and .env.example into your existing configuration.

Copy files in this order:

1. app/utils/__init__.py and record_utils.py
2. app/embeddings/__init__.py, embedding_records.py and embedding.py
3. app/storage/__init__.py and vector_store.py
4. app/document_processing/indexer.py and index_documents.py
5. app/retrieval/__init__.py, search.py and search_service.py
6. app/api_models.py and api.py

Preserve existing host package initializers, models and main.py. Add these lines after creating the FastAPI app in main.py:

```python
from app.api import router
app.include_router(router)
```

Run the workflow:

```powershell
python -m pip install -r requirements-ck27.txt
python -m app.document_processing.chunk
python -m app.storage.vector_store
python -m app.api
```

The vector_store command reads app/document_processing/output/chunks.json, prepares separate retrieval records, embeds them with local MiniLM, and atomically publishes .state/search.sqlite. It never rewrites chunks.json. Cached embeddings are reused. Failed builds retain the previous index. Re-run it after generating new chunks. Override the input with --chunks PATH or CK27_CHUNKS_PATH in .env. The first model use downloads public weights; LOCAL_EMBEDDING_MODEL may point to a downloaded model directory. Disabled Azure reference code has been removed to reduce hand typing. Package __init__.py files can be empty; preserve any existing host initializers.

POST /api/v1/search accepts {"query": "high pressure alarm"}. Open http://127.0.0.1:8000/docs to test it. It combines vector and keyword ranking and returns passages and original locators. Search does not rebuild the index. The upload endpoint and upload pipeline have been removed.

For an existing server use its normal startup command instead of python -m app.api. The alternate indexing command remains python -m app.document_processing.index_documents --authoritative.

The host chunker and actual chunks.json are not present in this checkout. Integration tests use representative chunks and deterministic embeddings; actual model-backed testing requires those inputs and model weights. Local scanning is intended for development; Azure reranking, CK-21 calibrated match labels (currently unscored), and CK-25 baseline evaluation remain pending.
