"""Tests for worktree operations."""

import pytest
from pathlib import Path

from wt import git
from wt.config import Config
from wt.worktree import WorktreeManager


@pytest.fixture
def manager(git_repo, tmp_path, monkeypatch):
    """Create a worktree manager."""
    # Use temp directory for config
    monkeypatch.setenv("WT_CONFIG", str(tmp_path))

    config = Config(git_repo)
    # Use "main" instead of "origin/main" for tests without remotes
    config.set("default_base", "main")
    config.save()

    return WorktreeManager(config)


def test_list_worktrees(manager, git_repo):
    """Test listing worktrees."""
    worktrees = manager.list_worktrees()
    assert len(worktrees) == 1
    assert worktrees[0]["name"] == "main"
    assert worktrees[0]["path"] == git_repo


def test_get_default_worktree(manager):
    """Test getting default worktree."""
    default = manager.get_default_worktree()
    assert default is not None
    assert default["name"] == "main"


def test_create_worktree(manager, git_repo, temp_dir):
    """Test creating a worktree."""
    wt_path = manager.create_worktree("feat")

    assert wt_path.exists()
    assert wt_path.name == "test-repo-feat"
    assert git.branch_exists("feature/feat", git_repo)


def test_create_worktree_with_base(manager, git_repo):
    """Test creating worktree from specific base."""
    wt_path = manager.create_worktree("feat", base="main")
    assert wt_path.exists()


def test_create_worktree_detached(manager, git_repo):
    """Test creating detached worktree."""
    wt_path = manager.create_worktree("exp", detached=True)
    assert wt_path.exists()


def test_create_duplicate_worktree(manager):
    """Test creating worktree that already exists."""
    manager.create_worktree("feat")

    with pytest.raises(git.GitError, match="already exists"):
        manager.create_worktree("feat")


def test_find_worktree_by_name(manager, git_repo):
    """Test finding worktree by name."""
    # Find main worktree
    wt = manager.find_worktree_by_name("main")
    assert wt is not None
    assert wt["branch"] == "main"

    # Create and find new worktree
    manager.create_worktree("feat")
    wt = manager.find_worktree_by_name("feat")
    assert wt is not None
    assert wt["branch"] == "feature/feat"

    # Non-existent worktree
    wt = manager.find_worktree_by_name("nonexistent")
    assert wt is None


def test_delete_worktree(manager, git_repo, no_prompt):
    """Test deleting a worktree."""
    manager.create_worktree("feat")
    assert git.branch_exists("feature/feat", git_repo)

    deleted = manager.delete_worktree("feat", force=True)
    assert deleted is True
    assert not git.branch_exists("feature/feat", git_repo)


def test_delete_worktree_keep_branch(manager, git_repo, no_prompt):
    """Test deleting worktree but keeping branch."""
    manager.create_worktree("feat")

    deleted = manager.delete_worktree("feat", force=True, keep_branch=True)
    assert deleted is True
    assert git.branch_exists("feature/feat", git_repo)


def test_create_worktree_with_existing_branch(manager, git_repo, no_prompt):
    """Test creating worktree when branch exists but has no worktree."""
    # First create a worktree and delete it but keep the branch
    manager.create_worktree("feat")
    assert git.branch_exists("feature/feat", git_repo)

    # Delete worktree but keep the branch
    deleted = manager.delete_worktree("feat", force=True, keep_branch=True)
    assert deleted is True
    assert git.branch_exists("feature/feat", git_repo)

    # Now create worktree again - should use existing branch
    wt_path = manager.create_worktree("feat")
    assert wt_path.exists()
    assert git.branch_exists("feature/feat", git_repo)

    # Verify worktree is properly associated with the branch
    wt = manager.find_worktree_by_name("feat")
    assert wt is not None
    assert wt["branch"] == "feature/feat"


def test_delete_nonexistent_worktree(manager):
    """Test deleting non-existent worktree."""
    with pytest.raises(git.GitError, match="not found"):
        manager.delete_worktree("nonexistent", force=True)


def test_get_worktree_status_clean(manager, git_repo):
    """Test getting status of clean worktree."""
    worktrees = manager.list_worktrees()
    status = manager.get_worktree_status(worktrees[0])

    assert status["uncommitted_count"] == 0
    assert status["uncommitted_files"] == ""


def test_get_worktree_status_uncommitted(manager, git_repo):
    """Test getting status with uncommitted changes."""
    # Create uncommitted changes
    (git_repo / "test.txt").write_text("test")

    worktrees = manager.list_worktrees()
    status = manager.get_worktree_status(worktrees[0])

    assert status["uncommitted_count"] > 0
    assert "test.txt" in status["uncommitted_files"]


def test_clean_merged_worktrees_none(manager, no_prompt):
    """Test clean when no worktrees to clean."""
    removed = manager.clean_merged_worktrees(force=True)
    assert removed == []


def test_clean_merged_worktrees_dry_run(manager, git_repo, no_prompt):
    """Test clean in dry-run mode."""
    # Create worktree
    manager.create_worktree("feat")

    # Simulate merge by creating branch from main
    # (This test is limited without a remote)
    removed = manager.clean_merged_worktrees(dry_run=True, force=True)
    # Should not remove anything in dry run
    wt = manager.find_worktree_by_name("feat")
    assert wt is not None


def test_find_by_full_branch_name(manager):
    """Test finding worktree by full branch name."""
    manager.create_worktree("feat")

    # Find by short name
    wt1 = manager.find_worktree_by_name("feat")
    # Find by full branch name
    wt2 = manager.find_worktree_by_name("feature/feat")

    assert wt1 is not None
    assert wt2 is not None
    assert wt1["path"] == wt2["path"]


# --- checkout_branch tests ---


def test_derive_name_from_branch():
    """Test name derivation from branch names."""
    derive = WorktreeManager._derive_name_from_branch
    assert derive("fix/login-bug") == "login-bug"
    assert derive("feature/add-auth") == "add-auth"
    assert derive("origin/feature/pr-123") == "pr-123"
    assert derive("main") == "main"
    assert derive("claude/some-branch") == "some-branch"
    assert derive("origin/main") == "main"
    assert derive("a/b/c") == "c"


def test_checkout_branch(manager, git_repo):
    """Test checking out an existing branch into a new worktree."""
    git.create_branch("fix/login-bug", "HEAD", git_repo)

    wt_path = manager.checkout_branch("fix/login-bug")

    assert wt_path.exists()
    wt = manager.find_worktree_by_name("login-bug")
    assert wt is not None
    assert wt["branch"] == "fix/login-bug"


def test_checkout_branch_custom_name(manager, git_repo):
    """Test checkout with a custom worktree name."""
    git.create_branch("fix/login-bug", "HEAD", git_repo)

    wt_path = manager.checkout_branch("fix/login-bug", name="review-login")

    assert wt_path.exists()
    wt = manager.find_worktree_by_name("review-login")
    assert wt is not None
    assert wt["branch"] == "fix/login-bug"


def test_checkout_nonexistent_branch(manager, git_repo):
    """Test checkout of a branch that doesn't exist."""
    with pytest.raises(git.GitError, match="does not exist"):
        manager.checkout_branch("nonexistent/branch")


def test_checkout_branch_already_has_worktree(manager, git_repo):
    """Test checkout of a branch that already has a worktree."""
    git.create_branch("fix/login-bug", "HEAD", git_repo)
    manager.checkout_branch("fix/login-bug")

    with pytest.raises(git.GitError, match="already has a worktree"):
        manager.checkout_branch("fix/login-bug")


def test_checkout_branch_findable_by_derived_name(manager, git_repo):
    """Test that checked-out worktree is findable by its derived name."""
    git.create_branch("claude/my-feature", "HEAD", git_repo)
    manager.checkout_branch("claude/my-feature")

    # Should be findable by derived name
    wt = manager.find_worktree_by_name("my-feature")
    assert wt is not None

    # Should also be findable by full branch name
    wt2 = manager.find_worktree_by_name("claude/my-feature")
    assert wt2 is not None
    assert wt["path"] == wt2["path"]


def test_checkout_branch_appears_in_list(manager, git_repo):
    """Test that checked-out worktree appears in list with correct name."""
    git.create_branch("fix/login-bug", "HEAD", git_repo)
    manager.checkout_branch("fix/login-bug")

    worktrees = manager.list_worktrees()
    names = [wt["name"] for wt in worktrees]
    assert "login-bug" in names


def test_checkout_branch_name_conflict(manager, git_repo):
    """Test checkout when derived name conflicts with existing path."""
    git.create_branch("fix/bug", "HEAD", git_repo)
    git.create_branch("hotfix/bug", "HEAD", git_repo)

    manager.checkout_branch("fix/bug")

    with pytest.raises(git.GitError, match="already exists"):
        manager.checkout_branch("hotfix/bug")
