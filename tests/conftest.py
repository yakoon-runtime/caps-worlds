from __future__ import annotations

from typing import Any

import pytest

_services: dict[str, Any] = {}


def _publish(name: str, service: Any) -> None:
    _services[name] = service


def _get(name: str) -> Any:
    return _services.get(name)


@pytest.fixture(autouse=True)
def _patch_ports(monkeypatch):
    _services.clear()
    import y5n.packs.luma.setup as luma_setup
    import y5n.sdk.ports as sdk_ports

    monkeypatch.setattr(sdk_ports, "publish", _publish)
    monkeypatch.setattr(sdk_ports, "get", _get)
    import asyncio

    asyncio.run(luma_setup.main())
    yield


@pytest.fixture
def worlds():
    return _get("luma.world.service")


@pytest.fixture
def boxes():
    return _get("luma.box.service")


@pytest.fixture
def endpoints():
    return _get("luma.endpoint.service")


@pytest.fixture
def connections():
    return _get("luma.connection.service")


@pytest.fixture
def refine():
    return _get("luma.refine.service")


@pytest.fixture
def notes():
    return _get("luma.note.service")
