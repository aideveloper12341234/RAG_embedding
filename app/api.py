import logging
from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from time import perf_counter
from app.api_models import SearchRequest, SearchResponse
from app.response_messages import DOCUMENTATION_UNAVAILABLE, INVALID_QUERY, SEARCH_UNAVAILABLE
from app.retrieval.search_service import SearchService
logger = logging.getLogger(__name__)
def error_response(status, message, started):
    return JSONResponse(status_code=status, content=SearchResponse(
        mode='local_hybrid', documents=[],
        response_time_ms=round((perf_counter() - started) * 1000, 2),
        message=message,
    ).model_dump())


class SearchRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def handle(request):
            started = perf_counter()
            try:
                return await handler(request)
            except RequestValidationError:
                return error_response(422, INVALID_QUERY, started)
        return handle


router = APIRouter(prefix='/api/v1', tags=['search'], route_class=SearchRoute)
@router.post('/search', response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    started = perf_counter()
    try:
        return SearchResponse.model_validate(await SearchService().search(request.query, alarm_id=request.alarm_id))
    except FileNotFoundError:
        return error_response(409, DOCUMENTATION_UNAVAILABLE, started)
    except ValueError:
        return error_response(422, INVALID_QUERY, started)
    except Exception:
        logger.exception('Local search failed')
        return error_response(503, SEARCH_UNAVAILABLE, started)
if __name__ == '__main__':
    import uvicorn
    from fastapi import FastAPI
    from dotenv import load_dotenv
    load_dotenv()
    application = FastAPI(title='Local document search')
    application.include_router(router)
    uvicorn.run(application, host='127.0.0.1', port=8000)
