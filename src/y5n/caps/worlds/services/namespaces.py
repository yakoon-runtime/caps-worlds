from y5n.runtime.api.naming import Key, Namespace


def world_key(world_id: str) -> Key:
    return Key.from_parts("worlds", "world", "global", world_id)


def box_key(box_id: str) -> Key:
    return Key.from_parts("worlds", "box", "global", box_id)


def endpoint_key(endpoint_id: str) -> Key:
    return Key.from_parts("worlds", "endpoint", "global", endpoint_id)


def connection_key(connection_id: str) -> Key:
    return Key.from_parts("worlds", "connection", "global", connection_id)


def note_key(note_id: str) -> Key:
    return Key.from_parts("worlds", "note", "global", note_id)


def world_namespace() -> Namespace:
    return Namespace("worlds", "world", "global")


def box_namespace() -> Namespace:
    return Namespace("worlds", "box", "global")


def endpoint_namespace() -> Namespace:
    return Namespace("worlds", "endpoint", "global")


def connection_namespace() -> Namespace:
    return Namespace("worlds", "connection", "global")


def note_namespace() -> Namespace:
    return Namespace("worlds", "note", "global")
