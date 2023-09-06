import logging
import os
from pathlib import Path, PurePath

from roster_api import constants, settings

import git

logger = logging.getLogger(constants.LOGGER_NAME)


class GitWorkspace:
    def __init__(
        self,
        root_dir: str,
        username: str = "",
        password: str = "",
        token: str = "",
    ):
        self.root_dir = PurePath(root_dir)
        self.username = username
        self.password = password
        self.token = token

    @classmethod
    def build(
        cls,
        installation_id: int,
        repository_name: str,
        username: str = "",
        password: str = "",
        token: str = "",
    ) -> "GitWorkspace":
        return cls(
            root_dir=f"{settings.WORKSPACE_DIR}/{installation_id}/{repository_name}",
            username=username,
            password=password,
            token=token,
        )

    @property
    def auth_env(self) -> dict[str, str]:
        if self.token:
            return {
                "GIT_ASKPASS": "echo",
                "GIT_USERNAME": "x-access-token",
                "GIT_PASSWORD": self.token,
            }

        return {
            "GIT_ASKPASS": "echo",
            "GIT_USERNAME": self.username,
            "GIT_PASSWORD": self.password,
        }

    def clone_repo(
        self,
        repo_url: str,
        overwrite_existing_dir: bool = False,
    ):
        repo_dir = Path(self.root_dir)

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

        git.Repo.clone_from(repo_url, str(self.root_dir), env=self.auth_env)

    def force_to_latest_main(self, repo_url: str):
        repo_dir = Path(self.root_dir)

        if not repo_dir.exists():
            self.clone_repo(repo_url)
            logger.info("(git-workspace) Cloned new repository from %s.", repo_url)
            return

        # Verify current state of root_dir is OK if not empty
        try:
            repo = git.Repo(str(self.root_dir))
            # disabling for now since remotes contain the access token
            # and fail checks against the unadorned https clone url
            # if repo.remotes.origin.url != repo_url:
            #     raise ValueError("Directory contains a different git repository.")
        except git.exc.InvalidGitRepositoryError:
            raise ValueError("Directory exists but is not a valid git repository.")
        except git.exc.NoSuchPathError:
            self.clone_repo(repo_url)
            logger.info(
                "(git-workspace) Directory was empty, cloned new repository from %s.",
                repo_url,
            )
            return
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")

        # Fetch latest HEAD for origin/main
        try:
            origin = repo.remote(name="origin")
            origin.fetch(env=self.auth_env)
        except git.exc.GitCommandError as e:
            raise ValueError("Failed to fetch latest changes from origin.") from e

        # Forcefully remove all dirty state
        repo.git.reset("--hard", "HEAD")
        repo.git.clean("-fd")
        logger.debug(
            "(git-workspace) Removed all dirty git status from repo %s", repo_url
        )

        # Switch to the main branch and reset to latest origin/main
        try:
            repo.git.checkout("main")
            repo.git.reset("--hard", "origin/main")
            logger.info(
                "(git-workspace) Checked out latest origin/main for %s", repo_url
            )
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to update to latest origin/main: {e}") from e

    def open(self, file: str, mode: str = "r", **kwargs):
        relative_file = PurePath(self.root_dir) / file
        return open(str(relative_file), mode=mode, **kwargs)

    def create_branch(self, branch: str):
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
            self.create_branch(branch)
            repo.git.checkout(branch)

        repo.git.reset("--hard", "HEAD")
        repo.git.clean("-fd")

    def commit(self, commit_msg: str):
        repo = git.Repo(str(self.root_dir))

        # Stage all changes
        repo.git.add(A=True)

        # Commit
        repo.index.commit(commit_msg)

    def push(self, force: bool = False):
        repo = git.Repo(str(self.root_dir))
        if "origin" in [remote.name for remote in repo.remotes]:
            origin = repo.remotes.origin
        else:
            raise ValueError("No remote named 'origin' found.")

        # Get the current branch name
        current_branch = repo.active_branch.name
        logger.debug("(git-workspace) About to push from branch: %s", current_branch)

        # Check if current branch is tracking an upstream branch
        if repo.active_branch.tracking_branch() is None:
            try:
                # Set upstream branch and push
                repo.git.push(
                    "--set-upstream", "origin", current_branch, env=self.auth_env
                )
            except git.GitCommandError as e:
                raise ValueError("Push operation failed while setting upstream.") from e
        else:
            try:
                push_option = "--force" if force else ""
                # Perform the push
                origin.push(push_option, env=self.auth_env)
            except git.GitCommandError as e:
                raise ValueError("Push operation failed.") from e
