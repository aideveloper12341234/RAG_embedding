from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field
class SearchRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=8000)
class SearchDocument(BaseModel):
    source_id: str
    title: str
    passage: str
    match: Literal['unscored']
    fusion_score: float = Field(ge=0, allow_inf_nan=False)
    exact_code: bool
    document_metadata: dict[str, Any]
    locator: dict[str, Any]
    ck18: dict[str, Any]
    segment: int = Field(ge=0)
class SearchResponse(BaseModel):
    mode: Literal['local_hybrid']
    documents: list[SearchDocument]
