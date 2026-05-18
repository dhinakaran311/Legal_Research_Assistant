"""
LegalResearchCrew
CrewAI crew that wraps the existing 5 agents as structured Agent+Task objects.
Used as an alternative execution path to LangGraph for complex multi-step queries.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from crewai import Agent, Crew, Process, Task
    from langchain_groq import ChatGroq
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("crewai/langchain-groq not installed — LegalResearchCrew unavailable")


class LegalResearchCrew:
    """
    CrewAI-based legal research crew.
    Agents use Groq LLM via langchain-groq integration.
    Falls back gracefully if crewai is not installed.
    """

    def __init__(
        self,
        chroma_client=None,
        neo4j_client=None,
        groq_api_key: Optional[str] = None,
        model: str = "groq/llama-3.3-70b-versatile",
        fast_model: str = "groq/llama-3.1-8b-instant",
    ):
        self.chroma = chroma_client
        self.neo4j = neo4j_client
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model
        self.fast_model = fast_model
        self._crew: Optional[Any] = None

        if CREWAI_AVAILABLE and self.groq_api_key:
            self._setup_crew()
        else:
            logger.warning(
                "LegalResearchCrew: crewai unavailable or GROQ_API_KEY missing — "
                "crew disabled, falling back to ConversationGraph"
            )

    @property
    def available(self) -> bool:
        return CREWAI_AVAILABLE and bool(self.groq_api_key)

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _setup_crew(self) -> None:
        from crew.tools import (
            ChromaSearchTool, Neo4jGraphTool,
            IndianKanoonTool, IndiaCodeTool,
        )

        # Tools
        chroma_tool   = ChromaSearchTool(chroma_client=self.chroma)
        neo4j_tool    = Neo4jGraphTool(neo4j_client=self.neo4j)
        kanoon_tool   = IndianKanoonTool()
        indiacode_tool = IndiaCodeTool()

        # LLM configs
        llm_main = self.model
        llm_fast = self.fast_model

        # ── Agents ────────────────────────────────────────────────────────────

        planner = Agent(
            role="Legal Query Planner",
            goal=(
                "Analyse the user's legal query, detect intent (factual/procedural/"
                "comparative/case_law/recent/exploratory), extract relevant Indian acts "
                "and section numbers, and decide the research strategy."
            ),
            backstory=(
                "You are a senior Indian legal analyst with 20 years of experience. "
                "You specialise in understanding complex legal queries and breaking them "
                "into structured research tasks."
            ),
            llm=llm_fast,
            verbose=False,
            allow_delegation=False,
        )

        researcher = Agent(
            role="Legal Researcher",
            goal=(
                "Search the local legal database (ChromaDB) and knowledge graph (Neo4j) "
                "to find the most relevant Indian legal provisions, sections, and case references."
            ),
            backstory=(
                "You are an expert legal researcher with deep knowledge of Indian statutes. "
                "You excel at finding precise legal provisions from large document collections."
            ),
            tools=[chroma_tool, neo4j_tool],
            llm=llm_main,
            verbose=False,
            allow_delegation=False,
        )

        web_researcher = Agent(
            role="Web Legal Researcher",
            goal=(
                "Search IndianKanoon and IndiaCode for recent judgments, case law, "
                "and official act text when local database results are insufficient."
            ),
            backstory=(
                "You are a legal researcher specialising in online legal databases. "
                "You know how to find authoritative sources from IndianKanoon and IndiaCode."
            ),
            tools=[kanoon_tool, indiacode_tool],
            llm=llm_main,
            verbose=False,
            allow_delegation=False,
        )

        analyst = Agent(
            role="Legal Conflict Analyst",
            goal=(
                "Identify contradictions, overlaps, and ambiguities between different "
                "Indian acts and provisions found in the research results."
            ),
            backstory=(
                "You are a legal analyst specialising in conflict of laws. "
                "You identify when multiple acts address the same issue differently."
            ),
            llm=llm_fast,
            verbose=False,
            allow_delegation=False,
        )

        synthesizer = Agent(
            role="Legal Answer Synthesizer",
            goal=(
                "Synthesize all research findings into a clear, accurate, well-cited "
                "answer to the user's legal question. Always cite act names and section numbers."
            ),
            backstory=(
                "You are a senior Indian lawyer who writes clear, authoritative legal answers. "
                "You always cite sources and acknowledge when laws conflict or are ambiguous."
            ),
            llm=llm_main,
            verbose=False,
            allow_delegation=False,
        )

        self._agents = {
            "planner": planner,
            "researcher": researcher,
            "web_researcher": web_researcher,
            "analyst": analyst,
            "synthesizer": synthesizer,
        }

        logger.info("LegalResearchCrew: agents configured with Groq (%s)", self.model)

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, query: str, intent: str = "general", needs_web: bool = False,
            needs_conflict_check: bool = False) -> Dict[str, Any]:
        """
        Run the crew for a single query.
        Returns dict with answer and metadata.
        """
        if not self.available:
            return {"error": "LegalResearchCrew not available", "answer": ""}

        try:
            tasks = self._build_tasks(query, intent, needs_web, needs_conflict_check)
            crew = Crew(
                agents=list(self._agents.values()),
                tasks=tasks,
                process=Process.sequential,
                verbose=False,
            )
            result = crew.kickoff()
            return {
                "answer": str(result),
                "used_crew": True,
                "model": self.model,
            }
        except Exception as e:
            logger.error("LegalResearchCrew.run failed: %s", e)
            return {"error": str(e), "answer": "", "used_crew": False}

    # ── Task builder ──────────────────────────────────────────────────────────

    def _build_tasks(
        self,
        query: str,
        intent: str,
        needs_web: bool,
        needs_conflict_check: bool,
    ) -> list:
        agents = self._agents

        plan_task = Task(
            description=(
                f"Analyse this Indian legal query and produce a research plan:\n\n"
                f"Query: {query}\n\n"
                "Output: intent type, relevant acts, section numbers, "
                "whether web search is needed, whether conflict check is needed."
            ),
            expected_output="Structured research plan with intent, acts, sections, and routing flags.",
            agent=agents["planner"],
        )

        research_task = Task(
            description=(
                f"Search the local legal database for: {query}\n\n"
                "Use chroma_legal_search and neo4j_graph_search tools. "
                "Return the top relevant provisions with act names, section numbers, and content."
            ),
            expected_output="List of relevant legal provisions with sources and relevance scores.",
            agent=agents["researcher"],
            context=[plan_task],
        )

        tasks = [plan_task, research_task]

        if needs_web:
            web_task = Task(
                description=(
                    f"Search IndianKanoon and IndiaCode for: {query}\n\n"
                    "Focus on recent judgments, case law, and official act text. "
                    "Return titles, URLs, and relevant content excerpts."
                ),
                expected_output="List of web results with titles, URLs, and content.",
                agent=agents["web_researcher"],
                context=[plan_task],
            )
            tasks.append(web_task)

        if needs_conflict_check:
            conflict_task = Task(
                description=(
                    f"Analyse the research results for conflicts related to: {query}\n\n"
                    "Identify contradictions, overlaps, or ambiguities between different acts. "
                    "If no conflicts, state 'No conflicts detected'."
                ),
                expected_output="Conflict analysis report or 'No conflicts detected'.",
                agent=agents["analyst"],
                context=tasks[1:],  # context from research tasks
            )
            tasks.append(conflict_task)

        synthesis_task = Task(
            description=(
                f"Write a comprehensive answer to this legal question: {query}\n\n"
                "Use ALL research findings above. "
                "Cite specific act names and section numbers. "
                "If conflicts were found, mention them and suggest resolution. "
                f"Tailor the answer style for intent: {intent}."
            ),
            expected_output=(
                "A clear, well-cited legal answer with act/section references, "
                "source citations, and any relevant conflict notes."
            ),
            agent=agents["synthesizer"],
            context=tasks,
        )
        tasks.append(synthesis_task)

        return tasks
