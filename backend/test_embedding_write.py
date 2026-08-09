from app.graph.neo4j_client import neo4j_client
from app.rag.embedding_service import embedding_service
from app.rag.semantic_text_builder import SemanticTextBuilder


neo4j_client.connect()

rows = neo4j_client.execute_query(
    """
    MATCH (c:Class)
    RETURN
        c.id AS id,
        c.name AS name,
        c.type AS type,
        c.annotations AS annotations,
        c.extends AS extends,
        c.implements AS implements,
        c.summary AS summary
    LIMIT 1
    """
)

c = rows[0]

text = SemanticTextBuilder.build_class_text(c)
embedding = embedding_service.embed(text)

print("ID:", c["id"])
print("TEXT:")
print(text)
print("EMBEDDING LENGTH:", len(embedding))

result = neo4j_client.execute_query(
    """
    MATCH (c:Class {id: $id})
    SET c.embedding = $embedding
    RETURN
        c.id AS id,
        size(c.embedding) AS dimension
    """,
    {
        "id": c["id"],
        "embedding": embedding,
    },
)

print("WRITE:", result)