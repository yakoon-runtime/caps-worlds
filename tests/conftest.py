from __future__ import annotations

from typing import Any

import pytest

_services: dict[str, Any] = {}


def _publish(name: str, service: Any) -> None:
    _services[name] = service


def _get(name: str) -> Any:
    return _services.get(name)


@pytest.fixture(autouse=True)
def _patch_ports(monkeypatch, tmp_path):
    _services.clear()
    import asyncio
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    from y5n.runtime.api.runtime.bus import _make_default_bus
    from y5n.runtime.api.runtime.bus import get_bus as _get_bus
    from y5n.runtime.api.runtime.bus import set_bus as _set_bus
    from y5n.runtime.engine.wire.adapter.store import StoreAdapter, StoreResolver
    from y5n.runtime.store.event.backends.memory import MemoryBackend
    from y5n.runtime.store.event.runtime import StoreRuntime
    from y5n.runtime.store.event.store import create_entity_store
    from y5n.runtime.store.sequence.allocator import ShardAllocator
    from y5n.runtime.store.sequence.backends.memory import MemoryShardRepository
    from y5n.runtime.store.sequence.runtime import Sequencer

    # Wire a real store behind the SDK `store` port so pack setup can use
    # sdk.store.get("luma") (ADR-17: the runtime owns the store; the resolver
    # routes the bound name to the installation's store).
    previous_bus = _get_bus()
    bus = _make_default_bus()
    _set_bus(bus)

    runtime = StoreRuntime(
        objects=create_entity_store(MemoryBackend()),
        sequencer=Sequencer(ShardAllocator(MemoryShardRepository())),
    )

    bus.resolver.register(
        "system:store",
        {
            "store": [
                "get",
                "get_many",
                "append",
                "replace",
                "record",
                "delete",
                "scan",
                "ensure_indexes",
                "query_index",
                "next_id",
            ]
        },
        path="/",
    )
    bus.transport.register_adapter(
        "store",
        StoreAdapter(
            resolver=StoreResolver(stores={"luma": runtime}),
        ),
    )

    import y5n.packs.luma.setup as luma_setup
    import y5n.sdk.ports as sdk_ports

    monkeypatch.setattr(sdk_ports, "publish", _publish)
    monkeypatch.setattr(sdk_ports, "get", _get)

    asyncio.run(luma_setup.main())
    yield
    _set_bus(previous_bus)


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
