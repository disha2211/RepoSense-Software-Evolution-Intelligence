from typing import Any

from neo4j import Driver, GraphDatabase, Session
from neo4j.exceptions import Neo4jError

from app.config import settings


class Neo4jClient:
    """
    - Initialize the Neo4j driver
    - Verify connectivity
    - Execute Cypher queries
    - Provide database sessions
    - Close the driver on application shutdown
    """

    def __init__(self) -> None:
        self._driver: Driver | None = None

    @property
    def driver(self) -> Driver:
        """
        Returns the initialized Neo4j driver.

        Raises:
            RuntimeError: If the driver has not been initialized.
        """
        if self._driver is None:
            raise RuntimeError(
                "Neo4j driver has not been initialized. Call connect() first."
            )
        return self._driver

    def connect(self) -> None:
        try:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(
                    settings.NEO4J_USERNAME,
                    settings.NEO4J_PASSWORD,
                ),
            )

            self.driver.verify_connectivity()

        except Exception:
            self.close()
            raise

    def close(self) -> None:
        """
        Closes the Neo4j driver.
        """
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def get_session(self) -> Session:
        """
        Creates and returns a new Neo4j session.
        Returns:
            Session: A Neo4j session.
        """
        return self.driver.session()

    def execute_query(
    self,
    query: str,
    parameters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
            """
            Executes a Cypher query and ensures the result is fully consumed.

            Args:
                query: Cypher query string.
                parameters: Query parameters.

            Returns:
                List of query results as dictionaries.

            Raises:
                Neo4jError: If query execution fails.
            """
            try:
                with self.get_session() as session:
                    result = session.run(
                        query,
                        parameters or {},
                    )

                    records = [
                        record.data()
                        for record in result
                    ]

                    # Explicitly consume the result so that
                    # write transactions are completed.
                    result.consume()

                    return records

            except Neo4jError as e:
                raise e

    def is_connected(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False


neo4j_client = Neo4jClient()
