import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.jobs.daily_index import main


def test_success_records_result_and_authoritative_flag():
    with TemporaryDirectory(dir=Path.cwd()) as directory:
        with patch('app.jobs.daily_index.IndexService') as service:
            service.return_value.index.return_value = {'records': 2}
            assert main(['--chunks', 'complete.json', '--authoritative', '--run-dir', directory]) == 0
            service.return_value.index.assert_called_once_with('complete.json', authoritative=True)
        record = json.loads(next(Path(directory).glob('*.json')).read_text())
        assert record['status'] == 'succeeded'
        assert record['result']['records'] == 2
        assert record['finished_at']


def test_failure_is_persisted_and_returns_nonzero():
    with TemporaryDirectory(dir=Path.cwd()) as directory:
        with patch('app.jobs.daily_index.IndexService') as service:
            service.return_value.index.side_effect = ValueError('incomplete corpus')
            assert main(['--run-dir', directory]) == 1
        record = json.loads(next(Path(directory).glob('*.json')).read_text())
        assert record['status'] == 'failed'
        assert record['error_type'] == 'ValueError'

