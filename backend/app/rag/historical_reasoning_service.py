from app.intelligence.gemini_client import GeminiClient

from app.rag.historical_context_builder import (
    HistoricalContextBuilder,
)
from app.rag.historical_models import HistoricalResponse
from app.rag.historical_prompt_builder import (
    HistoricalPromptBuilder,
)
from app.rag.historical_retriever import (
    HistoricalRetriever,
)
from app.rag.vector_retriever import VectorRetriever


class HistoricalReasoningService:
    """
    End-to-end historical repository reasoning.

    Pipeline:

        User Question
              ↓
        Semantic Retrieval
              ↓
        Class Resolution
              ↓
        Historical Commit Retrieval
              ↓
        Chronological Context
              ↓
        Gemini
              ↓
        Structured HistoricalResponse
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever | None = None,
        historical_retriever: HistoricalRetriever | None = None,
        gemini_client: GeminiClient | None = None,
    ) -> None:

        self.vector_retriever = (
            vector_retriever
            or VectorRetriever()
        )

        self.historical_retriever = (
            historical_retriever
            or HistoricalRetriever()
        )

        self.gemini_client = (
            gemini_client
            or GeminiClient()
        )

    def answer(
        self,
        question: str,
        top_k: int = 5,
    ) -> HistoricalResponse:

        if not question or not question.strip():
            raise ValueError(
                "Historical reasoning question cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        # ----------------------------------------
        # 1. Semantic retrieval
        # ----------------------------------------

        seeds = self.vector_retriever.retrieve_seeds(
            question=question,
            top_k=top_k,
        )

        if not seeds:
            return HistoricalResponse(
                answer=(
                    "No relevant repository entities were found "
                    "for this historical question."
                ),
                confidence="low",
            )

        # ----------------------------------------
        # 2. Resolve relevant Classes
        # ----------------------------------------

        class_ids = (
            self.historical_retriever.resolve_class_ids(
                seeds
            )
        )

        if not class_ids:
            return HistoricalResponse(
                answer=(
                    "Relevant repository entities were found, "
                    "but their historical class context could "
                    "not be resolved."
                ),
                confidence="low",
            )

        # ----------------------------------------
        # 3. Retrieve historical commits
        # ----------------------------------------

        events = (
            self.historical_retriever.retrieve(
                class_ids
            )
        )

        if not events:
            return HistoricalResponse(
                answer=(
                    "No historical commits were found for "
                    "the relevant repository components."
                ),
                confidence="low",
            )

        # ----------------------------------------
        # 4. Build historical context
        # ----------------------------------------

        context = HistoricalContextBuilder.build(
            question=question,
            class_ids=class_ids,
            events=events,
        )

        # ----------------------------------------
        # 5. Build reasoning prompt
        # ----------------------------------------

        prompt = HistoricalPromptBuilder.build(
            question=question,
            context=context,
        )

        # ----------------------------------------
        # 6. Ask Gemini
        # ----------------------------------------

        response = (
            self.gemini_client.generate_structured(
                prompt=prompt,
                response_model=HistoricalResponse,
            )
        )

        # ----------------------------------------
        # 7. Ensure sources come from Neo4j
        # ----------------------------------------

        retrieved_hashes = {
            event["commit_hash"]
            for event in events
            if event.get("commit_hash")
        }

        response.timeline = [
            event
            for event in response.timeline
            if event.commit_hash in retrieved_hashes
        ]

        response.sources = [
            event.commit_hash
            for event in response.timeline
        ]

        return response