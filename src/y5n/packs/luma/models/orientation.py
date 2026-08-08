"""A normalized planar orientation.

The canonical value is an angle in degrees (math convention: 0° = east /
positive x-axis, angles count counterclockwise). The unit vector is
derived. ``up``/``down``/``in``/``out`` have no planar orientation and are
represented as ``None`` on an Endpoint.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Direction word -> angle in degrees.
_DIRECTIONS: dict[str, float] = {
    "east": 0.0,
    "north": 90.0,
    "west": 180.0,
    "south": 270.0,
    "north-east": 45.0,
    "south-east": 315.0,
    "south-west": 225.0,
    "north-west": 135.0,
}


@dataclass(frozen=True)
class Orientation:
    angle: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "angle", self.angle % 360.0)

    @classmethod
    def from_notation(cls, notation: str | None) -> Orientation | None:
        """Parse a direction word or a raw angle ('90', '45°')."""
        text = (notation or "").strip().lower()
        if not text:
            return None
        if text in _DIRECTIONS:
            return cls(_DIRECTIONS[text])
        value = text.removesuffix("°")
        try:
            return cls(float(value))
        except ValueError:
            return None

    @classmethod
    def opposite(cls, other: Orientation) -> Orientation:
        return cls(other.angle + 180.0)

    def vector(self) -> tuple[float, float]:
        rad = math.radians(self.angle)
        return (math.cos(rad), math.sin(rad))

    def dot(self, other: Orientation) -> float:
        ax, ay = self.vector()
        bx, by = other.vector()
        return ax * bx + ay * by

    def word(self) -> str:
        """Nearest known direction word, else the raw angle."""
        for word, angle in _DIRECTIONS.items():
            if abs(self.angle - angle) < 1e-6:
                return word
        return f"{self.angle:.0f}°"


def angle_difference(a: float, b: float) -> float:
    """Smallest absolute difference between two angles in degrees."""
    diff = (a - b) % 360.0
    return min(diff, 360.0 - diff)


__all__ = ["Orientation", "angle_difference"]
