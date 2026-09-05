from modules.wiki.repositories import AnthropicWikiAgentReadRepository


def test_constructs_without_touching_anthropic_client():
    """Instantiation never builds an anthropic.Anthropic() client (built lazily
    inside retrieve_data instead), so it succeeds even with no API key configured.
    """
    AnthropicWikiAgentReadRepository()
