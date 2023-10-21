from pydantic import BaseModel, Field


class CodeOutput(BaseModel):
    kind: str = Field(
        description="The kind of output (e.g. new_file, modified_file, etc.)"
    )
    filepath: str = Field(description="The filepath of the output")
    content: str = Field(default="", description="The content of the output")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "kind": "code",
                "filepath": "my-file.py",
                "content": "print('Hello World!')",
            }
        }
