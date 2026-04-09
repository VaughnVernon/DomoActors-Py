# Contributing to DomoActors-Py

Thank you for your interest in contributing to DomoActors-Py!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/VaughnVernon/DomoActors-Py.git
cd DomoActors-Py
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Running Tests

Run the test suite:
```bash
pytest
```

Run a specific test file:
```bash
pytest tests/actors/test_counter.py
```

Run tests with coverage:
```bash
pytest --cov=domo_actors --cov-report=html
```

## Code Style

We use several tools to maintain code quality:

### Black (Code Formatting)
```bash
black domo_actors tests examples
```

### Ruff (Linting)
```bash
ruff check domo_actors tests examples
```

### MyPy (Type Checking)
```bash
mypy domo_actors
```

## Contribution Guidelines

1. **Fork the repository** and create your branch from `main`
2. **Write tests** for any new functionality
3. **Ensure all tests pass** before submitting
4. **Follow the code style** - run black, ruff, and mypy
5. **Write clear commit messages**
6. **Update documentation** if adding new features
7. **Submit a pull request**

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update tests to cover your changes
3. Ensure the test suite passes
4. The PR will be merged once you have sign-off from a maintainer

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Documentation improvements
- Questions about usage

## License

By contributing, you agree that your contributions will be licensed under the LGPL-3.0 License.
