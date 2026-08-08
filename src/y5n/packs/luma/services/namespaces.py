from y5n.runtime.api.naming import Key, Namespace


def world_key(world_id: str) -> Key:
    return Key.from_parts("luma", "world", "global", world_id)


def box_key(box_id: str) -> Key:
    return Key.from_parts("luma", "box", "global", box_id)


def endpoint_key(endpoint_id: str) -> Key:
    return Key.from_parts("luma", "endpoint", "global", endpoint_id)


def connection_key(connection_id: str) -> Key:
    return Key.from_parts("luma", "connection", "global", connection_id)


def note_key(note_id: str) -> Key:
    return Key.from_parts("luma", "note", "global", note_id)


def world_namespace() -> Namespace:
    return Namespace("luma", "world", "global")


def box_namespace() -> Namespace:
    return Namespace("luma", "box", "global")


def endpoint_namespace() -> Namespace:
    return Namespace("luma", "endpoint", "global")


def connection_namespace() -> Namespace:
    return Namespace("luma", "connection", "global")


def note_namespace() -> Namespace:
    return Namespace("luma", "note", "global")
