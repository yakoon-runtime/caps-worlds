from y5n.sdk import io, session


async def main():
    ses = await session.current()
    current_world = ses.data.get("luma.current_world")
    current_box = ses.data.get("luma.current_box")

    if current_world is None and current_box is None:
        await io.write("Nowhere to leave.")
        return

    await session.update(patch={"data": {"luma.current_world": None}})
    await session.update(patch={"data": {"luma.current_box": None}})

    parts = []
    if current_world:
        parts.append(f"'{current_world}'")
    if current_box:
        parts.append(f"box #{current_box}")
    await io.write(f"Left {' '.join(parts)}.")
