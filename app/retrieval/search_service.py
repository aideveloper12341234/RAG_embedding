import asyncio
from app.retrieval.search import Search
class SearchService:
    def __init__(self, search=None):
        self.__search = search
    async def search(self, query, *, source_ids=None):
        return await asyncio.to_thread(self.__retrieve, query, source_ids)
    def __retrieve(self, query, source_ids):
        from dotenv import load_dotenv
        load_dotenv(override=False)
        return (self.__search or Search()).search(query, source_ids=source_ids)
if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    args = parser.parse_args()
    print(json.dumps(asyncio.run(SearchService().search(args.query)), indent=2, ensure_ascii=False))
