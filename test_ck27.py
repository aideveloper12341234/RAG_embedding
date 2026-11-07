"""Run chunk creation, local indexing, and retrieval for one query."""

import argparse
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', help='Alarm or question to search for')
    args = parser.parse_args(argv)
    if not args.query.strip():
        parser.error('query must not be empty')

    if not (ROOT / 'app' / 'document_processing' / 'chunk.py').is_file():
        print('Chunk creation requires app/document_processing/chunk.py, which is not present in this checkout.',
              file=sys.stderr)
        return 1

    stages = [
        ('Creating chunks', ['-m', 'app.document_processing.chunk']),
        ('Creating and storing embeddings', ['-m', 'app.storage.vector_store']),
        ('Retrieving results', ['-m', 'app.retrieval.search_service', args.query]),
    ]
    for label, command in stages:
        print(f'\n{label}...', flush=True)
        started = time.perf_counter()
        try:
            result = subprocess.run([sys.executable, *command], cwd=ROOT, check=False)
        except OSError as exc:
            print(f'{label} could not start: {exc}', file=sys.stderr)
            return 1
        if result.returncode:
            print(f'{label} failed (exit code {result.returncode}); stopping.', file=sys.stderr)
            return result.returncode if result.returncode > 0 else 1
        print(f'{label} completed in {time.perf_counter() - started:.2f}s.', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
