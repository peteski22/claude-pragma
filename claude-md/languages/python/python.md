# Python Language Rules

## Style

- Follow PEP 8 for code style.
- Follow PEP 257 for docstrings.
- Use type hints (PEP 484) for function signatures.

## Project Structure

- Use pyproject.toml for project configuration.
- Prefer uv or poetry for dependency management.

## Code Quality

- Prefer composition over inheritance.
- Use dataclasses or Pydantic for data structures.
- Use context managers for resource management.

## Error Handling

- Be specific with exception types.
- Don't use bare `except:` clauses.
- Use custom exceptions for domain-specific errors.

## Testing

- Use pytest as the test framework.
- Use fixtures for test setup.
- Aim for focused, isolated unit tests.

## Before Committing

- Run: `uv run pre-commit run --all-files`
