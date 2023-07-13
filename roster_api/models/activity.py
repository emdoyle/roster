from enum import Enum

from pydantic import BaseModel, Field


class ExecutionType(Enum):
    TASK = "task"


class ActivityType(Enum):
    THOUGHT = "thought"
    ACTION = "action"


class AgentContext(BaseModel):
    identity: str = Field(default="", description="The identity of the agent.")
    team: str = Field(default="", description="The team of the agent.")
    role: str = Field(default="", description="The role of the agent.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "identity": "agent-1",
                "team": "team-1",
                "role": "role-1",
            }
        }


class ActivityEvent(BaseModel):
    execution_id: str = Field(
        description="A unique identifier for the execution context of the event."
    )
    execution_type: ExecutionType = Field(
        description="The type of execution context for the event."
    )
    type: ActivityType = Field(description="The type of the event.")
    content: str = Field(description="The content of the event.")
    agent_context: AgentContext = Field(
        default_factory=AgentContext,
        description="(optional) The Roster context for the agent.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "execution_id": "execution-1",
                "execution_type": "task",
                "type": "thought",
                "content": "Hello, world!",
                "agent_context": AgentContext.Config.schema_extra["example"],
            }
        }
