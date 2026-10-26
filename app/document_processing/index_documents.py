from app.document_processing.indexer import Indexer
class IndexService:
    def index(self, path, *, authoritative=False):
        from dotenv import load_dotenv
        load_dotenv(override=False)
        return Indexer().index(path, authoritative=authoritative)
if __name__ == '__main__':
    import argparse
    import json
    import os
    from dotenv import load_dotenv
    load_dotenv(override=False)
    parser = argparse.ArgumentParser()
    parser.add_argument('--chunks', default=os.getenv('CK27_CHUNKS_PATH', 'app/document_processing/output/chunks.json'))
    parser.add_argument('--authoritative', action='store_true')
    args = parser.parse_args()
    print(json.dumps(IndexService().index(args.chunks, authoritative=args.authoritative), indent=2))
