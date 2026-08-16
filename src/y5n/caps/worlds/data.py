from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorldData:
    CURRENT_VERSION = 1
    name: str
    description: str = ""
    entry_box_id: str | None = None
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "entry_box_id": self.entry_box_id,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WorldData:
        d = dict(d or {})
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            entry_box_id=d.get("entry_box_id"),
            _v=d.get("_v", 0),
        )


@dataclass
class BoxData:
    CURRENT_VERSION = 1
    world_id: str
    parent_id: str | None
    name: str
    description: str = ""
    portable: bool = False
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "description": self.description,
            "portable": self.portable,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> BoxData:
        d = dict(d or {})
        return cls(
            world_id=d["world_id"],
            parent_id=d.get("parent_id"),
            name=d["name"],
            description=d.get("description", ""),
            portable=d.get("portable", False),
            _v=d.get("_v", 0),
        )


@dataclass
class EndpointData:
    CURRENT_VERSION = 1
    box_id: str
    connection_id: str
    name: str = ""
    description: str = ""
    orientation: float | None = None
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {
            "box_id": self.box_id,
            "connection_id": self.connection_id,
            "name": self.name,
            "description": self.description,
            "orientation": self.orientation,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> EndpointData:
        d = dict(d or {})
        return cls(
            box_id=d["box_id"],
            connection_id=d["connection_id"],
            name=d.get("name", ""),
            description=d.get("description", ""),
            orientation=d.get("orientation"),
            _v=d.get("_v", 0),
        )


@dataclass
class ConnectionData:
    CURRENT_VERSION = 1
    world_id: str
    endpoint_a_id: str
    endpoint_b_id: str
    bidirectional: bool = True
    description: str = ""
    kind: str = "path"
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id,
            "endpoint_a_id": self.endpoint_a_id,
            "endpoint_b_id": self.endpoint_b_id,
            "bidirectional": self.bidirectional,
            "description": self.description,
            "kind": self.kind,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ConnectionData:
        d = dict(d or {})
        return cls(
            world_id=d["world_id"],
            endpoint_a_id=d["endpoint_a_id"],
            endpoint_b_id=d["endpoint_b_id"],
            bidirectional=d.get("bidirectional", True),
            description=d.get("description", ""),
            kind=d.get("kind", "path"),
            _v=d.get("_v", 0),
        )


@dataclass
class NoteData:
    CURRENT_VERSION = 1
    name: str
    content: str = ""
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {"name": self.name, "content": self.content, "_v": self._v}

    @classmethod
    def from_dict(cls, d: dict) -> NoteData:
        d = dict(d or {})
        return cls(name=d["name"], content=d.get("content", ""), _v=d.get("_v", 0))
