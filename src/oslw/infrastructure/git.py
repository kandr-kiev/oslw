"""GitManager - git operations for wiki repository management.

Provides:
- Status checking
- Commit operations
- Branch management
- Push/pull operations
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class GitStatus:
    """Git repository status.

    Attributes:
        branch: Current branch name
        has_changes: Whether there are uncommitted changes
        staged_files: List of staged files
        unstaged_files: List of unstaged files
        ahead: Commits ahead of remote
        behind: Commits behind remote
        last_commit: Last commit hash and message
    """

    branch: str = ""
    has_changes: bool = False
    staged_files: list[str] = field(default_factory=list)
    unstaged_files: list[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0
    last_commit: Optional[str] = None


class GitManager:
    """Git repository manager for wiki operations.

    Provides:
    - Status checking
    - Commit operations
    - Branch management
    - Push/pull operations

    Usage:
        git = GitManager(repo_path="/workspace/llm-wiki")
        status = git.status()
        if status.has_changes:
            git.commit("Update wiki pages")
            git.push()
    """

    def __init__(self, repo_path: str | Path):
        """Initialize GitManager.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path)

    def status(self) -> GitStatus:
        """Get repository status.

        Returns:
            GitStatus with current state
        """
        status = GitStatus()

        try:
            # Get current branch
            result = self._run("git", "branch", "--show-current")
            if result.success:
                status.branch = result.output.strip()

            # Get staged files
            result = self._run("git", "diff", "--staged", "--name-only")
            if result.success:
                status.staged_files = [f for f in result.output.strip().split("\n") if f]

            # Get unstaged files
            result = self._run("git", "diff", "--name-only")
            if result.success:
                status.unstaged_files = [f for f in result.output.strip().split("\n") if f]

            status.has_changes = bool(status.staged_files or status.unstaged_files)

            # Get ahead/behind
            result = self._run("git", "rev-list", "--left-right", "--count", "HEAD...origin/main")
            if result.success:
                parts = result.output.strip().split("\n")
                if len(parts) == 2:
                    status.ahead = int(parts[0].strip())
                    status.behind = int(parts[1].strip())

            # Get last commit
            result = self._run("git", "log", "-1", "--format=%H %s")
            if result.success:
                parts = result.output.strip().split(" ", 1)
                if len(parts) == 2:
                    status.last_commit = f"{parts[0][:8]} - {parts[1]}"

        except Exception as e:
            status.branch = f"error: {e}"

        return status

    def add(self, paths: list[str]) -> bool:
        """Stage files for commit.

        Args:
            paths: List of file paths to stage

        Returns:
            True if successful
        """
        for path in paths:
            self._run("git", "add", path)
        return True

    def commit(self, message: str, author: Optional[str] = None) -> bool:
        """Commit staged changes.

        Args:
            message: Commit message
            author: Optional author override

        Returns:
            True if successful
        """
        cmd = ["git", "commit", "-m", message]
        if author:
            cmd += ["--author", author]
        result = self._run(*cmd)
        return result.success

    def push(self, branch: Optional[str] = None, force: bool = False) -> bool:
        """Push to remote.

        Args:
            branch: Branch to push (defaults to current)
            force: Force push

        Returns:
            True if successful
        """
        cmd = ["git", "push"]
        if force:
            cmd.append("--force")
        if branch:
            cmd.extend([f"origin", branch])
        else:
            cmd.append("origin")

        result = self._run(*cmd)
        return result.success

    def pull(self, branch: Optional[str] = None) -> bool:
        """Pull from remote.

        Args:
            branch: Branch to pull (defaults to current)

        Returns:
            True if successful
        """
        cmd = ["git", "pull"]
        if branch:
            cmd.extend([f"origin", branch])
        else:
            cmd.append("origin")

        result = self._run(*cmd)
        return result.success

    def create_branch(self, name: str) -> bool:
        """Create a new branch.

        Args:
            name: Branch name

        Returns:
            True if successful
        """
        result = self._run("git", "checkout", "-b", name)
        return result.success

    def checkout(self, branch: str) -> bool:
        """Switch to a branch.

        Args:
            branch: Branch name

        Returns:
            True if successful
        """
        result = self._run("git", "checkout", branch)
        return result.success

    def _run(self, *args) -> "subprocess.CompletedProcess":
        """Run a git command.

        Args:
            *args: Command arguments

        Returns:
            CompletedProcess with result
        """
        try:
            result = subprocess.run(
                list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                list(args),
                returncode=-1,
                stdout="",
                stderr="Command timed out",
            )

    @property
    def is_repo(self) -> bool:
        """Check if path is a git repository.

        Returns:
            True if .git directory exists
        """
        return (self.repo_path / ".git").exists()
