# Local daily indexing

Run the Python scheduler from the project root:

```powershell
python schedule_ck27.py --time 02:00
```

The time is local Windows time. Keep the process running and the computer awake;
missed runs are not replayed. Each run first invokes the host chunker and then
embeds and indexes the resulting complete chunks file. If chunking fails,
indexing is skipped. The host chunker is not included in this checkout.

To run the same workflow once immediately, including for a future Azure job:

```powershell
python schedule_ck27.py --once
```

The one-off command exits nonzero if either stage fails. It uses the existing
chunker output and the vector store's configured `CK27_CHUNKS_PATH` (default
`app/document_processing/output/chunks.json`). Make sure those paths match and
the chunks contain the complete corpus: indexing replaces the current index.
The scheduler writes progress to the console; it does not register a Windows
task, persist run history, or alert on failure. For Azure, provide durable
storage and prevent overlapping jobs as appropriate.
