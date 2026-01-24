If this is a new tool, create a new folder under tools for your work with an appropriate name. Create a PRD.md and create stories and tasks under it as per the spec

Use uv for project management and pytest for testing

Pick up the most important task from PRD.md and start working on it

Create a notes.md file in that folder and append notes to it as you work, anything you tried or learned along the way that will be helpful for future agents.

If you need to create more tasks do it in inside PRD.md and under a story where task belong. If the story does not exist add the story as well

Add appropirate test for your work. try not to use mocks unless necessary

Mark a task done in PRD after the task is completed and tests are passing

Build/update README.md at the end if the story is finished

Your final commit should include just that folder and selected items from its contents:

- The notes.md, PRD.md and README.md files
- Any code you wrote along the way
- If you checked out and modified an existing repo, the output of "git diff" against that modified repo saved as a file - but not a copy of the full repo
- If appropriate, any binary files you created along the way provided they are less than 2MB in size
Do NOT include full copies of code that you fetched as part of your investigation. Your final commit should include only new files you created or diffs showing changes you made to existing code.

After everything is done update the root README.md with the tool's information

## Running Tests

**First time setup:**

```bash
cd tools/<tool-name>
uv pip install -e ".[dev]"  # Install with dev dependencies
```

**Run tests:**

```bash
uv run pytest tests/ -v              # Verbose output
uv run pytest tests/ -v --cov=<pkg>  # With coverage (if configured in pyproject.toml)
uv run pytest tests/test_foo.py::test_bar -v  # Run specific test
```

**Note:** Tests in this repo use real operations (not mocks) and temporary directories. If a test fails, check the error output for temp paths.

## Workflow Tips

1. **Always cd to tool directory first**: `cd tools/<tool-name>` before running commands
2. **Check pyproject.toml**: Review dependencies, scripts, and pytest config
3. **Read existing tests**: Understand test patterns and fixtures before adding new ones
4. **Use TodoWrite tool**: Track progress on multi-step tasks
5. **Document learnings**: Add to notes.md as you discover gotchas or solutions
6. **Test as you go**: Run tests after each significant change, not just at the end
7. **Git config in tests**: Disable GPG signing in test fixtures: `git config commit.gpgsign false`
