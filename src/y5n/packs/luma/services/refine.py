"""Graph refactoring: split a box along a line.

A split is a pure graph transformation. The line (angle + normalized
offset) classifies each endpoint of the box by its orientation; endpoints
on one side are reassigned to the new box. Connections stay untouched —
they only reference endpoint ids.
"""

from __future__ import annotations

import math

from ..models import Orientation
from .box import BoxService
from .connection import ConnectionService
from .endpoint import EndpointService

# Geometry lives here; boxes and endpoints are only re-pointed.
_EPS = 1e-9


def _normal(angle_deg: float) -> tuple[float, float]:
    rad = math.radians(angle_deg)
    return (math.cos(rad), math.sin(rad))


def _support(nx: float, ny: float) -> float:
    """Distance at which the line touches the box edge in normal direction."""
    return abs(nx) + abs(ny)


def _side(exit_angle: float, angle_deg: float, offset: float) -> float:
    nx, ny = _normal(angle_deg)
    d = offset * _support(nx, ny)
    px = math.cos(math.radians(exit_angle))
    py = math.sin(math.radians(exit_angle))
    return px * nx + py * ny - d


def _nearest_cardinal(nx: float, ny: float) -> str:
    if abs(nx) >= abs(ny):
        return "east" if nx >= 0 else "west"
    return "north" if ny >= 0 else "south"


def belongs_to_new(angle_deg: float, split_angle_deg: float, offset: float) -> bool:
    """True if an orientation at *angle_deg* lies on the new side of the line."""
    return _side(angle_deg, split_angle_deg, offset) > _EPS


class RefineService:
    def __init__(
        self,
        boxes: BoxService,
        connections: ConnectionService,
        endpoints: EndpointService,
    ):
        self._boxes = boxes
        self._connections = connections
        self._endpoints = endpoints

    async def split(
        self,
        *,
        world_id: str,
        box_id: str,
        angle_deg: float,
        offset: float = 0.0,
    ) -> dict:
        """Split *box_id* along a line through its center.

        Creates a second box, connects both halves, and reassigns every
        endpoint of the original box by its orientation. Returns a summary.
        """
        box = await self._boxes.get_box(box_id=box_id)
        if box is None:
            raise ValueError(f"Box '#{box_id}' not found.")

        new_name = await self._next_name(world_id, box.name)
        new_box = await self._boxes.add_box(
            world_id=world_id,
            parent_id=box.parent_id,
            name=new_name,
            description="",
        )

        nx, ny = _normal(angle_deg)
        fwd = _nearest_cardinal(nx, ny)
        rev = _opposite(fwd)
        connection = await self._connections.connect(
            world_id=world_id,
            box_a_id=box.id,
            box_b_id=new_box.id,
            name_a=fwd,
            orientation_a=Orientation.from_notation(fwd),
            name_b=rev,
            orientation_b=Orientation.from_notation(rev),
        )

        moved = 0
        for endpoint in await self._endpoints.for_box(box_id=box.id):
            if endpoint.connection_id == connection.id:
                continue
            if endpoint.orientation is None:
                continue
            if belongs_to_new(endpoint.orientation.angle, angle_deg, offset):
                await self._endpoints.update(endpoint_id=endpoint.id, box_id=new_box.id)
                moved += 1

        return {
            "box": box,
            "new_box": new_box,
            "moved": moved,
            "angle": angle_deg,
            "offset": offset,
        }

    async def _next_name(self, world_id: str, base: str) -> str:
        candidate = base
        n = 2
        while await self._boxes.find_box(world_id=world_id, name=candidate) is not None:
            candidate = f"{base} {n}"
            n += 1
        return candidate


def _opposite(direction: str) -> str:
    pairs = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
    }
    return pairs.get(direction, "")
