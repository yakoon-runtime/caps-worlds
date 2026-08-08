from __future__ import annotations

from dataclasses import dataclass

from .orientation import Orientation


@dataclass
class Endpoint:
    """The local view of a connection as seen from one box.

    An endpoint is first-class: it carries its own name, description and
    orientation, and it is the thing a user navigates by.
    """

    id: str
    box_id: str
    connection_id: str
    name: str = ""
    description: str = ""
    orientation: Orientation | None = None
