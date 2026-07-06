from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Box:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return max(0.0, self.right - self.left)

    @property
    def height(self) -> float:
        return max(0.0, self.bottom - self.top)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def centroid(self) -> Point:
        return Point((self.left + self.right) / 2, (self.top + self.bottom) / 2)

    def intersection_over_union(self, other: Box) -> float:
        left = max(self.left, other.left)
        top = max(self.top, other.top)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)

        overlap = Box(left, top, right, bottom).area
        if overlap <= 0:
            return 0.0

        union = self.area + other.area - overlap
        if union <= 0:
            return 0.0
        return overlap / union


Polygon = list[Point]


def point_in_polygon(point: Point, polygon: Polygon) -> bool:
    if len(polygon) < 3:
        return False

    inside = False
    previous = polygon[-1]
    for current in polygon:
        crosses_y = (current.y > point.y) != (previous.y > point.y)
        if crosses_y:
            slope_x = (previous.x - current.x) * (point.y - current.y)
            slope_y = previous.y - current.y
            x_at_y = slope_x / slope_y + current.x if slope_y else current.x
            if point.x < x_at_y:
                inside = not inside
        previous = current
    return inside


def polygon_from_tuples(points: list[tuple[int, int]]) -> Polygon:
    return [Point(float(x), float(y)) for x, y in points]

