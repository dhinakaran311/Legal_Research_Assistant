"""
Indian Legal Research Assistant — Agent Package
"""

from src.agents.planner_agent import PlannerAgent
from src.agents.local_research_agent import LocalResearchAgent
from src.agents.web_research_agent import WebResearchAgent
from src.agents.conflict_checker_agent import ConflictCheckerAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.agents.agentic_pipeline import AgenticPipeline

__all__ = [
    # Agents
    "PlannerAgent",
    "LocalResearchAgent",
    "WebResearchAgent",
    "ConflictCheckerAgent",
    "SynthesisAgent",
    # Pipeline
    "AgenticPipeline",
    # Data classes
    "Plan", "SubTask", "TaskType",
    "LocalResearchBundle",
    "WebResearchBundle",
    "ConflictReport",
    "SynthesisOutput",
    "PipelineResult",
]
