import json
import logging
import os
import subprocess
from collections import defaultdict
from typing import Optional

from pydantic import BaseModel, Field
from roster_api import constants

logger = logging.getLogger(constants.LOGGER_NAME)


class Tag(BaseModel):
    kind: str
    name: str
    signature: Optional[str] = None
    scope: Optional[str] = None
    scope_kind: Optional[str] = None
    decorators: Optional[str] = None
    children: list["Tag"] = Field(default_factory=list)


class CtagFileTreeGenerator:
    # TODO: wildcard/pattern support
    DEFAULT_EXCLUDED_TAGS = [
        Tag(kind="class", name="Config"),
        Tag(kind="member", name="__init__"),
        Tag(kind="member", name="__str__"),
        Tag(kind="variable", name="logger"),
    ]
    KIND_DISPLAY_NAMES = {
        "class": "class",
        "function": "def",
        "member": "member",
        "variable": "var",
    }

    def __init__(self, repo_path: str, excluded_tags: Optional[list[Tag]] = None):
        self.repo_path = os.path.abspath(repo_path)
        self.excluded_tags = {
            f"{tag.kind} {tag.name}"
            for tag in excluded_tags or self.DEFAULT_EXCLUDED_TAGS
        }

    @staticmethod
    def generate_ctags(repo_path: str) -> str:
        try:
            result = subprocess.run(
                [
                    "ctags",
                    "-R",
                    "--fields=+KSns-P",
                    "--fields-python=+{decorators}",
                    "--kinds-python=+cfm",
                    "--output-format=json",
                ],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except FileNotFoundError:
            raise FileNotFoundError(
                "Error: ctags not found. Make sure universal-ctags is installed."
            )

    def parse_ctags(self, tags_data: str) -> dict[str, list[Tag]]:
        file_tree = defaultdict(list)
        tag_lookup = {}
        unresolved_tags = []

        try:
            lines = tags_data.splitlines()
            for line in lines:
                line_data = json.loads(line)
                name = line_data["name"]
                kind = line_data["kind"]

                if f"{kind} {name}" in self.excluded_tags:
                    logger.debug("(ctag-tree) Skipping excluded tag %s %s", kind, name)
                    continue

                file_path = line_data["path"]
                signature = line_data.get("signature")
                scope = line_data.get("scope")
                scope_kind = line_data.get("scopeKind")
                decorators = line_data.get("decorators")

                if not file_path.startswith(self.repo_path):
                    file_path = os.path.join(self.repo_path, file_path)
                relative_path = os.path.relpath(file_path, self.repo_path)

                tag = Tag(
                    kind=kind,
                    name=name,
                    signature=signature,
                    scope=scope,
                    scope_kind=scope_kind,
                    decorators=decorators,
                )

                # Add to parent's children list if a scope exists.
                if scope and scope_kind:
                    parent_local_name = scope.split(".")[-1]
                    parent_key = f"{scope_kind}-{scope}-{relative_path}"
                    parent_tag = tag_lookup.get(parent_key)
                    if parent_tag:
                        # We have already parsed the parent tag, so we can add this tag to its children.
                        parent_tag.children.append(tag)
                    elif f"{scope_kind} {parent_local_name}" in self.excluded_tags:
                        # The parent of this tag is excluded, we should move on.
                        continue
                    else:
                        # We haven't parsed the parent tag yet, so we need to add this tag to the unresolved list.
                        unresolved_tags.append((tag, parent_key))
                else:
                    # This is a top-level tag for the file.
                    file_tree[relative_path].append(tag)

                # Add this tag to the lookup dictionary.
                full_name = f"{scope}.{name}" if scope else name
                tag_key = f"{kind}-{full_name}-{relative_path}"
                tag_lookup[tag_key] = tag

            for tag, parent_key in unresolved_tags:
                parent_tag = tag_lookup.get(parent_key)
                if parent_tag:
                    parent_tag.children.append(tag)
                else:
                    logger.warning(
                        "(ctag-tree) Unable to find parent tag (%s) for %s %s",
                        parent_key,
                        tag.kind,
                        tag.name,
                    )
                    raise Exception(
                        f"Error: Unable to find parent tag for {tag.kind} {tag.name}"
                    )

            return file_tree
        except Exception as e:
            raise Exception(f"Error: Something went wrong in ctags parsing. {str(e)}")

    def tag_lines(self, tags: list[Tag], indent_level: int = 1) -> list[str]:
        indent = "    " * indent_level
        lines = []
        for tag in tags:
            decorator_suffix = (
                f" (decorators: {tag.decorators})" if tag.decorators else ""
            )
            if tag.kind == "function":
                signature_suffix = tag.signature or "()"
            else:
                signature_suffix = ""
            lines.append(
                f"{indent}- {tag.kind} {tag.name}{signature_suffix}{decorator_suffix}"
            )
            lines.extend(self.tag_lines(tag.children, indent_level + 1))
        return lines

    def generate_tree(self) -> list[str]:
        ctags_data = self.generate_ctags(self.repo_path)
        tree = self.parse_ctags(ctags_data)
        lines = []
        for file, tags in sorted(tree.items()):
            lines.append(f"{file}:")
            lines.extend(self.tag_lines(tags))
        return lines
