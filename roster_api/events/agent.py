from pydantic import BaseModel, Field
from roster_api.models.agent import AgentSpec


class PutAgentSpecEvent(BaseModel):
    namespace: str = Field(description="The namespace of the agent.")
    name: str = Field(description="The name of the agent.")
    spec: AgentSpec = Field(description="The specification of the agent.")

    class Config:
        validate_assignment = True


class DeleteAgentSpecEvent(BaseModel):
    namespace: str = Field(description="The namespace of the agent.")
    name: str = Field(description="The name of the agent.")

    class Config:
        validate_assignment = True
