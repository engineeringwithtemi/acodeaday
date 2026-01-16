# Contributing

Thank you for your interest in contributing to acodeaday! This guide will help you get started.

## Ways to Contribute

### Report Bugs

Found a bug? Please [open an issue](https://github.com/engineeringwithtemi/acodeaday/issues/new) with:

- A clear, descriptive title
- Steps to reproduce the bug
- Expected vs actual behavior
- Screenshots (if applicable)
- Your environment (browser, OS, etc.)

### Suggest Features

Have an idea? [Open a feature request](https://github.com/engineeringwithtemi/acodeaday/issues/new) with:

- Description of the feature
- Why it would be useful
- Any implementation ideas you have

### Submit Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `uv run pytest` (backend) / `npm test` (frontend)
5. Commit with clear messages
6. Push and open a Pull Request

### Add Problems

See [Adding Problems](/guide/adding-problems) to contribute new coding challenges.

### Improve Documentation

Documentation improvements are always welcome! Edit files in the `docs/` directory.

## Development Setup

See [Quick Start](/guide/quick-start) for setting up your development environment.

### Running Tests

**Backend:**
```bash
cd backend
uv run pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript/React**: Follow ESLint configuration
- **Commits**: Use clear, descriptive commit messages

## Pull Request Guidelines

1. **One feature per PR** - Keep PRs focused
2. **Include tests** - Add tests for new functionality
3. **Update docs** - Update documentation if needed
4. **Describe changes** - Write a clear PR description

## Code of Conduct

Be respectful and inclusive. We're all here to learn and build together.

## Questions?

- [Open an issue](https://github.com/engineeringwithtemi/acodeaday/issues)
- Check existing [discussions](https://github.com/engineeringwithtemi/acodeaday/discussions)

## License

By contributing, you agree that your contributions will be licensed under the project's license.
