import logging
import os
from pathlib import Path, PurePath

from roster_api import constants

import git

logger = logging.getLogger(constants.LOGGER_NAME)


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

    def force_to_latest_main(
        self, repo_url: str, username: str = "", password: str = "", token: str = ""
    ):
        repo_dir = Path(self.root_dir)

        if not repo_dir.exists():
            self.clone_repo(repo_url, username=username, password=password, token=token)
            logger.info("(git-workspace) Cloned new repository from %s.", repo_url)
            return

        # Verify current state of root_dir is OK if not empty
        try:
            repo = git.Repo(str(self.root_dir))
            if repo.remotes.origin.url != repo_url:
                raise ValueError("Directory contains a different git repository.")
        except git.exc.InvalidGitRepositoryError:
            raise ValueError("Directory exists but is not a valid git repository.")
        except git.exc.NoSuchPathError:
            self.clone_repo(repo_url, username=username, password=password, token=token)
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
            origin.fetch()
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

        push_option = "--force" if force else ""
        try:
            repo.git.push(push_option)
        except git.exc.GitCommandError as e:
            raise ValueError("Push operation failed.") from e
