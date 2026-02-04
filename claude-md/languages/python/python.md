# Python Language Rules

## Style

- Follow PEP 8 for code style.
- Use Google-style docstrings (Args, Returns, Raises sections).
- Use modern type hints: `str | None` not `Optional[str]`.
- End single-line comments with a full stop.

## Project Structure

- Use pyproject.toml for project configuration.
- Use Astral's uv for dependency management.
- Use src layout or app layout with clear module separation.
- Organize by layer: routes/api, services, repositories, models.

## Code Quality

- Prefer composition over inheritance.
- Use Pydantic or SQLModel for data structures.
- Use context managers for resource management.
- Use mixins for shared model fields (timestamps, primary keys).

## Error Handling

- Create custom exception hierarchies inheriting from a base ServiceError.
- Map exceptions to HTTP status codes at the route layer.
- Always chain exceptions with `raise ... from e`.
- Don't use bare `except:` clauses.

## Testing

- Use pytest as the test framework.
- Name test case variables `tc` not `tt`.
- Use `t.Parallel()` equivalent: run independent tests in parallel.
- Use fixtures with proper scope (module/function) and cleanup.
- Mirror app structure in tests directory.

## Type Checking

- Prefer Astral's ty for new projects (faster, integrated with uv/ruff ecosystem).
- Use mypy with strict mode if already configured in the project.
- Configure ruff with pyupgrade rules.

## Validation Commands

These commands are used by `/implement` and `/review` during validation. Override in `.claude/local/CLAUDE.md` if your project uses different scripts.

- **Lint:** `uv run pre-commit run --all-files`
