from y5n.sdk import context, io, ports, session

_OPPOSITE = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
    "up": "down",
    "down": "up",
    "in": "out",
    "out": "in",
}


async def main():
    ses = await session.current()
    current_box = ses.data.get("luma.current_box")
    current_world = ses.data.get("luma.current_world")
    if not current_box or not current_world:
        await io.write("You are not inside any box. Use 'enter' first.")
        return

    target_ref = context.request().arg(0)
    direction = context.request().option("direction") or ""
    via = context.request().option("via") or target_ref
    twoway = context.request().has_option("twoway")
    world_ref = context.request().option("world")

    if not target_ref:
        await io.write("Error: target name is required.")
        return

    target_world = current_world
    if world_ref:
        worlds = ports.get("luma.world.service")
        world = await worlds.get_world_by_name(name=world_ref)
        if world is None:
            await io.write(f"World '{world_ref}' not found.")
            return
        target_world = world.id

    boxes = ports.get("luma.box.service")
    existing = await boxes.list_boxes(world_id=target_world, parent_id=None)
    target = next((b for b in existing if b.name.lower() == target_ref.lower()), None)

    if target is None:
        await io.write(f"Box '{target_ref}' not found.")
        return

    exits = ports.get("luma.exit.service")

    await exits.connect(
        world_id=current_world,
        source_box_id=current_box,
        target_box_id=target.id,
        target_world_id=target_world,
        name=via,
        direction=direction,
    )

    lines = [f"Connected to '{target.name}' via '{via}'."]

    if twoway:
        rev_dir = _OPPOSITE.get(direction.lower()) if direction else ""
        await exits.connect(
            world_id=target_world,
            source_box_id=target.id,
            target_box_id=current_box,
            target_world_id=current_world,
            name=via,
            direction=rev_dir,
        )
        lines.append("  Reverse exit created.")

    await io.write("\n".join(lines))
