"""
Cypher Tools
============

This module provides wrapper functions for interacting with Neo4j
graph database using Cypher queries.

The CypherTools class handles:
- Database connection management
- Query construction and execution
- Result formatting
- Error handling and retries

Example Usage:
    tools = CypherTools()
    destinations = tools.find_by_category("MUSEUM", location="Paris")
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Neo4j driver import with fallback
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    GraphDatabase = None
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not installed. Graph features will use mock data.")


class CypherTools:
    """
    Tool class for Neo4j graph database operations.

    This class manages connections to Neo4j and provides
    high-level methods for querying travel destination data.

    Attributes:
        uri: Neo4j connection URI
        username: Database username
        password: Database password
        driver: Neo4j driver instance
    """

    def __init__(self):
        """Initialize CypherTools with connection parameters from environment."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "")
        self.driver = None
        self._connected = False

        # Attempt connection if driver available
        if NEO4J_AVAILABLE and self.password and "your_" not in self.password:
            self._connect()

        logger.info(f"CypherTools initialized (connected: {self._connected})")

    def _connect(self) -> bool:
        """
        Establish connection to Neo4j database.

        Returns:
            bool: True if connection successful
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Verify connection
            self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
            return False

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            self._connected = False
            logger.info("Neo4j connection closed")

    def execute_query(self, query: str, parameters: dict = None) -> list:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            list: Query results as list of dictionaries
        """
        parameters = parameters or {}

        if not self._connected:
            logger.warning("Not connected to Neo4j, returning mock data")
            return self._get_mock_data(query)

        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def find_by_category(
        self,
        category: str,
        location: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """
        Find destinations by category.

        Args:
            category: Destination category (MUSEUM, BEACH, etc.)
            location: Optional location filter
            limit: Maximum results

        Returns:
            list: Matching destinations
        """
        if location:
            query = """
            MATCH (d:Destination)-[:IN_REGION]->(r:Region)
            WHERE d.category = $category AND r.name CONTAINS $location
            RETURN d.name as name, d.category as category, d.rating as rating,
                   d.description as description, r.name as region
            ORDER BY d.rating DESC
            LIMIT $limit
            """
            parameters = {"category": category, "location": location, "limit": limit}
        else:
            query = """
            MATCH (d:Destination)
            WHERE d.category = $category
            RETURN d.name as name, d.category as category, d.rating as rating,
                   d.description as description
            ORDER BY d.rating DESC
            LIMIT $limit
            """
            parameters = {"category": category, "limit": limit}

        results = self.execute_query(query, parameters)

        if not results:
            return self._get_mock_destinations(category, location, limit)

        return results

    def find_destinations_in_region(self, region: str, limit: int = 10) -> list:
        """
        Find all destinations in a region.

        Args:
            region: Region name
            limit: Maximum results

        Returns:
            list: Destinations in the region
        """
        query = """
        MATCH (d:Destination)-[:IN_REGION]->(r:Region)
        WHERE r.name CONTAINS $region
        RETURN d.name as name, d.category as category, d.rating as rating,
               d.description as description, r.name as region
        ORDER BY d.rating DESC
        LIMIT $limit
        """
        results = self.execute_query(query, {"region": region, "limit": limit})

        if not results:
            return self._get_mock_destinations(None, region, limit)

        return results

    def find_nearby_destinations(
        self,
        location: str,
        max_distance_km: int = 50,
        limit: int = 10
    ) -> list:
        """
        Find destinations near a location.

        Args:
            location: Reference location name
            max_distance_km: Maximum distance in kilometers
            limit: Maximum results

        Returns:
            list: Nearby destinations
        """
        query = """
        MATCH (origin:Destination {name: $location})-[r:NEAR]-(nearby:Destination)
        WHERE r.distance_km <= $max_distance
        RETURN nearby.name as name, nearby.category as category,
               nearby.rating as rating, r.distance_km as distance
        ORDER BY r.distance_km ASC
        LIMIT $limit
        """
        results = self.execute_query(query, {
            "location": location,
            "max_distance": max_distance_km,
            "limit": limit
        })

        if not results:
            return self._get_mock_nearby(location, limit)

        return results

    def find_connected_destinations(
        self,
        location: str,
        connection_types: list = None,
        limit: int = 10
    ) -> list:
        """
        Find destinations connected to a location.

        Args:
            location: Reference location
            connection_types: Types of connections to follow
            limit: Maximum results

        Returns:
            list: Connected destinations
        """
        connection_types = connection_types or ["NEAR", "SIMILAR_TO", "RECOMMENDED_WITH"]
        
        # Validation to prevent Cypher injection
        allowed_types = {"NEAR", "SIMILAR_TO", "RECOMMENDED_WITH", "IN_REGION", "NEXT_TO"}
        valid_types = [t for t in connection_types if t in allowed_types]
        if not valid_types:
            valid_types = ["NEAR"]

        # Build relationship type clause
        rel_types = "|".join(valid_types)

        query = f"""
        MATCH (origin:Destination)-[r:{rel_types}]-(connected:Destination)
        WHERE origin.name CONTAINS $location
        RETURN connected.name as name, connected.category as category,
               connected.rating as rating, type(r) as connection_type
        ORDER BY connected.rating DESC
        LIMIT $limit
        """
        results = self.execute_query(query, {"location": location, "limit": limit})

        if not results:
            return self._get_mock_connected(location, limit)

        return results

    def find_route_suggestions(
        self,
        start_location: str,
        preferences: list = None
    ) -> list:
        """
        Find suggested routes from a starting location.

        Args:
            start_location: Starting point
            preferences: Category preferences

        Returns:
            list: Route suggestions
        """
        preferences = preferences or []

        query = """
        MATCH path = (start:Destination)-[:NEAR*1..3]->(end:Destination)
        WHERE start.name CONTAINS $start_location
        RETURN [n in nodes(path) | n.name] as route,
               [n in nodes(path) | n.category] as categories,
               reduce(d = 0, r in relationships(path) | d + r.distance_km) as total_distance
        ORDER BY total_distance ASC
        LIMIT 5
        """
        results = self.execute_query(query, {"start_location": start_location})

        if not results:
            return self._get_mock_routes(start_location)

        return results

    def search_destinations(
        self,
        categories: list = None,
        location: str = None,
        budget: str = None,
        limit: int = 10
    ) -> list:
        """
        General destination search with multiple filters.

        Args:
            categories: List of categories to include
            location: Location filter
            budget: Budget level filter
            limit: Maximum results

        Returns:
            list: Matching destinations
        """
        conditions = []
        parameters = {"limit": limit}

        if categories:
            conditions.append("d.category IN $categories")
            parameters["categories"] = categories

        if location:
            conditions.append("(r.name CONTAINS $location OR d.name CONTAINS $location)")
            parameters["location"] = location

        if budget:
            budget_mapping = {"budget": ["$"], "moderate": ["$", "$$"], "luxury": ["$$", "$$$"]}
            conditions.append("d.price_range IN $price_ranges")
            parameters["price_ranges"] = budget_mapping.get(budget, ["$", "$$"])

        where_clause = " AND ".join(conditions) if conditions else "true"

        query = f"""
        MATCH (d:Destination)
        OPTIONAL MATCH (d)-[:IN_REGION]->(r:Region)
        WHERE {where_clause}
        RETURN d.name as name, d.category as category, d.rating as rating,
               d.description as description, r.name as region
        ORDER BY d.rating DESC
        LIMIT $limit
        """

        results = self.execute_query(query, parameters)

        if not results:
            return self._get_mock_destinations(
                categories[0] if categories else None,
                location,
                limit
            )

        return results

    def get_popular_destinations(self, limit: int = 10) -> list:
        """
        Get most popular destinations overall.

        Args:
            limit: Maximum results

        Returns:
            list: Popular destinations
        """
        query = """
        MATCH (d:Destination)
        RETURN d.name as name, d.category as category, d.rating as rating,
               d.description as description
        ORDER BY d.rating DESC, d.popularity DESC
        LIMIT $limit
        """
        results = self.execute_query(query, {"limit": limit})

        if not results:
            return self._get_mock_popular(limit)

        return results

    # ==================== Mock Data Methods ====================
    # These provide sample data when Neo4j is not connected

    def _get_mock_data(self, query: str) -> list:
        """Return appropriate mock data based on query."""
        if "NEAR" in query:
            return self._get_mock_nearby("Sample", 5)
        if "category" in query.lower():
            return self._get_mock_destinations("ATTRACTION", None, 5)
        return self._get_mock_popular(5)

    def _get_mock_destinations(self, category: str, location: str, limit: int) -> list:
        """Generate mock destination data."""
        mock_destinations = [
            {
                "name": f"Sample {category or 'Attraction'} {i}",
                "category": category or "ATTRACTION",
                "rating": 4.5 - (i * 0.1),
                "description": f"A wonderful {category.lower() if category else 'place'} to visit",
                "region": location or "Sample Region"
            }
            for i in range(min(limit, 5))
        ]
        return mock_destinations

    def _get_mock_nearby(self, location: str, limit: int) -> list:
        """Generate mock nearby destinations."""
        return [
            {
                "name": f"Nearby Place {i}",
                "category": ["MUSEUM", "PARK", "LANDMARK"][i % 3],
                "rating": 4.2 - (i * 0.1),
                "distance": 5 + (i * 3)
            }
            for i in range(min(limit, 5))
        ]

    def _get_mock_connected(self, location: str, limit: int) -> list:
        """Generate mock connected destinations."""
        return [
            {
                "name": f"Connected Destination {i}",
                "category": ["BEACH", "MOUNTAIN", "CITY"][i % 3],
                "rating": 4.3 - (i * 0.1),
                "connection_type": ["SIMILAR_TO", "RECOMMENDED_WITH", "NEAR"][i % 3]
            }
            for i in range(min(limit, 5))
        ]

    def _get_mock_routes(self, start: str) -> list:
        """Generate mock route suggestions."""
        return [
            {
                "route": [start, "Stop 1", "Stop 2", f"Destination {i}"],
                "categories": ["CITY", "LANDMARK", "MUSEUM", "ATTRACTION"],
                "total_distance": 50 + (i * 20)
            }
            for i in range(3)
        ]

    def _get_mock_popular(self, limit: int) -> list:
        """Generate mock popular destinations."""
        popular_places = [
            {"name": "Eiffel Tower", "category": "LANDMARK", "rating": 4.8, "description": "Iconic Paris landmark"},
            {"name": "Colosseum", "category": "HISTORICAL", "rating": 4.7, "description": "Ancient Roman amphitheater"},
            {"name": "Machu Picchu", "category": "HISTORICAL", "rating": 4.9, "description": "Incan citadel in Peru"},
            {"name": "Great Wall of China", "category": "LANDMARK", "rating": 4.8, "description": "Ancient fortification"},
            {"name": "Santorini", "category": "BEACH", "rating": 4.7, "description": "Beautiful Greek island"}
        ]
        return popular_places[:limit]
