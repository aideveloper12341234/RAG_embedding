"""Run once, emit a durable JSON run record, and return a scheduler exit code."""
import argparse
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from app.document_processing.index_documents import IndexService


def main(argv=None):
    load_dotenv(override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chunks', default=os.getenv('CK27_CHUNKS_PATH', 'app/document_processing/output/chunks.json'))
    parser.add_argument('--authoritative', action='store_true', help='Input contains the complete current corpus, not only changes')
    parser.add_argument('--run-dir', default=os.getenv('CK27_RUN_DIR', '.state/runs'))
    args = parser.parse_args(argv)
    run_id = uuid.uuid4().hex
    directory = Path(args.run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{run_id}.json'
    record = {'run_id': run_id, 'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'running'}

    def save():
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record, indent=2), encoding='utf-8')
        temporary.replace(path)

    save()
    try:
        record['result'] = IndexService().index(args.chunks, authoritative=args.authoritative)
        record['status'] = 'succeeded'
        code = 0
    except Exception as exc:
        logging.exception('Index run %s failed', run_id)
        record.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        code = 1
    record['finished_at'] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps(record), flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
