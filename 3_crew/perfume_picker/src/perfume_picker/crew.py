from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field, HttpUrl
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from typing import Optional, List

class TrendingPerfume(BaseModel):
    """ A trending perfume """
    name: str = Field(description="Perfume name")
    brand: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    description: Optional[str] = None
    image: Optional[HttpUrl] = None
    link: Optional[HttpUrl] = None

class TrendingPerfumeList(BaseModel):
    """ A list of trending perfumes that match the user's criteria"""
    perfumes: List[TrendingPerfume] = Field(description="List of trending perfumes")

class TrendingPerfumeResearch(BaseModel):
    """ Detailed research on a perfume """
    name: str = Field(description="Perfume name")
    brand: Optional[str] = None
    description: Optional[str] = None
    similar_characteristics: List[str] = Field(description="Similar characteristics of what the user wants in a perfume")
    trendiness: int = Field(description="Trendiness of the perfume") 


class TrendingPerfumeResearchList(BaseModel):
    """ A list of detailed research on all the perfumes """
    research_list: List[TrendingPerfumeResearch] = Field(description="Comprehensive research on all trending perfumes")


class DerivedPreferences(BaseModel):
    reference_perfumes: List[str] = Field(default_factory=list)
    target_accords: List[str] = Field(default_factory=list)
    target_notes: List[str] = Field(default_factory=list)
    avoid_notes: List[str] = Field(default_factory=list)
    season: Optional[str] = None
    occasion: Optional[str] = None
    intensity: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    rationale: str


@CrewBase
class PerfumePicker():
    "PerfumePicker crew"

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], tools=[SerperDevTool()])
    
    @agent
    def analyst(self) -> Agent:
        return Agent(config=self.agents_config['analyst'])

    @agent
    def perfume_picker(self) -> Agent:
        return Agent(config=self.agents_config['perfume_picker'])
    
    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'], 
        output_pydantic=TrendingPerfumeList,
        )
    
    @task
    def analyst_task(self) -> Task:
        return Task(config=self.tasks_config['analyst_task'], 
        output_pydantic=TrendingPerfumeResearchList,
        )
    
    @task
    def derive_preferences_task(self) -> Task:
        return Task(
        config=self.tasks_config["derive_preferences_task"],
        output_pydantic=DerivedPreferences
    )
    
    @task
    def perfume_picker_task(self) -> Task:
        return Task(config=self.tasks_config['perfume_picker_task'],
        output_pydantic=TrendingPerfume,
        )
    
    
    @crew
    def crew(self) -> Crew:
        "Creates the Perfume Picker Crew"
        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True,
            long_term_memory=LongTermMemory(
                storage=LTMSQLiteStorage(
                    db_path="./memory/long_term_memory_storage.db"
                )
            ),
            short_term_memory=ShortTermMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "openai",
                        "config": {
                            "model": "text-embedding-3-small"
                        }
                    },
                    type="short_term",
                    path="./memory/"
                )
            ),
            entity_memory=EntityMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "openai",
                        "config": {
                            "model": "text-embedding-3-small"
                        }
                    },
                    type="short_term",
                    path="./memory/"
                )
            ),
        )