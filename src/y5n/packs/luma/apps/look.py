from y5n.sdk import io, ports, session


async def main():
    ses = await session.current()
    current_box = ses.data.get("luma.current_box")
    current_world = ses.data.get("luma.current_world")

    if not current_box:
        await io.write("You are not inside any box. Use 'enter' first.")
        return

    boxes = ports.get("luma.box.service")
    box = await boxes.get_box(box_id=current_box)
    if box is None:
        await io.write("Current box not found.")
        return

    worlds = ports.get("luma.world.service")

    lines = [f"[{box.name}]"]
    if box.description:
        lines.append(f"  {box.description}")

    endpoints = ports.get("luma.endpoint.service")
    connections = ports.get("luma.connection.service")
    from_here = await endpoints.for_box(box_id=box.id)

    if from_here:
        lines.append("")
        lines.append("Exits:")
        for ep in from_here:
            connection = await connections.get(connection_id=ep.connection_id)
            other = (
                await connections.other_endpoint(
                    connection_id=connection.id, box_id=box.id
                )
                if connection
                else None
            )
            target = await boxes.get_box(box_id=other.box_id) if other else None
            target_name = (
                target.name if target else f"#{other.box_id if other else '?'}"
            )
            if target and target.world_id != current_world:
                world = await worlds.get_world(world_id=target.world_id)
                world_name = world.name if world else f"world {target.world_id}"
                target_name = f"{target_name} (world '{world_name}')"
            label = ep.name or (ep.orientation.word() if ep.orientation else "?")
            if ep.orientation is not None and ep.name:
                lines.append(f"  {ep.orientation.word()}: {label} -> {target_name}")
            else:
                lines.append(f"  {label} -> {target_name}")

    items = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
    items = [b for b in items if b.portable]
    if items:
        lines.append("")
        lines.append("Contains:")
        for b in items:
            parts = [f"  {b.name}"]
            if b.description:
                parts.append(f" - {b.description}")
            lines.append("".join(parts))

    await io.write("\n".join(lines))
