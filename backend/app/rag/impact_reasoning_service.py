from app.intelligence.gemini_client import GeminiClient

from app.rag.impact_context_builder import (
    ImpactContextBuilder,
)
from app.rag.impact_models import ImpactResponse
from app.rag.impact_prompt_builder import (
    ImpactPromptBuilder,
)
from app.rag.impact_retriever import ImpactRetriever
from app.rag.vector_retriever import VectorRetriever


class ImpactReasoningService:
    """
    End-to-end repository impact reasoning.

    Pipeline:

        User Question
              ↓
        Vector Retrieval
              ↓
        Target Seed
              ↓
        Neo4j Impact Retrieval
              ↓
        Evidence Context
              ↓
        Gemini
              ↓
        Structured ImpactResponse
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever | None = None,
        impact_retriever: ImpactRetriever | None = None,
        gemini_client: GeminiClient | None = None,
    ) -> None:

        self.vector = (
            vector_retriever
            or VectorRetriever()
        )

        self.impact = (
            impact_retriever
            or ImpactRetriever()
        )

        self.gemini = (
            gemini_client
            or GeminiClient()
        )


    def _select_target(
    self,
    seeds: list[dict],
) -> dict:
        """
        Prefer a class seed when the semantic results
        clearly cluster around the same class.
        """

        if not seeds:
            return {}

        # Direct class match gets priority.
        for seed in seeds:
            if seed.get("seed_type") == "class":
                return seed

        # If multiple method seeds belong to the same
        # class namespace, resolve to the declaring class.
        method_seeds = [
            seed
            for seed in seeds
            if seed.get("seed_type") == "method"
        ]

        if method_seeds:
            first_method_id = method_seeds[0].get("id", "")

            if "#" in first_method_id:
                class_id = first_method_id.split("#", 1)[0]

                return {
                    "id": class_id,
                    "name": class_id.rsplit(".", 1)[-1],
                    "summary": (
                        "Class-level impact target resolved "
                        "from semantically related methods."
                    ),
                    "score": method_seeds[0].get("score", 0.0),
                    "seed_type": "class",
                }

        return seeds[0]

    def answer(
        self,
        question: str,
        top_k: int = 5,
    ) -> ImpactResponse:

        if not question or not question.strip():
            raise ValueError(
                "Impact analysis question cannot be empty."
            )

        seeds = self.vector.retrieve_seeds(
            question=question,
            top_k=top_k,
        )

        if not seeds:
            return ImpactResponse(
                target="unknown",
                impact_level="low",
                summary=(
                    "No relevant repository component was "
                    "found for the requested impact analysis."
                ),
            )

        # The highest-scoring semantic seed becomes the
        # primary impact target.
        target_seed = self._select_target(seeds)

        context = self.impact.retrieve(
            target_seed
        )

        if not context:
            return ImpactResponse(
                target=target_seed.get("id", "unknown"),
                impact_level="low",
                summary=(
                    "The target was found, but no structural "
                    "impact relationships were available."
                ),
                sources=[
                    target_seed["id"]
                ],
            )

        evidence_context = (
            ImpactContextBuilder.build(
                seed=target_seed,
                context=context,
            )
        )

        prompt = ImpactPromptBuilder.build(
            question=question,
            context=evidence_context,
        )

        response = self.gemini.generate_structured(
            prompt=prompt,
            response_model=ImpactResponse,
        )

        # Do not trust LLM-generated source IDs.
        sources = {target_seed["id"]}

        for item in (
            context.get("dependencies") or []
        ):
            if item.get("id"):
                sources.add(item["id"])

        for item in (
            context.get("dependents") or []
        ):
            if item.get("id"):
                sources.add(item["id"])

        response.target = target_seed["id"]
        affected_components = []

        for item in context.get("dependents") or []:
            affected_components.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "relationship": item["relationship"],
                    "direction": item["direction"],
                }
            )

        for item in context.get("dependencies") or []:
            affected_components.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "relationship": item["relationship"],
                    "direction": item["direction"],
                }
            )

        response.affected_components = affected_components
        response.sources = sorted(sources)
    

        return response