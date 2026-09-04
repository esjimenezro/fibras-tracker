from modules.wiki.repositories import FileSystemWikiSchemaReadRepository


def test_returns_schema_with_query_operation():
    """retrieve_data returns SCHEMA.md, which documents the Query operation."""
    content = FileSystemWikiSchemaReadRepository().retrieve_data()

    assert "Operación: Query" in content
