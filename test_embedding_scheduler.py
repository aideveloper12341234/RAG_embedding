"""Schedule daily chunking and indexing, or run the same job once."""

import argparse
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run_job():
    for label, module in (
        ('Chunking', 'app.document_processing.chunk'),
        ('Embedding and indexing', 'app.storage.vector_store'),
    ):
        print(f'{datetime.now().isoformat(timespec="seconds")} {label} started', flush=True)
        try:
            result = subprocess.run([sys.executable, '-m', module], cwd=ROOT, check=False)
        except OSError as exc:
            print(f'{label} could not start: {exc}', file=sys.stderr, flush=True)
            return 1
        if result.returncode:
            print(f'{label} failed with exit code {result.returncode}', file=sys.stderr, flush=True)
            return result.returncode if result.returncode > 0 else 1
        print(f'{datetime.now().isoformat(timespec="seconds")} {label} completed', flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--time', default='02:00', help='Daily local time in HH:MM format (default: 02:00)')
    parser.add_argument('--once', action='store_true', help='Run immediately once and exit')
    args = parser.parse_args(argv)
    try:
        scheduled = datetime.strptime(args.time, '%H:%M').time()
    except ValueError:
        parser.error('--time must be in HH:MM format')
    if args.once:
        return run_job()

    while True:
        now = datetime.now()
        next_run = datetime.combine(now.date(), scheduled)
        if next_run <= now:
            next_run += timedelta(days=1)
        print(f'Next run: {next_run.isoformat(sep=" ", timespec="minutes")} (local time)', flush=True)
        while datetime.now() < next_run:
            time.sleep(min(60, max(0, (next_run - datetime.now()).total_seconds())))
        run_job()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\nScheduler stopped.', flush=True)
        sys.exit(0)
