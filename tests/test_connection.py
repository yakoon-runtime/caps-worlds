import pytest
from y5n.packs.luma.models import Orientation


def _angle(direction: str) -> float:
    o = Orientation.from_notation(direction)
    return o.angle if o is not None else 0.0


async def _world_with_box(worlds, boxes, name="A"):
    world = await worlds.add_world(name="Welt", description="")
    box = await boxes.add_box(
        world_id=world.id, parent_id=None, name=name, description="", portable=False
    )
    return world, box


async def _other_box(connections, boxes, endpoint, current_box):
    conn = await connections.get(endpoint.connection_id)
    other = await connections.other_endpoint(conn.id, current_box)
    if other is None:
        return None
    return await boxes.get_box(box_id=other.box_id)


@pytest.mark.asyncio
async def test_connect_creates_connection_with_two_endpoints(
    worlds, boxes, connections, endpoints
):
    world, raum_a = await _world_with_box(worlds, boxes, "A")
    raum_b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="B", description="", portable=False
    )

    conn = await connections.connect(
        world_id=world.id,
        box_a_id=raum_a.id,
        box_b_id=raum_b.id,
        name_a="Tür",
        orientation_a=_angle("east"),
    )

    assert conn.bidirectional is True
    assert conn.kind == "path"

    eps = await connections.endpoints(conn.id)
    assert len(eps) == 2
    by_box = {e.box_id: e for e in eps}
    assert set(by_box) == {raum_a.id, raum_b.id}

    a_ep = by_box[raum_a.id]
    b_ep = by_box[raum_b.id]
    assert a_ep.name == "Tür"
    assert a_ep.orientation is not None
    assert a_ep.orientation.angle == 0.0
    assert b_ep.name == "Tür"
    assert b_ep.orientation is not None
    assert b_ep.orientation.angle == 180.0


@pytest.mark.asyncio
async def test_connect_oneway_sets_bidirectional_false(worlds, boxes, connections):
    world, raum_a = await _world_with_box(worlds, boxes, "A")
    raum_b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="B", description="", portable=False
    )

    conn = await connections.connect(
        world_id=world.id,
        box_a_id=raum_a.id,
        box_b_id=raum_b.id,
        name_a="Falltür",
        bidirectional=False,
    )

    assert conn.bidirectional is False


@pytest.mark.asyncio
async def test_endpoints_for_box_and_other_side(worlds, boxes, connections, endpoints):
    world, raum_a = await _world_with_box(worlds, boxes, "A")
    raum_b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="B", description="", portable=False
    )
    await connections.connect(
        world_id=world.id,
        box_a_id=raum_a.id,
        box_b_id=raum_b.id,
        name_a="Tür",
    )

    from_a = await endpoints.for_box(box_id=raum_a.id)
    assert len(from_a) == 1

    other = await _other_box(connections, boxes, from_a[0], raum_a.id)
    assert other is not None
    assert other.name == "B"


@pytest.mark.asyncio
async def test_endpoint_update_moves_box(worlds, boxes, connections, endpoints):
    world, raum_a = await _world_with_box(worlds, boxes, "A")
    raum_b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="B", description="", portable=False
    )
    raum_c = await boxes.add_box(
        world_id=world.id, parent_id=None, name="C", description="", portable=False
    )
    conn = await connections.connect(
        world_id=world.id,
        box_a_id=raum_a.id,
        box_b_id=raum_b.id,
        name_a="Tür",
    )

    eps = await connections.endpoints(conn.id)
    a_ep = next(e for e in eps if e.box_id == raum_a.id)
    updated = await endpoints.update(endpoint_id=a_ep.id, box_id=raum_c.id, name="Tor")

    assert updated.box_id == raum_c.id
    assert updated.name == "Tor"
    conn_after = await connections.get(conn.id)
    assert conn_after is not None


@pytest.mark.asyncio
async def test_disconnect_removes_connection_and_endpoints(
    worlds, boxes, connections, endpoints
):
    world, raum_a = await _world_with_box(worlds, boxes, "A")
    raum_b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="B", description="", portable=False
    )
    conn = await connections.connect(
        world_id=world.id,
        box_a_id=raum_a.id,
        box_b_id=raum_b.id,
        name_a="Tür",
    )

    await connections.disconnect(connection_id=conn.id)

    assert await connections.get(conn.id) is None
    assert await endpoints.for_box(box_id=raum_a.id) == []
    assert await endpoints.for_box(box_id=raum_b.id) == []


@pytest.mark.asyncio
async def test_cross_world_connection(worlds, boxes, connections, endpoints):
    wohnen = await worlds.add_world(name="Wohnen", description="")
    nlp = await worlds.add_world(name="NLP", description="")
    schrank = await boxes.add_box(
        world_id=wohnen.id,
        parent_id=None,
        name="Schrank",
        description="",
        portable=False,
    )
    portal = await boxes.add_box(
        world_id=nlp.id,
        parent_id=None,
        name="Portalraum",
        description="",
        portable=False,
    )

    await connections.connect(
        world_id=wohnen.id,
        box_a_id=schrank.id,
        box_b_id=portal.id,
        name_a="Wardrobe",
    )

    from_schrank = await endpoints.for_box(box_id=schrank.id)
    assert len(from_schrank) == 1
    other = await _other_box(connections, boxes, from_schrank[0], schrank.id)
    assert other is not None
    assert other.world_id == nlp.id
