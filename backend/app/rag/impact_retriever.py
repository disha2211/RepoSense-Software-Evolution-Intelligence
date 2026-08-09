from typing import Any

from app.graph.neo4j_client import neo4j_client


class ImpactRetriever:
    """
    Retrieves structural impact evidence from Neo4j.

    Current graph relationships:

        IMPORTS
        EXTENDS
        IMPLEMENTS
        DECLARES
        HAS_FIELD
        CONTAINS
        MODIFIED

    This retriever deliberately does not infer relationships
    that are not currently represented in the graph.
    """

    CLASS_IMPACT_QUERY = """
    MATCH (target:Class {id: $class_id})

    OPTIONAL MATCH (target)-[outgoing:IMPORTS|EXTENDS|IMPLEMENTS]->(dependency:Class)

    OPTIONAL MATCH (dependent:Class)-[incoming:IMPORTS|EXTENDS|IMPLEMENTS]->(target)

    OPTIONAL MATCH (target)-[:DECLARES]->(method:Method)

    RETURN
        target.id AS target_id,
        target.name AS target_name,
        target.summary AS target_summary,

        collect(DISTINCT {
            id: dependency.id,
            name: dependency.name,
            relationship: type(outgoing),
            direction: "outgoing"
        }) AS dependencies,

        collect(DISTINCT {
            id: dependent.id,
            name: dependent.name,
            relationship: type(incoming),
            direction: "incoming"
        }) AS dependents,

        collect(DISTINCT {
            id: method.id,
            name: method.name,
            relationship: "DECLARES",
            direction: "outgoing"
        }) AS methods
    """

    METHOD_IMPACT_QUERY = """
    MATCH (target:Method {id: $method_id})
    MATCH (owner:Class)-[:DECLARES]->(target)

    OPTIONAL MATCH (owner)-[outgoing:IMPORTS|EXTENDS|IMPLEMENTS]->(dependency:Class)

    OPTIONAL MATCH (dependent:Class)-[incoming:IMPORTS|EXTENDS|IMPLEMENTS]->(owner)

    RETURN
        target.id AS target_id,
        target.name AS target_name,
        target.summary AS target_summary,

        {
            id: owner.id,
            name: owner.name,
            relationship: "DECLARES",
            direction: "outgoing"
        } AS declaring_class,

        collect(DISTINCT {
            id: dependency.id,
            name: dependency.name,
            relationship: type(outgoing),
            direction: "outgoing"
        }) AS dependencies,

        collect(DISTINCT {
            id: dependent.id,
            name: dependent.name,
            relationship: type(incoming),
            direction: "incoming"
        }) AS dependents
    """

    def __init__(self) -> None:
        neo4j_client.connect()

    def retrieve(
        self,
        seed: dict[str, Any],
    ) -> dict[str, Any]:

        seed_id = seed.get("id")
        seed_type = seed.get("seed_type")

        if not seed_id:
            return {}

        if seed_type == "class":
            rows = neo4j_client.execute_query(
                self.CLASS_IMPACT_QUERY,
                {"class_id": seed_id},
            )

        elif seed_type == "method":
            rows = neo4j_client.execute_query(
                self.METHOD_IMPACT_QUERY,
                {"method_id": seed_id},
            )

        else:
            return {}

        if not rows:
            return {}

        return self._clean_result(rows[0])

    @staticmethod
    def _clean_result(
        result: dict[str, Any],
    ) -> dict[str, Any]:

        def clean_items(items: Any) -> list[dict]:
            if not items:
                return []

            return [
                item
                for item in items
                if item and item.get("id")
            ]

        result["dependencies"] = clean_items(
            result.get("dependencies")
        )

        result["dependents"] = clean_items(
            result.get("dependents")
        )

        result["methods"] = clean_items(
            result.get("methods")
        )

        declaring = result.get("declaring_class")

        if declaring and not declaring.get("id"):
            result["declaring_class"] = None

        return result