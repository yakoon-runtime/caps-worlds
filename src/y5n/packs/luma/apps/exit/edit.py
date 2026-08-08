from y5n.sdk import context, io, ports

from ...models import Orientation


async def main():
    exit_name = context.request().arg(0)
    world_ref = context.request().option("world")
    box_ref = context.request().option("box")
    new_name = context.request().option("new-name")
    description = context.request().option("description")
    direction = context.request().option("direction")

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

    final_name = new_name if new_name is not None else ep.name
    final_desc = description if description is not None else ep.description
    final_orientation = (
        Orientation.from_notation(direction) if direction is not None else None
    )
    final_orientation = (
        final_orientation if final_orientation is not None else ep.orientation
    )

    await endpoints.update(
        endpoint_id=ep.id,
        name=final_name,
        description=final_desc,
        orientation=final_orientation,
    )
    await io.write(f"Exit '{exit_name}' updated.")
