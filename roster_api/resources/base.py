import yaml
from pydantic import BaseModel


class YamlResource(BaseModel):
    @classmethod
    def from_yaml(cls, file_path):
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        # Is there something else I can do to error handle here?
        return cls.parse_obj(data)
