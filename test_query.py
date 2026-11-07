"""Search the existing CK-27 index with a query from the command line."""

import argparse
import subprocess
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', help='Alarm or question to search for')
    args = parser.parse_args(argv)
    if not args.query.strip():
        parser.error('query must not be empty')
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'app.retrieval.search_service', args.query],
            cwd=Path(__file__).resolve().parent,
            check=False,
        )
    except OSError as exc:
        print(f'Could not start retrieval: {exc}', file=sys.stderr)
        return 1
    return result.returncode if result.returncode >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
