from y5n.sdk import context, io, ports


async def main():
    exit_name = context.request().arg(0)
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
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
    src = next((b for b in all_boxes if b.name.lower() == box_ref.lower()), None)
    if src is None:
        await io.write(f"Box '{box_ref}' not found.")
        return

    endpoints = ports.get("luma.endpoint.service")
    from_src = await endpoints.for_box(box_id=src.id)
    ep = next((e for e in from_src if e.name.lower() == exit_name.lower()), None)
    if ep is None:
        await io.write(f"Exit '{exit_name}' not found in '{box_ref}'.")
        return

    connections = ports.get("luma.connection.service")
    connection = await connections.get(ep.connection_id)
    other = await connections.other_endpoint(connection, src.id) if connection else None
    target = await boxes.get_box(box_id=other.box_id) if other else None
    tgt_name = target.name if target else f"#{other.box_id if other else '?'}"

    lines = [
        f"Exit '{ep.name}'",
        f"  From: {box_ref} (#{ep.box_id})",
        f"  To:   {tgt_name}",
    ]
    if target and target.world_id != world_id:
        world = await worlds.get_world(world_id=target.world_id)
        world_name = world.name if world else f"world {target.world_id}"
        lines.append(f"  World: {world_name}")
    if ep.orientation is not None:
        lines.append(f"  Direction: {ep.orientation.word()}")
    if connection is not None and not connection.bidirectional:
        lines.append("  One-way")
    if connection is not None and connection.kind != "path":
        lines.append(f"  Kind: {connection.kind}")
    if ep.description:
        lines.append(f"  Description: {ep.description}")
    await io.write("\n".join(lines))
