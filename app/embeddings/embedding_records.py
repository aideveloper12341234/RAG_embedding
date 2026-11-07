import json
from app.utils.record_utils import RecordUtils


class EmbeddingRecords:
    @staticmethod
    def adapt(chunks, namespace, required, pattern):
        if not isinstance(required, dict) or any(not isinstance(path, str) or not path for path in required.values()):
            raise ValueError('Required metadata must map names to nonempty dotted paths')
        records, skipped = [], []
        for ordinal, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                raise ValueError(f'Chunk {ordinal} must be an object')
            metadata = chunk.get('document_metadata') or {}
            if not isinstance(metadata, dict) or not metadata.get('document_name'):
                raise ValueError(f'Chunk {ordinal} has invalid document metadata')
            mapped = {}
            for key, path in required.items():
                value = chunk
                for name in path.split('.'):
                    value = value.get(name) if isinstance(value, dict) else None
                mapped[key] = value
            if any(value is None or value == '' for value in mapped.values()):
                raise ValueError(f'Chunk {ordinal} is missing configured CK-18 metadata')
            content = chunk.get('content') or []
            content = [content] if isinstance(content, str) else content
            if not isinstance(content, list) or not all(isinstance(value, str) for value in content):
                raise ValueError('Chunk content must be text or a list of text')
            parts = [value for value in content if value.strip()]
            for table in chunk.get('tables') or []:
                rendered = '\n'.join(' | '.join('' if value is None else str(value) for value in row)
                                     for row in table.get('data', []))
                if rendered and rendered not in '\n'.join(parts):
                    parts.append(rendered)
            if not parts:
                skipped.append({'ordinal': ordinal, 'reason': 'no searchable text', 'name': metadata['document_name']})
                continue
            title = str(chunk.get('section') or metadata['document_name'])
            text = title + '\n' + '\n'.join(parts)
            locator = {key: chunk[key] for key in ('pages', 'slide_number', 'sheet_name', 'row_number', 'images') if key in chunk}
            source = str(metadata.get('source_id') or metadata.get('source_uri') or metadata['document_name'])
            source_id = RecordUtils.digest(namespace + '\n' + source)
            records.append({'id': RecordUtils.digest(f'{source_id}:{ordinal}:0'),
                            'source_id': source_id, 'title': title, 'content': text,
                            'equipment_codes': RecordUtils.codes(text, pattern),
                            'payload': json.dumps({'document_metadata': metadata, 'locator': locator,
                                                   'ck18': mapped, 'segment': 0}, ensure_ascii=False)})
        return records, skipped
