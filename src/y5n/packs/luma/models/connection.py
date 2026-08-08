from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Connection:
    """A topological link between two boxes.

    The connection is the path itself: it connects two endpoints and is
    navigable in both directions unless ``bidirectional`` is false.
    """

    id: str
    world_id: str
    endpoint_a_id: str
    endpoint_b_id: str
    bidirectional: bool = True
    description: str = ""
    kind: str = "path"
