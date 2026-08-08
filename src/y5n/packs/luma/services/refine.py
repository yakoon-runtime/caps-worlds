"""Graph refactoring: split a box along a line.

A split is a pure graph transformation. Boxes and exits are unchanged;
only the box references of affected exits are rewired.

The geometry is purely logical. A line through the box's center is
described by its angle (math convention: 0° = +x = east, counterclockwise)
and a normalized offset (-1 ≤ offset ≤ 1, where 0 is the center and ±1
puts the line on the edge). Exits carry an implicit position on their
source side; the line classifies each exit into the new or the old room.

Exits whose side midpoint lies exactly on the line stay with the old
room — deterministic, no user interaction.
"""

from __future__ import annotations

import math

from .box import BoxService
from .directions import Directions
from .exit import ExitService

# Exit direction -> position on the unit circle (0° = east, CCW).
EXIT_ANGLES = {
    "east": 0.0,
    "north": 90.0,
    "west": 180.0,
    "south": 270.0,
}

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


def _belongs_to_new(direction: str, angle_deg: float, offset: float) -> bool:
    exit_angle = EXIT_ANGLES.get(direction.lower())
    if exit_angle is None:
        return False
    return _side(exit_angle, angle_deg, offset) > _EPS


class RefineService:
    def __init__(self, boxes: BoxService, exits: ExitService):
        self._boxes = boxes
        self._exits = exits

    async def split(
        self,
        *,
        world_id: str,
        box_id: str,
        angle_deg: float,
        offset: float = 0.0,
    ) -> dict:
        """Split *box_id* along a line through its center.

        Creates a second box, connects both halves, and rewires every
        exit that touches the original box. Returns a summary dict.
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
        rev = Directions.opposite(fwd) or fwd

        fwd_name = await self._next_exit_name(box.id, f"to {new_box.name}")
        rev_name = await self._next_exit_name(new_box.id, f"to {box.name}")
        await self._exits.connect(
            world_id=world_id,
            source_box_id=box.id,
            target_box_id=new_box.id,
            name=fwd_name,
            direction=fwd,
        )
        await self._exits.connect(
            world_id=world_id,
            source_box_id=new_box.id,
            target_box_id=box.id,
            name=rev_name,
            direction=rev,
        )

        outgoing = [
            e
            for e in await self._exits.find_from(box_id=box.id)
            if e.target_box_id != new_box.id
        ]
        incoming = [
            e
            for e in await self._exits.find_to(box_id=box.id)
            if e.source_box_id != new_box.id
        ]

        by_source: dict[str, list] = {}
        for e in incoming:
            by_source.setdefault(e.source_box_id, []).append(e)

        used: set[str] = set()
        moved = 0
        for e in outgoing:
            assigned = (
                new_box.id
                if _belongs_to_new(e.direction, angle_deg, offset)
                else box.id
            )
            if assigned == new_box.id:
                moved += 1
            await self._exits.update_exit(exit_id=e.id, source_box_id=assigned)

            for pair in by_source.get(e.target_box_id, []):
                if pair.id in used:
                    continue
                if pair.name.lower() != e.name.lower():
                    continue
                await self._exits.update_exit(exit_id=pair.id, target_box_id=assigned)
                used.add(pair.id)
                break

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

    async def _next_exit_name(self, source_box_id: str, base: str) -> str:
        taken = {
            e.name.lower() for e in await self._exits.find_from(box_id=source_box_id)
        }
        candidate = base
        n = 2
        while candidate.lower() in taken:
            candidate = f"{base} {n}"
            n += 1
        return candidate
