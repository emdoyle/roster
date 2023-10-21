from typing import Optional

from pydantic import BaseModel, Field


# TODO: expand to workflow messages, share model
class Sender(BaseModel):
    name: str = Field(description="The name of the Actor sending the message")
    namespace: str = Field(
        default="default", description="The namespace of the Actor sending the message"
    )

    class Config:
        validate_assignment = True
        schema_extra = {"example": {"name": "Sender", "namespace": "default"}}


class ToolMessage(BaseModel):
    id: str = Field(description="An identifier for this tool invocation.")
    tool: str = Field(description="The tool which this message refers to.")
    kind: str = Field(description="The kind of the message data.")
    data: dict = Field(default_factory=dict, description="The data of the message.")
    error: str = Field(
        default="", description="An error message returned by the tool, if any."
    )
    sender: Optional[Sender] = Field(
        default=None, description="The sender of the message."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tool": "ToolName",
                "kind": "tool_response",
                "data": {
                    "outputs": {"output1": "value1", "output2": "value2"},
                },
                "error": "",
                "sender": Sender.Config.schema_extra["example"],
            }
        }
