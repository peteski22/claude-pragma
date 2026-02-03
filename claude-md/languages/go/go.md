# Go Language Rules

## Core Philosophy

- Follow the Go Proverbs (https://go-proverbs.github.io/).
- Reference specific proverbs when making design decisions.
- Prefer functional and declarative approaches over imperative and mutating approaches.

## Key Proverbs to Enforce

- Don't communicate by sharing memory, share memory by communicating.
- Concurrency is not parallelism.
- The bigger the interface, the weaker the abstraction.
- Make the zero value useful.
- A little copying is better than a little dependency.
- Clear is better than clever.
- Errors are values.
- Don't just check errors, handle them gracefully.

## Code Organization

- Organize files in order: package → imports → constants → variables → interfaces → types → functions/methods.
- Within each section, top-level declarations should be in lexicographical order.
- Struct fields should be grouped logically (related fields together).
- Always start with unexported types, functions, fields. Only export when necessary.
- Unexported structs should have unexported fields (unless required by encoding/json or similar).

## Function Design

- Functions should have 4 parameters maximum. Use options pattern or config struct for more.
- Never group similar types in signatures: use `(urlStr string, registryName string)` not `(urlStr, registryName string)`.
- Use pointer types (*string, *bool) for optional configuration fields.
- Use value types for required fields.

## Naming

- No GetX() accessors; use X() for getters. SetX() is acceptable for setters.
- Function names should not repeat context from package name or receiver type.
- Avoid verbose prefixes when the operation is obvious from context. `New` is idiomatic for constructors.
- Prefer concise names: `WorktreePath` over `GenerateWorktreePathWithTemplate`.

## Error Handling

- Use '%s' (not %q) in error format strings.
- Reference items by name/identifier in errors, not array indices.
- Use errors.Join for collecting multiple validation errors.

## Interface Design

- Prefer type assertion over expanding interfaces.
- Keep interfaces small and focused.

## Testing

- Name test case variable 'tc' not 'tt'.
- Use t.Parallel(), t.Helper(), t.TempDir() where possible.
- Use require from testify (not assert).
- Use testdata/ directories for static test fixtures.

## Before Committing

- Run: `golangci-lint run --fix -v`
