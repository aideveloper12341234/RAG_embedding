import unittest
from fastapi import FastAPI
from pydantic import ValidationError
from app.api import router
from app.api_models import SearchRequest


class ApiTests(unittest.TestCase):
    def test_search_contract(self):
        with self.assertRaises(ValidationError):
            SearchRequest(query=' ')
        app = FastAPI()
        app.include_router(router)
        self.assertEqual(set(app.openapi()['paths']), {'/api/v1/search'})
