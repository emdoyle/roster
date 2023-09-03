import os
from pathlib import Path, PurePath

import git


class GitWorkspace:
    def __init__(self, root_dir: str):
        self.root_dir = PurePath(root_dir)

    def clone_repo(
        self,
        repo_url: str,
        overwrite_existing_dir: bool = False,
        username: str = "",
        password: str = "",
        token: str = "",
    ):
        repo_dir = Path(self.root_dir)

        if token:
            repo_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
        elif username and password:
            repo_url = repo_url.replace("https://", f"https://{username}:{password}@")

        # Check if directory already exists
        if repo_dir.is_dir():
            if overwrite_existing_dir:
                # Remove existing directory if overwrite is allowed
                for item in repo_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    else:
                        os.rmdir(item)
            else:
                raise FileExistsError(f"Directory {self.root_dir} already exists.")

        git.Repo.clone_from(repo_url, str(self.root_dir))

    def open(self, file: str, mode: str = "r", **kwargs):
        relative_file = PurePath(self.root_dir) / file
        return open(str(relative_file), mode=mode, **kwargs)

    def branch(self, branch: str):
        repo = git.Repo(str(self.root_dir))

        try:
            return repo.create_head(branch)
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to create branch {branch}.") from e

    def checkout_branch(self, branch: str):
        repo = git.Repo(str(self.root_dir))

        try:
            # Try to checkout the branch
            repo.git.checkout(branch)
        except git.exc.GitCommandError:
            self.branch(branch)
            repo.git.checkout(branch)

    def commit(self, commit_msg: str):
        repo = git.Repo(str(self.root_dir))

        # Stage all changes
        repo.git.add(A=True)

        # Commit
        repo.index.commit(commit_msg)

    def push(self, force: bool = False):
        repo = git.Repo(str(self.root_dir))

        push_option = "--force" if force else ""
        try:
            repo.git.push(push_option)
        except git.exc.GitCommandError as e:
            raise ValueError("Push operation failed.") from e
