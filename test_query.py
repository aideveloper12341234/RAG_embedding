"""Search the existing CK-27 index through the search API."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


async def search(query, alarm_id):
    import httpx
    from fastapi import FastAPI

    from app.api import router

    app = FastAPI()
    app.include_router(router)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://localhost') as client:
        return await client.post('/api/v1/search', json={'query': query, 'alarm_id': alarm_id})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', help='Alarm or question to search for')
    parser.add_argument('--alarm-id', help='Alarm identifier to record if no document matches')
    args = parser.parse_args(argv)

    # Keep relative index and log paths anchored to the script directory.
    original_directory = Path.cwd()
    try:
        os.chdir(Path(__file__).resolve().parent)
        response = asyncio.run(search(args.query, args.alarm_id))
    finally:
        os.chdir(original_directory)

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    if response.is_error:
        print(f'HTTP {response.status_code}', file=sys.stderr)
        return 2 if response.status_code == 422 and not args.query.strip() else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
