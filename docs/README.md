# Maily Documentation

This directory contains comprehensive documentation for the Maily platform.

## Documentation Structure

- `api/` - API documentation and OpenAPI specifications
- `development/` - Development guides and instructions
- `internal/` - Internal architecture and design documentation
- `adr/` - Architecture Decision Records
- `migrations/` - Database migration guides and procedures

## Documentation Standards

All documentation should follow these standards:
- Use Markdown format for all documentation
- Include clear headers and navigation
- Keep documentation up-to-date with code changes
- Include examples and code snippets where appropriate
- Link to related documentation when relevant

## Building the Documentation

The documentation site is built using MkDocs:

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Build the documentation
mkdocs build

# Serve the documentation locally
mkdocs serve
```

## Contributing to Documentation

When adding or updating documentation:
1. Follow the existing structure and format
2. Include metadata (date, author, version) where appropriate
3. Review documentation for clarity and accuracy
4. Update related documentation if necessary
5. Add documentation entries to the navigation in `mkdocs.yml`