from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

_services: dict[str, Any] = {}


def _publish(name: str, service: Any) -> None:
    _services[name] = service


def _get(name: str) -> Any:
    return _services.get(name)


def _is_caps_worlds_test(node) -> bool:
    """This conftest is autouse; guard it so it only affects caps-worlds tests.

    In a combined multi-project pytest run the same conftest file is applied
    to sibling test trees (e.g. caps-ident). That global monkeypatch of
    ``y5n.sdk.ports`` would otherwise break other packs' port-based tests.
    """
    this_dir = Path(__file__).resolve().parent
    fspath = Path(getattr(node, "fspath", "")).resolve() if getattr(node, "fspath", None) else None
    return fspath is not None and this_dir in fspath.parents


@pytest.fixture(autouse=True)
def _patch_ports(request, monkeypatch, tmp_path):
    if not _is_caps_worlds_test(request.node):
        return
    _services.clear()
    import asyncio
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    from y5n.runtime.api.runtime.bus import _make_default_bus
    from y5n.runtime.api.runtime.bus import get_bus as _get_bus
    from y5n.runtime.api.runtime.bus import set_bus as _set_bus
    from y5n.runtime.engine.wire.adapter.store import StoreAdapter
    from y5n.runtime.store.event.backends.memory import MemoryBackend
    from y5n.runtime.store.event.runtime import StoreRuntime
    from y5n.runtime.store.event.store import create_entity_store
    from y5n.runtime.store.sequence.allocator import ShardAllocator
    from y5n.runtime.store.sequence.backends.memory import MemoryShardRepository
    from y5n.runtime.store.sequence.runtime import Sequencer

    # Wire a real store behind the SDK `store` port so pack setup can use
    # sdk.store.get("worlds") (ADR-17: the runtime owns the store; the resolver
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
        "system:store",
        StoreAdapter(stores={"worlds": runtime}),
    )

    import y5n.caps.worlds.setup as worlds_setup
    import y5n.sdk.ports as sdk_ports

    monkeypatch.setattr(sdk_ports, "publish", _publish)
    monkeypatch.setattr(sdk_ports, "get", _get)

    asyncio.run(worlds_setup.main())
    yield
    _set_bus(previous_bus)


@pytest.fixture
def worlds():
    return _get("worlds.world.service")


@pytest.fixture
def boxes():
    return _get("worlds.box.service")


@pytest.fixture
def endpoints():
    return _get("worlds.endpoint.service")


@pytest.fixture
def connections():
    return _get("worlds.connection.service")


@pytest.fixture
def refine():
    return _get("worlds.refine.service")


@pytest.fixture
def notes():
    return _get("worlds.note.service")
