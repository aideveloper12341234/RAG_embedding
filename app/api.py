import logging
from fastapi import APIRouter, HTTPException
from app.api_models import SearchRequest, SearchResponse
from app.retrieval.search_service import SearchService
logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/v1', tags=['search'])
@router.post('/search', response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    try:
        return SearchResponse.model_validate(await SearchService().search(request.query))
    except FileNotFoundError:
        raise HTTPException(409, 'Search index missing; run python -m app.storage.vector_store') from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    except Exception:
        logger.exception('Local search failed')
        raise HTTPException(503, 'Local search is unavailable') from None
if __name__ == '__main__':
    import uvicorn
    from fastapi import FastAPI
    from dotenv import load_dotenv
    load_dotenv()
    application = FastAPI(title='Local document search')
    application.include_router(router)
    uvicorn.run(application, host='127.0.0.1', port=8000)
