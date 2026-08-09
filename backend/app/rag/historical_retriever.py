from typing import Any

from app.graph.neo4j_client import neo4j_client


class HistoricalRetriever:
    """
    Retrieves repository evolution history from Neo4j.

    Historical graph path:

        Class
          ↑
        CONTAINS
          ↑
        File
          ↑
        MODIFIED
          ↑
        Commit

    Commit semantic metadata:
        - intent
        - message
        - author
        - timestamp
    """

    HISTORY_QUERY = """
    UNWIND $class_ids AS class_id

    MATCH (c:Class {id: class_id})
          <-[:CONTAINS]-(f:File)
          <-[:MODIFIED]-(commit:Commit)

    WITH
        commit,
        collect(DISTINCT f.path) AS affected_files

    RETURN
        commit.hash AS commit_hash,
        commit.timestamp AS timestamp,
        commit.author AS author,
        commit.message AS message,
        commit.intent AS intent,
        affected_files

    ORDER BY timestamp ASC
    """

    METHOD_TO_CLASS_QUERY = """
    MATCH (c:Class)-[:DECLARES]->(m:Method)
    WHERE m.id IN $method_ids

    RETURN
        m.id AS method_id,
        c.id AS class_id
    """

    def __init__(self) -> None:
        neo4j_client.connect()

    def resolve_class_ids(
        self,
        seeds: list[dict[str, Any]],
    ) -> list[str]:
        """
        Convert semantic retrieval seeds into Class IDs.

        Class seeds are used directly.

        Method seeds are resolved through:

            Class -[:DECLARES]-> Method
        """

        if not seeds:
            return []

        class_ids: set[str] = set()
        method_ids: list[str] = []

        for seed in seeds:
            seed_id = seed.get("id")
            seed_type = seed.get("seed_type")

            if not seed_id:
                continue

            if seed_type == "class":
                class_ids.add(seed_id)

            elif seed_type == "method":
                method_ids.append(seed_id)

        if method_ids:
            rows = neo4j_client.execute_query(
                self.METHOD_TO_CLASS_QUERY,
                {
                    "method_ids": method_ids,
                },
            )

            for row in rows:
                class_id = row.get("class_id")

                if class_id:
                    class_ids.add(class_id)

        return sorted(class_ids)

    def retrieve(
        self,
        class_ids: list[str],
    ) -> list[dict[str, Any]]:
        """
        Retrieve chronological commit history for
        the supplied repository Classes.
        """

        if not class_ids:
            return []

        return neo4j_client.execute_query(
            self.HISTORY_QUERY,
            {
                "class_ids": class_ids,
            },
        )