"""
Just Travel App - Agents Package
================================

This package contains all specialist agents for the travel planning system.

Agents:
    - ProfilerAgent: Captures user dietary/religious constraints and preferences
    - PathfinderAgent: Handles Cypher queries for Neo4j graph database
    - TrendSpotterAgent: Manages Apify social media scraping
    - ConciergeAgent: Filters food/hotels via Google Maps API
    - OptimizerAgent: Finalizes the dynamic daily planner
"""

from .profiler import ProfilerAgent
from .pathfinder import PathfinderAgent
from .trend_spotter import TrendSpotterAgent
from .concierge import ConciergeAgent
from .optimizer import OptimizerAgent
from .creative_director import CreativeDirectorAgent

__all__ = [
    "ProfilerAgent",
    "PathfinderAgent",
    "TrendSpotterAgent",
    "ConciergeAgent",
    "OptimizerAgent",
    "CreativeDirectorAgent"
]
