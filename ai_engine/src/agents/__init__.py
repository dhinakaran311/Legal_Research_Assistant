"""
Indian Legal Research Assistant — Agent Package
"""

from agents.planner_agent          import PlannerAgent, Plan, SubTask, TaskType
from agents.local_research_agent   import LocalResearchAgent, LocalResearchBundle
from agents.web_research_agent     import WebResearchAgent, WebResearchBundle
from agents.conflict_checker_agent import ConflictCheckerAgent, ConflictReport
from agents.synthesis_agent        import SynthesisAgent, SynthesisOutput
from agents.agentic_pipeline       import AgenticPipeline, PipelineResult

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
