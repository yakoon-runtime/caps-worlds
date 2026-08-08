from y5n.sdk import context, io, ports


async def main():
    world_ref = context.request().option("world")
    box_ref = context.request().option("box")

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_id)
        if w is None:
            await io.write("World not found.")
            return
        world_id = w.id

    boxes = ports.get("luma.box.service")
    endpoints = ports.get("luma.endpoint.service")
    connections = ports.get("luma.connection.service")

    rows = []

    if box_ref:
        all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
        box_id = next(
            (b.id for b in all_boxes if b.name.lower() == box_ref.lower()), None
        )
        if box_id is None:
            await io.write(f"Box '{box_ref}' not found.")
            return
        for ep in await endpoints.for_box(box_id=box_id):
            rows.append((ep, box_id))

    else:
        for connection in await connections.for_world(world_id=world_id):
            for ep in await connections.endpoints(connection_id=connection.id):
                rows.append((ep, ep.box_id))

    if not rows:
        await io.write("No exits.")
        return

    lines = ["Exits:"]
    for ep, source_box_id in rows:
        source = await boxes.get_box(box_id=source_box_id)
        connection = await connections.get(connection_id=ep.connection_id)
        other = (
            await connections.other_endpoint(
                connection_id=connection.id, box_id=source_box_id
            )
            if connection
            else None
        )
        target = await boxes.get_box(box_id=other.box_id) if other else None
        src_name = source.name if source else f"#{source_box_id}"
        tgt_name = target.name if target else f"#{other.box_id if other else '?'}"
        if target and target.world_id != world_id:
            world = await worlds.get_world(world_id=target.world_id)
            world_name = world.name if world else f"world {target.world_id}"
            tgt_name = f"{tgt_name} ({world_name})"
        line = f"  #{ep.id} {ep.name or '?'}: {src_name} -> {tgt_name}"
        if ep.orientation is not None:
            line += f" ({ep.orientation.word()})"
        lines.append(line)
    await io.write("\n".join(lines))
