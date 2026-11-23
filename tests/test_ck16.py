import unittest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import router

class CK16Tests(unittest.TestCase):
    def test_all_outcomes_share_contract(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        fields = {'mode', 'documents', 'response_time_ms', 'summary', 'message', 'escalation_guidance'}
        cases = [
            ({'mode': 'local_hybrid', 'documents': [], 'response_time_ms': 1}, 200),
            ({'mode': 'local_hybrid', 'documents': [], 'response_time_ms': 1, 'message': 'Details not available.', 'escalation_guidance': 'Call operations.'}, 200),
            (FileNotFoundError(), 409), (ValueError(), 422), (RuntimeError(), 503),
        ]
        for result, status in cases:
            with self.subTest(status=status, result=result):
                mock = AsyncMock(side_effect=result) if isinstance(result, Exception) else AsyncMock(return_value=result)
                with patch('app.api.SearchService.search', mock):
                    response = client.post('/api/v1/search', json={'query': 'P-101'})
                self.assertEqual(response.status_code, status)
                self.assertEqual(set(response.json()), fields)
                self.assertEqual(response.json()['summary'], '')
        for payload in [{'query': ''}, {}, {'query': 'alarm', 'unexpected': True}]:
            response = client.post('/api/v1/search', json=payload)
            self.assertEqual(response.status_code, 422)
            self.assertEqual(set(response.json()), fields)
