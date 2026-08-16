from __future__ import annotations

from typing import Protocol

from y5n.runtime.store.event.ports import OnDelete, OnGet, OnReplace

from ..data import ConnectionData
from ..models import Connection, Endpoint
from .endpoint import EndpointService
from .namespaces import connection_key, connection_namespace


class OnScan(Protocol):
    async def __call__(self, *, namespace) -> list: ...


class ConnectionService:
    def __init__(
        self,
        endpoints: EndpointService,
        on_get: OnGet,
        on_replace: OnReplace,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_next_id,
    ):
        self._endpoints = endpoints
        self._on_get = on_get
        self._on_replace = on_replace
        self._on_scan = on_scan
        self._on_delete = on_delete
        self._on_next_id = on_next_id

    async def _all(self) -> list[Connection]:
        rows = await self._on_scan(namespace=connection_namespace())
        result = []
        for r in rows:
            if r is None:
                continue
            data = ConnectionData.from_dict(r.require_object())
            result.append(
                Connection(
                    id=r.key.id,
                    world_id=data.world_id,
                    endpoint_a_id=data.endpoint_a_id,
                    endpoint_b_id=data.endpoint_b_id,
                    bidirectional=data.bidirectional,
                    description=data.description,
                    kind=data.kind,
                )
            )
        return result

    async def get(self, connection_id: str) -> Connection | None:
        row = await self._on_get(key=connection_key(connection_id))
        if row is None or row.data is None:
            return None
        data = ConnectionData.from_dict(row.require_object())
        return Connection(
            id=connection_id,
            world_id=data.world_id,
            endpoint_a_id=data.endpoint_a_id,
            endpoint_b_id=data.endpoint_b_id,
            bidirectional=data.bidirectional,
            description=data.description,
            kind=data.kind,
        )

    async def for_world(self, world_id: str) -> list[Connection]:
        return [c for c in await self._all() if c.world_id == world_id]

    async def connect(
        self,
        *,
        world_id: str,
        box_a_id: str,
        box_b_id: str,
        name_a: str,
        orientation_a: float | None = None,
        name_b: str | None = None,
        orientation_b: float | None = None,
        bidirectional: bool = True,
        description: str = "",
        kind: str = "path",
    ) -> Connection:
        """Create a connection between two boxes plus its two endpoints.

        Orientations are angles in degrees (or None); when only one side
        is given, the other is its opposite.
        """
        if name_b is None:
            name_b = name_a
        if orientation_b is None and orientation_a is not None:
            orientation_b = (orientation_a + 180.0) % 360.0

        next_id = await self._on_next_id(prefix="c")
        endpoint_a = await self._endpoints.add(
            box_id=box_a_id,
            connection_id=str(next_id),
            name=name_a,
            orientation=orientation_a,
        )
        endpoint_b = await self._endpoints.add(
            box_id=box_b_id,
            connection_id=str(next_id),
            name=name_b,
            orientation=orientation_b,
        )
        data = ConnectionData(
            world_id=world_id,
            endpoint_a_id=endpoint_a.id,
            endpoint_b_id=endpoint_b.id,
            bidirectional=bidirectional,
            description=description,
            kind=kind,
        )
        await self._on_replace(key=connection_key(str(next_id)), doc=data.to_dict())
        return Connection(
            id=str(next_id),
            world_id=world_id,
            endpoint_a_id=endpoint_a.id,
            endpoint_b_id=endpoint_b.id,
            bidirectional=bidirectional,
            description=description,
            kind=kind,
        )

    async def update(
        self,
        *,
        connection_id: str,
        bidirectional: bool | None = None,
        description: str | None = None,
        kind: str | None = None,
    ) -> Connection:
        c = await self.get(connection_id)
        if c is None:
            raise ValueError(f"Connection '{connection_id}' not found.")
        data = ConnectionData(
            world_id=c.world_id,
            endpoint_a_id=c.endpoint_a_id,
            endpoint_b_id=c.endpoint_b_id,
            bidirectional=(
                bidirectional if bidirectional is not None else c.bidirectional
            ),
            description=description if description is not None else c.description,
            kind=kind if kind is not None else c.kind,
        )
        await self._on_replace(key=connection_key(connection_id), doc=data.to_dict())
        return Connection(
            id=connection_id,
            world_id=c.world_id,
            endpoint_a_id=c.endpoint_a_id,
            endpoint_b_id=c.endpoint_b_id,
            bidirectional=data.bidirectional,
            description=data.description,
            kind=data.kind,
        )

    async def disconnect(self, connection_id: str) -> None:
        c = await self.get(connection_id)
        if c is None:
            return
        await self._endpoints.delete(c.endpoint_a_id)
        await self._endpoints.delete(c.endpoint_b_id)
        await self._on_delete(key=connection_key(connection_id))

    async def endpoints(self, connection_id: str) -> list[Endpoint]:
        c = await self.get(connection_id)
        if c is None:
            return []
        result = []
        for eid in (c.endpoint_a_id, c.endpoint_b_id):
            e = await self._endpoints.get(eid)
            if e is not None:
                result.append(e)
        return result

    async def endpoint_on(self, connection_id: str, box_id: str) -> Endpoint | None:
        for e in await self.endpoints(connection_id):
            if e.box_id == box_id:
                return e
        return None

    async def other_endpoint(self, connection_id: str, box_id: str) -> Endpoint | None:
        for e in await self.endpoints(connection_id):
            if e.box_id != box_id:
                return e
        return None
