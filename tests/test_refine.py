import pytest


async def _world_with_box(worlds, boxes, name="A"):
    world = await worlds.add_world(name="Welt", description="")
    box = await boxes.add_box(
        world_id=world.id, parent_id=None, name=name, description="", portable=False
    )
    return world, box


async def _add_reverse(exits, world_id, box, other, direction, name):
    from y5n.packs.luma.services import Directions

    await exits.connect(
        world_id=world_id,
        source_box_id=box.id,
        target_box_id=other.id,
        name=name,
        direction=direction,
    )
    await exits.connect(
        world_id=world_id,
        source_box_id=other.id,
        target_box_id=box.id,
        name=name,
        direction=Directions.opposite(direction),
    )


def _exit_angles(exits, box_id):
    return {
        (e.source_box_id, e.target_box_id): e
        for e in exits
        if e.source_box_id == box_id
    }


@pytest.mark.asyncio
async def test_split_creates_second_box_and_connection(worlds, boxes, exits, refine):
    world, box = await _world_with_box(worlds, boxes)

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=90.0)

    new_box = result["new_box"]
    assert new_box.id != box.id
    assert new_box.parent_id == box.parent_id
    assert new_box.name == f"{box.name} 2"

    from_a = await exits.find_from(box_id=box.id)
    from_new = await exits.find_from(box_id=new_box.id)
    assert any(e.target_box_id == new_box.id for e in from_a)
    assert any(e.target_box_id == box.id for e in from_new)


@pytest.mark.asyncio
async def test_vertical_split_moves_east_and_pairs(worlds, boxes, exits, refine):
    world, box = await _world_with_box(worlds, boxes)
    east = await boxes.add_box(
        world_id=world.id, parent_id=None, name="East", description="", portable=False
    )
    north = await boxes.add_box(
        world_id=world.id, parent_id=None, name="North", description="", portable=False
    )
    await _add_reverse(exits, world.id, box, east, "east", "door")
    await exits.connect(
        world_id=world.id,
        source_box_id=box.id,
        target_box_id=north.id,
        name="top",
        direction="north",
    )

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=0.0)

    new_box = result["new_box"]
    from_east = [
        e
        for e in await exits.find_from(box_id=east.id)
        if e.target_box_id == box.id or e.target_box_id == new_box.id
    ]
    assert len(from_east) == 1
    assert from_east[0].target_box_id == new_box.id
    assert result["moved"] == 1

    from_north = await exits.find_to(box_id=north.id)
    assert any(e.source_box_id == box.id for e in from_north)


@pytest.mark.asyncio
async def test_exit_on_the_line_stays_with_old_room(worlds, boxes, exits, refine):
    world, box = await _world_with_box(worlds, boxes)
    north = await boxes.add_box(
        world_id=world.id, parent_id=None, name="North", description="", portable=False
    )
    await exits.connect(
        world_id=world.id,
        source_box_id=box.id,
        target_box_id=north.id,
        name="top",
        direction="north",
    )

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=0.0)

    assert result["moved"] == 0
    from_a = await exits.find_from(box_id=box.id)
    assert any(e.target_box_id == north.id for e in from_a)


@pytest.mark.asyncio
async def test_diagonal_split_assigns_corners(worlds, boxes, exits, refine):
    world, box = await _world_with_box(worlds, boxes)
    targets = {}
    for name, direction in (
        ("E", "east"),
        ("N", "north"),
        ("W", "west"),
        ("S", "south"),
    ):
        other = await boxes.add_box(
            world_id=world.id,
            parent_id=None,
            name=name,
            description="",
            portable=False,
        )
        await exits.connect(
            world_id=world.id,
            source_box_id=box.id,
            target_box_id=other.id,
            name=direction,
            direction=direction,
        )
        targets[direction] = other.id

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=45.0)

    new_box = result["new_box"]
    assert result["moved"] == 2
    sources = _exit_angles(await exits.find_from(box_id=new_box.id), new_box.id)
    moved_to_new = {e.target_box_id for e in sources.values()}
    assert targets["east"] in moved_to_new
    assert targets["north"] in moved_to_new

    sources_old = _exit_angles(await exits.find_from(box_id=box.id), box.id)
    moved_old = {
        e.target_box_id for e in sources_old.values() if e.target_box_id != new_box.id
    }
    assert targets["west"] in moved_old
    assert targets["south"] in moved_old


@pytest.mark.asyncio
async def test_offset_makes_narrow_strip(worlds, boxes, exits, refine):
    world, box = await _world_with_box(worlds, boxes)
    targets = {}
    for name, direction in (
        ("N", "north"),
        ("E", "east"),
        ("W", "west"),
        ("S", "south"),
    ):
        other = await boxes.add_box(
            world_id=world.id,
            parent_id=None,
            name=name,
            description="",
            portable=False,
        )
        await exits.connect(
            world_id=world.id,
            source_box_id=box.id,
            target_box_id=other.id,
            name=direction,
            direction=direction,
        )
        targets[direction] = other.id

    result = await refine.split(
        world_id=world.id, box_id=box.id, angle_deg=0.0, offset=0.8
    )

    new_box = result["new_box"]
    assert result["moved"] == 1
    sources = _exit_angles(await exits.find_from(box_id=new_box.id), new_box.id)
    moved_to_new = {
        e.target_box_id for e in sources.values() if e.target_box_id != box.id
    }
    assert moved_to_new == {targets["east"]}


@pytest.mark.asyncio
async def test_unpaired_incoming_exit_stays_with_old(worlds, boxes, exits, refine):
    world, box = await _world_with_box(worlds, boxes)
    c = await boxes.add_box(
        world_id=world.id, parent_id=None, name="C", description="", portable=False
    )
    await exits.connect(
        world_id=world.id,
        source_box_id=c.id,
        target_box_id=box.id,
        name="fall",
        direction="south",
    )

    await refine.split(world_id=world.id, box_id=box.id, angle_deg=90.0)

    from_c = await exits.find_from(box_id=c.id)
    assert len(from_c) == 1
    assert from_c[0].target_box_id == box.id
