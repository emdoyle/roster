import logging
import subprocess
from pathlib import Path, PurePath
from shutil import rmtree

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

    @classmethod
    def setup(
        cls,
        installation_id: int,
        repository_name: str,
        repo_url: str,
        username: str = "",
        password: str = "",
        token: str = "",
    ):
        workspace = cls.build(
            installation_id=installation_id,
            repository_name=repository_name,
            username=username,
            password=password,
            token=token,
        )
        workspace.setup_repo(repo_url)
        return workspace

    @property
    def auth_env(self) -> dict[str, str]:
        if self.token:
            return {
                "GIT_PASSWORD": self.token,
            }

        return {
            "GIT_PASSWORD": self.password,
        }

    def setup_credentials(self, repo_url: str):
        subprocess.run(
            [
                "git",
                "config",
                "--global",
                f"credential.{repo_url}.username",
                self.username or "x-access-token",
            ],
            cwd=str(self.root_dir),
        )
        subprocess.run(
            [
                "git",
                "config",
                "--global",
                "credential.helper",
                '!f() { echo "password=$GIT_PASSWORD"; }; f',
            ],
            cwd=str(self.root_dir),
        )

    def clone_repo(self, repo_url: str):
        git.Repo.clone_from(repo_url, str(self.root_dir), env=self.auth_env)

    def clean_repo_dir(self, repo_dir: Path, repo_url: str) -> bool:
        # If the directory doesn't exist, create it
        if not repo_dir.exists():
            repo_dir.mkdir(parents=True, exist_ok=True)
            return False

        # Verify current state of root_dir is OK if not empty
        try:
            repo = git.Repo(str(self.root_dir))
            if repo.remote().url != repo_url:
                raise ValueError("Directory contains a different git repository.")
            # If we reach this point, the repo is OK
            return True
        except (ValueError, git.exc.InvalidGitRepositoryError):
            # The directory exists, but it doesn't contain a git repo
            # So we clear the directory
            if repo_dir.is_dir():
                for item in repo_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    else:
                        rmtree(str(item))
                return False
            else:
                raise FileExistsError(
                    f"Directory {self.root_dir} already exists (as a file)."
                )
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")

    def setup_repo(self, repo_url: str):
        repo_dir = Path(self.root_dir)
        repo_exists = self.clean_repo_dir(repo_dir, repo_url)
        self.setup_credentials(repo_url)
        if not repo_exists:
            self.clone_repo(repo_url)

    def force_to_latest(self, branch: str = "main"):
        repo = git.Repo(str(self.root_dir))

        # Fetch latest HEAD for origin/main
        try:
            origin = repo.remote(name="origin")
            origin.fetch(env=self.auth_env)
        except git.exc.GitCommandError as e:
            raise ValueError("Failed to fetch latest changes from origin.") from e

        # Forcefully remove all dirty state
        repo.git.reset("--hard", "HEAD")
        repo.git.clean("-fd")
        logger.debug("(git-workspace) Removed all dirty git status from repo")

        # Switch to the branch and reset to latest origin
        try:
            repo.git.checkout(branch)
            repo.git.reset("--hard", f"origin/{branch}")
            logger.info("(git-workspace) Checked out latest origin/%s", branch)
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to update to latest origin/{branch}: {e}") from e

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

    def checkout_sha(self, sha: str):
        repo = git.Repo(str(self.root_dir))

        try:
            repo.git.checkout(sha)
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to checkout SHA {sha}.") from e

    def get_current_head_sha(self) -> str:
        repo = git.Repo(str(self.root_dir))
        return repo.head.commit.hexsha

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
