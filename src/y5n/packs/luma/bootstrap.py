"""Development seed data for the luma space.

Creates two worlds with one room each and sets their entry point, so
manual exploration and tests don't have to set up basic data by hand.
Idempotent: existing worlds and rooms are reused, never duplicated.
"""

from __future__ import annotations

from .services import BoxService, WorldService

_SEED = [
    ("Tiergarten", "Eingang"),
    ("Bibliothek", "Lesesaal"),
]


async def bootstrap(worlds: WorldService, boxes: BoxService) -> None:
    for world_name, room_name in _SEED:
        world = await worlds.get_world_by_name(name=world_name)
        if world is None:
            world = await worlds.add_world(name=world_name, description="")

        room = await boxes.find_box(world_id=world.id, name=room_name)
        if room is None:
            room = await boxes.add_box(
                world_id=world.id,
                parent_id=None,
                name=room_name,
                description="",
                portable=False,
            )

        if world.entry_box_id != room.id:
            await worlds.set_entry(world_id=world.id, box_id=room.id)
