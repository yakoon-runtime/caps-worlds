from y5n.sdk import context, io, ports, session

from ..models import Orientation, angle_difference


async def main():
    ses = await session.current()
    current_box = ses.data.get("luma.current_box")
    current_world = ses.data.get("luma.current_world")
    if not current_box:
        await io.write("You are not inside any box.")
        return

    ref = context.request().arg(0) or ""
    if not ref:
        await io.write("Go where?")
        return

    boxes = ports.get("luma.box.service")

    if ref == "..":
        box = await boxes.get_box(box_id=current_box)
        if box is None or box.parent_id is None:
            await io.write("Cannot go up from here.")
            return
        parent = await boxes.get_box(box_id=box.parent_id)
        await ports.get("session").update(
            patch={"data": {"luma.current_box": box.parent_id}}
        )
        await io.write(f"{parent.name if parent else '..'}")
        return

    children = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
    child = next((c for c in children if c.name.lower() == ref.lower()), None)
    if child is not None:
        await ports.get("session").update(
            patch={"data": {"luma.current_box": child.id}}
        )
        await io.write(f"{child.name}")
        return

    endpoints = ports.get("luma.endpoint.service")
    connections = ports.get("luma.connection.service")
    from_here = await endpoints.for_box(box_id=current_box)

    by_name = [e for e in from_here if e.name.lower() == ref.lower()]
    if len(by_name) == 1:
        endpoint = by_name[0]
    elif len(by_name) > 1:
        await io.write(f"Multiple exits named '{ref}' from here.")
        return
    else:
        wanted = Orientation.from_notation(ref)
        placed = [e for e in from_here if e.orientation is not None]
        if wanted is None or not placed:
            await io.write(f"Nothing leads '{ref}' from here.")
            return
        nearest = min(
            placed,
            key=lambda e: angle_difference(e.orientation.angle, wanted.angle),
        )
        best_diff = angle_difference(nearest.orientation.angle, wanted.angle)
        close = [
            e
            for e in placed
            if angle_difference(e.orientation.angle, wanted.angle) <= best_diff + 1e-9
        ]
        if len(close) > 1:
            names = ", ".join(e.name or "?" for e in close)
            await io.write(f"Multiple exits lead '{ref}': {names}. Use a name.")
            return
        endpoint = nearest

    connection = await connections.get(endpoint.connection_id)
    if connection is None:
        await io.write("Exit leads nowhere (connection missing).")
        return
    other = await connections.other_endpoint(connection, current_box)
    if other is None:
        await io.write("Exit leads nowhere (connection incomplete).")
        return

    target = await boxes.get_box(box_id=other.box_id)
    if target is None:
        await io.write(f"Exit leads nowhere (box #{other.box_id} missing).")
        return

    target_world = target.world_id or current_world
    patch = {"luma.current_box": target.id}
    if target_world != current_world:
        patch["luma.current_world"] = target_world
    await ports.get("session").update(patch={"data": patch})

    if target_world != current_world:
        worlds = ports.get("luma.world.service")
        world = await worlds.get_world(world_id=target_world)
        world_name = world.name if world else f"world {target_world}"
        await io.write(f"{target.name} (world '{world_name}')")
    else:
        await io.write(f"{target.name}")
