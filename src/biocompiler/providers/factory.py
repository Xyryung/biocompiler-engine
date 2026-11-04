from biocompiler.config import Settings, get_settings
from biocompiler.providers.base import Provider


def get_provider(settings: Settings | None = None) -> Provider:
    config = settings or get_settings()
    if config.biocompiler_provider == "mock":
        from biocompiler.providers.mock import MockProvider

        return MockProvider()
    from biocompiler.providers.meta import MetaProvider

    return MetaProvider(config)
