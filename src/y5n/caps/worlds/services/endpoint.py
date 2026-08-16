from __future__ import annotations

from typing import Protocol

from y5n.runtime.store.event.ports import OnDelete, OnGet, OnReplace

from ..data import EndpointData
from ..models import Endpoint, Orientation
from .namespaces import endpoint_key, endpoint_namespace


class OnScan(Protocol):
    async def __call__(self, *, namespace) -> list: ...


def _wrap_orientation(angle: float | None) -> Orientation | None:
    return Orientation(angle) if angle is not None else None


def _unwrap_orientation(orientation: Orientation | None) -> float | None:
    return orientation.angle if orientation is not None else None


class EndpointService:
    def __init__(
        self,
        on_get: OnGet,
        on_replace: OnReplace,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_next_id,
    ):
        self._on_get = on_get
        self._on_replace = on_replace
        self._on_scan = on_scan
        self._on_delete = on_delete
        self._on_next_id = on_next_id

    async def _all(self) -> list[Endpoint]:
        rows = await self._on_scan(namespace=endpoint_namespace())
        result = []
        for r in rows:
            if r is None:
                continue
            result.append(
                self._to_endpoint(r.key.id, EndpointData.from_dict(r.require_object()))
            )
        return result

    async def get(self, endpoint_id: str) -> Endpoint | None:
        row = await self._on_get(key=endpoint_key(endpoint_id))
        if row is None or row.data is None:
            return None
        return self._to_endpoint(
            endpoint_id, EndpointData.from_dict(row.require_object())
        )

    async def for_box(self, box_id: str) -> list[Endpoint]:
        return [e for e in await self._all() if e.box_id == box_id]

    async def add(
        self,
        *,
        box_id: str,
        connection_id: str,
        name: str = "",
        description: str = "",
        orientation: float | None = None,
    ) -> Endpoint:
        """Create an endpoint. *orientation* is an angle in degrees (or None)."""
        next_id = await self._on_next_id(prefix="p")
        data = EndpointData(
            box_id=box_id,
            connection_id=connection_id,
            name=name,
            description=description,
            orientation=orientation,
        )
        await self._on_replace(key=endpoint_key(str(next_id)), doc=data.to_dict())
        return Endpoint(
            id=str(next_id),
            box_id=box_id,
            connection_id=connection_id,
            name=name,
            description=description,
            orientation=_wrap_orientation(orientation),
        )

    async def update(
        self,
        *,
        endpoint_id: str,
        box_id: str | None = None,
        connection_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        orientation: float | None = None,
    ) -> Endpoint:
        e = await self.get(endpoint_id)
        if e is None:
            raise ValueError(f"Endpoint '{endpoint_id}' not found.")
        final_angle = (
            orientation
            if orientation is not None
            else _unwrap_orientation(e.orientation)
        )
        data = EndpointData(
            box_id=box_id if box_id is not None else e.box_id,
            connection_id=(
                connection_id if connection_id is not None else e.connection_id
            ),
            name=name if name is not None else e.name,
            description=description if description is not None else e.description,
            orientation=final_angle,
        )
        await self._on_replace(key=endpoint_key(endpoint_id), doc=data.to_dict())
        return Endpoint(
            id=endpoint_id,
            box_id=data.box_id,
            connection_id=data.connection_id,
            name=data.name,
            description=data.description,
            orientation=_wrap_orientation(final_angle),
        )

    async def delete(self, endpoint_id: str) -> None:
        await self._on_delete(key=endpoint_key(endpoint_id))

    def _to_endpoint(self, endpoint_id: str, data: EndpointData) -> Endpoint:
        return Endpoint(
            id=endpoint_id,
            box_id=data.box_id,
            connection_id=data.connection_id,
            name=data.name,
            description=data.description,
            orientation=_wrap_orientation(data.orientation),
        )
