import pytest
from y5n.packs.luma.models import Orientation


async def _world_with_box(worlds, boxes, name="A"):
    world = await worlds.add_world(name="Welt", description="")
    box = await boxes.add_box(
        world_id=world.id, parent_id=None, name=name, description="", portable=False
    )
    return world, box


async def _connect_cardinal(connections, world_id, box, other, direction, name=None):
    return await connections.connect(
        world_id=world_id,
        box_a_id=box.id,
        box_b_id=other.id,
        name_a=name or direction,
        orientation_a=Orientation.from_notation(direction),
    )


async def _endpoints_excluding(connections, endpoints, box_id, other_id):
    """Endpoints of *box_id* whose connection does not also touch *other_id*."""
    result = []
    for ep in await endpoints.for_box(box_id=box_id):
        conn = await connections.get(ep.connection_id)
        if conn is None:
            continue
        other = await connections.other_endpoint(conn, box_id)
        if other is not None and other.box_id == other_id:
            continue
        result.append(ep)
    return result


@pytest.mark.asyncio
async def test_split_creates_second_box_and_connection(
    worlds, boxes, connections, refine
):
    world, box = await _world_with_box(worlds, boxes)

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=90.0)

    new_box = result["new_box"]
    assert new_box.id != box.id
    assert new_box.parent_id == box.parent_id
    assert new_box.name == f"{box.name} 2"

    conns = await connections.for_world(world_id=world.id)
    assert len(conns) == 1
    endpoints = await connections.endpoints(conns[0].id)
    assert {e.box_id for e in endpoints} == {box.id, new_box.id}


@pytest.mark.asyncio
async def test_vertical_split_moves_east_endpoint(
    worlds, boxes, connections, endpoints, refine
):
    world, box = await _world_with_box(worlds, boxes)
    east = await boxes.add_box(
        world_id=world.id, parent_id=None, name="East", description="", portable=False
    )
    north = await boxes.add_box(
        world_id=world.id, parent_id=None, name="North", description="", portable=False
    )
    await _connect_cardinal(connections, world.id, box, east, "east", "door")
    await _connect_cardinal(connections, world.id, box, north, "north", "top")

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=0.0)

    new_box = result["new_box"]
    assert result["moved"] == 1

    on_new = {
        e.orientation.word()
        for e in await _endpoints_excluding(connections, endpoints, new_box.id, box.id)
    }
    assert on_new == {"east"}
    on_old = {
        e.orientation.word()
        for e in await _endpoints_excluding(connections, endpoints, box.id, new_box.id)
    }
    assert "north" in on_old


@pytest.mark.asyncio
async def test_exit_on_the_line_stays_with_old_room(
    worlds, boxes, connections, endpoints, refine
):
    world, box = await _world_with_box(worlds, boxes)
    north = await boxes.add_box(
        world_id=world.id, parent_id=None, name="North", description="", portable=False
    )
    await _connect_cardinal(connections, world.id, box, north, "north", "top")

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=0.0)

    assert result["moved"] == 0
    new_box = result["new_box"]
    on_old = {
        e.orientation.word()
        for e in await _endpoints_excluding(connections, endpoints, box.id, new_box.id)
    }
    assert "north" in on_old


@pytest.mark.asyncio
async def test_diagonal_split_assigns_corners(
    worlds, boxes, connections, endpoints, refine
):
    world, box = await _world_with_box(worlds, boxes)
    for direction in ("east", "north", "west", "south"):
        other = await boxes.add_box(
            world_id=world.id,
            parent_id=None,
            name=direction,
            description="",
            portable=False,
        )
        await _connect_cardinal(connections, world.id, box, other, direction, direction)

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=45.0)

    new_box = result["new_box"]
    assert result["moved"] == 2
    on_new = {
        e.orientation.word()
        for e in await _endpoints_excluding(connections, endpoints, new_box.id, box.id)
    }
    assert on_new == {"east", "north"}
    on_old = {
        e.orientation.word()
        for e in await _endpoints_excluding(connections, endpoints, box.id, new_box.id)
    }
    assert {"west", "south"} <= on_old


@pytest.mark.asyncio
async def test_offset_makes_narrow_strip(worlds, boxes, connections, endpoints, refine):
    world, box = await _world_with_box(worlds, boxes)
    for direction in ("east", "north", "west", "south"):
        other = await boxes.add_box(
            world_id=world.id,
            parent_id=None,
            name=direction,
            description="",
            portable=False,
        )
        await _connect_cardinal(connections, world.id, box, other, direction, direction)

    result = await refine.split(
        world_id=world.id, box_id=box.id, angle_deg=0.0, offset=0.8
    )

    new_box = result["new_box"]
    assert result["moved"] == 1
    on_new = {
        e.orientation.word()
        for e in await _endpoints_excluding(connections, endpoints, new_box.id, box.id)
    }
    assert on_new == {"east"}


@pytest.mark.asyncio
async def test_oneway_incoming_endpoint_classified_by_orientation(
    worlds, boxes, connections, endpoints, refine
):
    world, box = await _world_with_box(worlds, boxes)
    c = await boxes.add_box(
        world_id=world.id, parent_id=None, name="C", description="", portable=False
    )
    await connections.connect(
        world_id=world.id,
        box_a_id=c.id,
        box_b_id=box.id,
        name_a="fall",
        orientation_a=Orientation.from_notation("south"),
        name_b="fall",
        orientation_b=Orientation.from_notation("north"),
        bidirectional=False,
    )

    result = await refine.split(world_id=world.id, box_id=box.id, angle_deg=90.0)

    new_box = result["new_box"]
    assert result["moved"] == 1
    on_new = [e for e in await endpoints.for_box(box_id=new_box.id)]
    assert any(e.connection_id and e.name == "fall" for e in on_new)
