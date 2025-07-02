"""
Store Layout Data Models
Defines data structures for store layout, sections, products, and waypoints
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class WaypointType(Enum):
    """Types of waypoints in the store"""

    START = "start"
    END = "end"
    JUNCTION = "junction"
    SECTION_ACCESS = "section_access"
    CHECKOUT = "checkout"
    OBSTACLE = "obstacle"


class AisleType(Enum):
    """Types of aisles in the store"""

    MAIN = "main"
    ACCESS = "access"
    CROSS = "cross"


@dataclass
class Point:
    """Represents a 2D coordinate point"""

    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        """Calculate Euclidean distance to another point"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def manhattan_distance_to(self, other: "Point") -> float:
        """Calculate Manhattan distance to another point"""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict) -> "Point":
        """Create Point from dictionary"""
        return cls(x=data["x"], y=data["y"])


@dataclass
class ProductLocation:
    """Represents a product's location in the store"""

    name: str
    section: str
    position: Point
    shelf: str
    picking_time: int  # in seconds
    zone_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "section": self.section,
            "x": self.position.x,
            "y": self.position.y,
            "shelf": self.shelf,
            "picking_time": self.picking_time,
            "zone_id": self.zone_id,
        }

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> "ProductLocation":
        """Create ProductLocation from dictionary"""
        return cls(
            name=name,
            section=data["section"],
            position=Point(data["x"], data["y"]),
            shelf=data["shelf"],
            picking_time=data["picking_time"],
            zone_id=data.get("zone_id"),
        )


@dataclass
class StoreSection:
    """Represents a section in the store"""

    id: str
    name: str
    position: Point
    width: float
    height: float
    color: str
    border_color: str
    products: List[str]
    zone_id: str

    @property
    def center(self) -> Point:
        """Get center point of the section"""
        return Point(
            self.position.x + self.width / 2, self.position.y + self.height / 2
        )

    @property
    def access_point(self) -> Point:
        """Get access point for the section (bottom center)"""
        return Point(self.position.x + self.width / 2, self.position.y)

    def contains_product(self, product_name: str) -> bool:
        """Check if section contains a specific product"""
        return product_name in self.products

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "x": self.position.x,
            "y": self.position.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "border_color": self.border_color,
            "products": self.products,
            "zone_id": self.zone_id,
        }

    @classmethod
    def from_dict(cls, section_id: str, data: Dict) -> "StoreSection":
        """Create StoreSection from dictionary"""
        return cls(
            id=section_id,
            name=data["name"],
            position=Point(data["x"], data["y"]),
            width=data["width"],
            height=data["height"],
            color=data["color"],
            border_color=data["border_color"],
            products=data["products"],
            zone_id=data["zone_id"],
        )


@dataclass
class Waypoint:
    """Represents a waypoint for navigation"""

    id: str
    name: str
    position: Point
    waypoint_type: WaypointType
    connects_to: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "x": self.position.x,
            "y": self.position.y,
            "type": self.waypoint_type.value,
            "connects_to": self.connects_to,
        }

    @classmethod
    def from_dict(cls, waypoint_id: str, data: Dict) -> "Waypoint":
        """Create Waypoint from dictionary"""
        return cls(
            id=waypoint_id,
            name=data["name"],
            position=Point(data["x"], data["y"]),
            waypoint_type=WaypointType(data["type"]),
            connects_to=data.get("connects_to"),
        )


@dataclass
class Aisle:
    """Represents an aisle/path in the store"""

    id: str
    path: List[Point]
    width: float
    aisle_type: AisleType

    def get_length(self) -> float:
        """Calculate total length of the aisle"""
        if len(self.path) < 2:
            return 0.0

        total_length = 0.0
        for i in range(len(self.path) - 1):
            total_length += self.path[i].distance_to(self.path[i + 1])
        return total_length

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "path": [point.to_dict() for point in self.path],
            "width": self.width,
            "type": self.aisle_type.value,
        }

    @classmethod
    def from_dict(cls, aisle_id: str, data: Dict) -> "Aisle":
        """Create Aisle from dictionary"""
        return cls(
            id=aisle_id,
            path=[Point.from_dict(point_data) for point_data in data["path"]],
            width=data["width"],
            aisle_type=AisleType(data["type"]),
        )


@dataclass
class Obstacle:
    """Represents an obstacle in the store"""

    id: str
    position: Point
    width: float
    height: float
    obstacle_type: str

    def contains_point(self, point: Point) -> bool:
        """Check if a point is inside this obstacle"""
        return (
            self.position.x <= point.x <= self.position.x + self.width
            and self.position.y <= point.y <= self.position.y + self.height
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "x": self.position.x,
            "y": self.position.y,
            "width": self.width,
            "height": self.height,
            "type": self.obstacle_type,
        }

    @classmethod
    def from_dict(cls, obstacle_id: str, data: Dict) -> "Obstacle":
        """Create Obstacle from dictionary"""
        return cls(
            id=obstacle_id,
            position=Point(data["x"], data["y"]),
            width=data["width"],
            height=data["height"],
            obstacle_type=data["type"],
        )


@dataclass
class RouteOptimizationConfig:
    """Configuration for route optimization"""

    walking_speed_mps: float
    section_entry_time: int
    section_exit_time: int
    turn_penalty: int
    distance_unit: str
    time_unit: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "walking_speed_mps": self.walking_speed_mps,
            "section_entry_time": self.section_entry_time,
            "section_exit_time": self.section_exit_time,
            "turn_penalty": self.turn_penalty,
            "distance_unit": self.distance_unit,
            "time_unit": self.time_unit,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RouteOptimizationConfig":
        """Create RouteOptimizationConfig from dictionary"""
        return cls(
            walking_speed_mps=data["walking_speed_mps"],
            section_entry_time=data["section_entry_time"],
            section_exit_time=data["section_exit_time"],
            turn_penalty=data["turn_penalty"],
            distance_unit=data["distance_unit"],
            time_unit=data["time_unit"],
        )


@dataclass
class StoreInfo:
    """Store information and dimensions"""

    name: str
    width: float
    height: float
    grid_size: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "grid_size": self.grid_size,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "StoreInfo":
        """Create StoreInfo from dictionary"""
        return cls(
            name=data["name"],
            width=data["width"],
            height=data["height"],
            grid_size=data["grid_size"],
        )


class StoreLayout:
    """Main store layout class that contains all store data"""

    def __init__(self):
        self.store_info: Optional[StoreInfo] = None
        self.entrance: Optional[Waypoint] = None
        self.sections: Dict[str, StoreSection] = {}
        self.waypoints: Dict[str, Waypoint] = {}
        self.aisles: Dict[str, Aisle] = {}
        self.product_locations: Dict[str, ProductLocation] = {}
        self.obstacles: Dict[str, Obstacle] = {}
        self.route_config: Optional[RouteOptimizationConfig] = None

    def load_from_json(self, json_file_path: str) -> bool:
        """Load store layout from JSON file"""
        try:
            if not os.path.exists(json_file_path):
                print(f"Store layout file not found: {json_file_path}")
                return False

            with open(json_file_path, "r") as file:
                data = json.load(file)

            # Load store info
            if "store_info" in data:
                self.store_info = StoreInfo.from_dict(data["store_info"])

            # Load entrance
            if "entrance" in data:
                entrance_data = data["entrance"]
                self.entrance = Waypoint(
                    id="entrance",
                    name=entrance_data["name"],
                    position=Point(entrance_data["x"], entrance_data["y"]),
                    waypoint_type=WaypointType.START,
                )

            # Load sections
            if "sections" in data:
                for section_id, section_data in data["sections"].items():
                    self.sections[section_id] = StoreSection.from_dict(
                        section_id, section_data
                    )

            # Load waypoints
            if "waypoints" in data:
                for waypoint_id, waypoint_data in data["waypoints"].items():
                    self.waypoints[waypoint_id] = Waypoint.from_dict(
                        waypoint_id, waypoint_data
                    )

            # Load aisles
            if "aisles" in data:
                for aisle_data in data["aisles"]:
                    aisle = Aisle.from_dict(aisle_data["id"], aisle_data)
                    self.aisles[aisle.id] = aisle

            # Load product locations
            if "product_locations" in data:
                for product_name, product_data in data["product_locations"].items():
                    self.product_locations[product_name] = ProductLocation.from_dict(
                        product_name, product_data
                    )

            # Load obstacles
            if "obstacles" in data:
                for obstacle_data in data["obstacles"]:
                    obstacle = Obstacle.from_dict(obstacle_data["id"], obstacle_data)
                    self.obstacles[obstacle.id] = obstacle

            # Load route optimization config
            if "route_optimization" in data:
                self.route_config = RouteOptimizationConfig.from_dict(
                    data["route_optimization"]
                )

            print(f"Store layout loaded successfully from {json_file_path}")
            return True

        except Exception as e:
            print(f"Error loading store layout: {e}")
            return False

    def get_product_location(self, product_name: str) -> Optional[ProductLocation]:
        """Get location of a specific product"""
        return self.product_locations.get(product_name)

    def get_section_by_product(self, product_name: str) -> Optional[StoreSection]:
        """Get section that contains a specific product"""
        product_location = self.get_product_location(product_name)
        if product_location:
            return self.sections.get(product_location.section)
        return None

    def get_products_in_section(self, section_id: str) -> List[str]:
        """Get all products in a specific section"""
        section = self.sections.get(section_id)
        if section:
            return section.products
        return []

    def get_section_access_waypoint(self, section_id: str) -> Optional[Waypoint]:
        """Get access waypoint for a section"""
        for waypoint in self.waypoints.values():
            if (
                waypoint.waypoint_type == WaypointType.SECTION_ACCESS
                and waypoint.connects_to == section_id
            ):
                return waypoint
        return None

    def get_all_sections_for_products(
        self, product_names: List[str]
    ) -> List[StoreSection]:
        """Get all sections needed for a list of products"""
        sections = []
        section_ids = set()

        for product_name in product_names:
            section = self.get_section_by_product(product_name)
            if section and section.id not in section_ids:
                sections.append(section)
                section_ids.add(section.id)

        return sections

    def calculate_distance_between_points(self, point1: Point, point2: Point) -> float:
        """Calculate distance between two points"""
        return point1.distance_to(point2)

    def is_point_blocked(self, point: Point) -> bool:
        """Check if a point is blocked by an obstacle"""
        for obstacle in self.obstacles.values():
            if obstacle.contains_point(point):
                return True
        return False

    def to_dict(self) -> Dict:
        """Convert entire store layout to dictionary"""
        return {
            "store_info": self.store_info.to_dict() if self.store_info else None,
            "entrance": self.entrance.to_dict() if self.entrance else None,
            "sections": {
                sid: section.to_dict() for sid, section in self.sections.items()
            },
            "waypoints": {
                wid: waypoint.to_dict() for wid, waypoint in self.waypoints.items()
            },
            "aisles": [aisle.to_dict() for aisle in self.aisles.values()],
            "product_locations": {
                name: location.to_dict()
                for name, location in self.product_locations.items()
            },
            "obstacles": [obstacle.to_dict() for obstacle in self.obstacles.values()],
            "route_optimization": (
                self.route_config.to_dict() if self.route_config else None
            ),
        }

    def __str__(self) -> str:
        """String representation of store layout"""
        return f"StoreLayout(sections={len(self.sections)}, products={len(self.product_locations)}, waypoints={len(self.waypoints)})"
