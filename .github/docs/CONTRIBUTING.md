# Contributing to Maily

Thank you for your interest in contributing to Maily! This document outlines the process for contributing to the project.

## Code of Conduct

All contributors are expected to adhere to our Code of Conduct. Please read it before contributing.

## Getting Started

1. **Fork the repository**: Create your own fork of the repository to work on.
2. **Set up your development environment**: Follow the instructions in the [Development Guide](../../docs/development/installation.md).
3. **Create a feature branch**: Always work on a feature branch, not directly on `main`.

## Development Workflow

1. **Create an issue**: Before starting work, create an issue describing the change you plan to make.
2. **Claim the issue**: Comment on the issue to let others know you're working on it.
3. **Create a feature branch**: Name your branch according to the convention `feature/issue-number-short-description`.
4. **Make your changes**: Implement your changes following our [Code Style Guide](../../CLAUDE.md).
5. **Write tests**: Add or update tests as necessary.
6. **Run tests locally**: Ensure all tests pass before submitting a pull request.
7. **Update documentation**: Update any relevant documentation.

## Pull Request Process

1. **Open a pull request**: When your changes are ready, open a pull request against the `main` branch.
2. **Fill out the PR template**: Complete all sections of the pull request template.
3. **Link the issue**: Link your pull request to the issue it resolves.
4. **Request reviews**: Request reviews from appropriate team members.
5. **Address feedback**: Make any requested changes promptly.
6. **Wait for CI**: Ensure all CI checks pass before merging.
7. **Merge**: Once approved and all checks pass, your PR will be merged.

## Commit Message Guidelines

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line
- Use conventional commits format: `type(scope): message`
  - Types: feat, fix, docs, style, refactor, test, chore
  - Example: `feat(auth): add OAuth2 authentication`

## Code Style

Follow the code style guidelines in the [CLAUDE.md](../../CLAUDE.md) file.

## Testing

All new features and bug fixes should include tests. Run tests locally before submitting a pull request:

```bash
# Run all tests
npm run test

# Run specific tests
npm test -- -t "test name"

# Run Python tests
pytest tests/unit/
```

## Documentation

Update documentation for any new features or changes to existing features. Documentation is as important as code!

## Questions?

If you have any questions about contributing, feel free to open an issue or reach out to the maintainers.