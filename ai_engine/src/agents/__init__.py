"""
Indian Legal Research Assistant — Agent Package
"""

from agents.planner_agent import PlannerAgent
from agents.local_research_agent import LocalResearchAgent
from agents.web_research_agent import WebResearchAgent
from agents.conflict_checker_agent import ConflictCheckerAgent
from agents.synthesis_agent import SynthesisAgent
from agents.agentic_pipeline import AgenticPipeline

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
