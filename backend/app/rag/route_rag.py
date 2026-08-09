from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag.rag_services import RAGService
from app.rag.rag_models import RAGResponse


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)

rag_service = RAGService()


class RAGQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Natural language repository question.",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of semantic seed nodes to retrieve.",
    )


@router.post(
    "/chat",
    response_model=RAGResponse,
    summary="Ask RepoSense GraphRAG",
)
def chat(
    request: RAGQueryRequest,
) -> RAGResponse:

    try:
        return rag_service.answer(
            question=request.question,
            top_k=request.top_k,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"GraphRAG query failed: {type(error).__name__}: {error}",
        ) from error