import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


_append_lock = Lock()


def record_gap(query: str, alarm_id: str | None) -> None:
    path = Path(os.getenv('CK23_GAP_LOG') or '.state/documentation_gaps.txt')
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'alarm_id': alarm_id,
        'query': query,
    }
    with _append_lock, path.open('a', encoding='utf-8') as log:
        log.write(json.dumps(entry, ensure_ascii=False) + '\n')
