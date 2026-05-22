"""Shared pytest configuration and auto-marking by test layer."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Tag tests by layer and enable DB for integration tests."""
    for item in items:
        path = item.nodeid.replace("\\", "/")
        if "/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/api/" in path:
            item.add_marker(pytest.mark.api)
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.django_db)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.django_db)
