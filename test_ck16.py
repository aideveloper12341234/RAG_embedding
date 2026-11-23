"""Run CK-16 response checks: python test_ck16.py."""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from app.api import router
from app.response_messages import (
    DEFAULT_ESCALATION_GUIDANCE, DETAILS_NOT_AVAILABLE,
    DOCUMENTATION_UNAVAILABLE, INVALID_QUERY, SEARCH_UNAVAILABLE,
)


class CK16Tests(unittest.TestCase):
    def test_responses(self):
        asyncio.run(self.check_responses())

    async def check_responses(self):
        app = FastAPI()
        app.include_router(router)
        base = dict(mode='local_hybrid', documents=[], response_time_ms=1)
        cases = [
            (base, 200, None),
            ({**base, 'message': DETAILS_NOT_AVAILABLE,
              'escalation_guidance': DEFAULT_ESCALATION_GUIDANCE}, 200, DETAILS_NOT_AVAILABLE),
            (FileNotFoundError(), 409, DOCUMENTATION_UNAVAILABLE),
            (ValueError(), 422, INVALID_QUERY),
            (RuntimeError(), 503, SEARCH_UNAVAILABLE),
        ]
        fields = set(base) | {'summary', 'message', 'escalation_guidance'}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            for result, status, message in cases:
                mock = AsyncMock(side_effect=result) if isinstance(result, Exception) else AsyncMock(return_value=result)
                with patch('app.api.SearchService.search', mock):
                    response = await client.post('/api/v1/search', json={'query': 'P-101'})
                with self.subTest(status=status, message=message):
                    body = response.json()
                    self.assertEqual(response.status_code, status)
                    self.assertEqual(set(body), fields)
                    self.assertEqual(body['summary'], '')
                    self.assertEqual(body['message'], message)
                    print(status, message or 'Search completed')
            response = await client.post('/api/v1/search', json={'query': ''})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(set(response.json()), fields)
            self.assertEqual(response.json()['message'], INVALID_QUERY)


if __name__ == '__main__':
    unittest.main(verbosity=2)
