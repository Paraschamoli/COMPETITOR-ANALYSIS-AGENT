#!/usr/bin/env python3
"""
Model configuration for the Competitor Analysis Agent
"""

from agno.models.openrouter import OpenRouter
from .config import COORDINATOR_MODEL, AGENT_MODEL


def coordinator_model():
    """Get the coordinator model instance"""
    return OpenRouter(id=COORDINATOR_MODEL)


def agent_model():
    """Get the agent model instance"""
    return OpenRouter(id=AGENT_MODEL)
