from y5n.sdk import context, io, ports, session


def _parse_angle(raw: str | None) -> float | None:
    text = (raw or "").strip().removesuffix("°")
    try:
        return float(text)
    except ValueError:
        return None


async def main():
    ses = await session.current()
    current_box = ses.data.get("luma.current_box")
    current_world = ses.data.get("luma.current_world")
    if not current_box or not current_world:
        await io.write("You are not inside any box. Use 'enter' first.")
        return

    angle = _parse_angle(context.request().arg(0))
    if angle is None:
        await io.write("Error: angle required (e.g. 'refine split 90').")
        return

    offset = 0.0
    raw_offset = context.request().option("offset")
    if raw_offset:
        try:
            offset = float(raw_offset)
        except ValueError:
            await io.write("Error: offset must be a number.")
            return
    if not -1.0 <= offset <= 1.0:
        await io.write("Error: offset must be between -1 and 1.")
        return

    refine = ports.get("luma.refine.service")
    try:
        result = await refine.split(
            world_id=current_world,
            box_id=current_box,
            angle_deg=angle,
            offset=offset,
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    new_name = result["new_box"].name
    lines = [
        f"Split '{result['box'].name}' into '{result['box'].name}' and '{new_name}'.",
        f"  {result['moved']} exit(s) moved to the new room.",
    ]
    await io.write("\n".join(lines))
