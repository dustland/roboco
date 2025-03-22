# Contributing to RoboCo

Thank you for your interest in contributing to RoboCo! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with the following information:

1. A clear, descriptive title
2. A detailed description of the issue
3. Steps to reproduce the problem
4. Expected behavior
5. Actual behavior
6. Screenshots (if applicable)
7. Environment information (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:

1. A clear, descriptive title
2. A detailed description of the proposed enhancement
3. The rationale for the enhancement
4. Any relevant examples or mockups

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit with clear, descriptive messages
5. Push to your branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

#### Pull Request Guidelines

- Follow the coding style of the project
- Include tests for new features
- Update documentation for any changes
- Ensure all tests pass before submitting
- Keep pull requests focused on a single change

## Development Environment

### Setup

```bash
# Clone your fork
git clone https://github.com/dustland/roboco.git
cd roboco

# Set up the development environment
./setup.sh  # On Unix/macOS
# or
setup.bat   # On Windows

# Add your API keys to .env
cp .env.example .env
# Edit .env with your API keys
```

### Testing

We use pytest for testing. Run the tests with:

```bash
pytest
```

## Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use descriptive variable and function names
- Include docstrings for all modules, classes, and functions
- Organize imports as described in [roboco.mdc](.cursor/rules/roboco.mdc)

## Documentation

Update documentation when you make changes:

- Update relevant Markdown files in the `docs/` directory
- Add docstrings to new functions, classes, and modules
- Update example scripts if necessary

## License

By contributing to RoboCo, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Recognition

Contributors will be recognized in the project's README and/or CONTRIBUTORS file.

## Questions?

If you have any questions, feel free to create an issue or contact the maintainers at hi@dustland.ai.
