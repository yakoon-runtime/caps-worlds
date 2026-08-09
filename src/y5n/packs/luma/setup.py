from __future__ import annotations

from y5n.runtime.store.event.models import IndexKey, IndexSpec, IndexTerm, ValueType
from y5n.sdk import ports
from y5n.sdk.store import StoreClient

from .bootstrap import bootstrap
from .services import (
    BoxService,
    ConnectionService,
    EndpointService,
    NoteService,
    RefineService,
    WorldService,
    box_namespace,
    connection_namespace,
    endpoint_namespace,
    note_namespace,
    world_namespace,
)


async def main():

    store = StoreClient()

    INDEX_ALL = IndexSpec(key=IndexKey("all"), value_type=ValueType.TEXT, unique=False)

    for ns in [
        world_namespace(),
        box_namespace(),
        endpoint_namespace(),
        connection_namespace(),
        note_namespace(),
    ]:
        await store.ensure_indexes(namespace=ns, specs=[INDEX_ALL])

    async def _scan(namespace):
        return await store.scan(
            namespace=namespace, index_key=IndexKey("all"), value="1"
        )

    async def _replace(*, key, doc, indexes=(), snapshot_hint=None, expected_rev=None):
        idx = list(indexes) + [IndexTerm(key=IndexKey("all"), value="1")]
        return await store.replace(key=key, doc=doc, indexes=idx)

    worlds = WorldService(
        on_get=store.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.delete,
        on_next_id=store.next_id,
    )
    boxes = BoxService(
        on_get=store.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.delete,
        on_next_id=store.next_id,
    )
    endpoints = EndpointService(
        on_get=store.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.delete,
        on_next_id=store.next_id,
    )
    connections = ConnectionService(
        endpoints=endpoints,
        on_get=store.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.delete,
        on_next_id=store.next_id,
    )
    notes = NoteService(
        on_get=store.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.delete,
        on_next_id=store.next_id,
    )
    refine = RefineService(boxes=boxes, connections=connections, endpoints=endpoints)

    await bootstrap(worlds=worlds, boxes=boxes)

    ports.publish("luma.world.service", worlds)
    ports.publish("luma.box.service", boxes)
    ports.publish("luma.endpoint.service", endpoints)
    ports.publish("luma.connection.service", connections)
    ports.publish("luma.note.service", notes)
    ports.publish("luma.refine.service", refine)
