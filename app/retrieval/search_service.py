import asyncio
import os
from time import perf_counter
from app.retrieval.search import Search
from app.storage.documentation_gaps import record_gap

DEFAULT_ESCALATION_GUIDANCE = 'Follow your standard alarm escalation procedure.'


class SearchService:
    def __init__(self, search=None):
        self.__search = search
    async def search(self, query, *, source_ids=None, alarm_id=None):
        started = perf_counter()
        result = await asyncio.to_thread(self.__retrieve, query, source_ids, alarm_id)
        return {**result, 'response_time_ms': round((perf_counter() - started) * 1000, 2)}
    def __retrieve(self, query, source_ids, alarm_id):
        from dotenv import load_dotenv
        load_dotenv(override=False)
        result = (self.__search or Search()).search(query, source_ids=source_ids)
        if result['documents']:
            return result
        record_gap(query, alarm_id)
        guidance = os.getenv('CK23_ESCALATION_GUIDANCE', '').strip() or DEFAULT_ESCALATION_GUIDANCE
        return {**result, 'message': 'Details not available', 'escalation_guidance': guidance}
if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--alarm-id', help='Alarm identifier to record if no document matches')
    args = parser.parse_args()
    print(json.dumps(asyncio.run(SearchService().search(args.query, alarm_id=args.alarm_id)), indent=2, ensure_ascii=False))
