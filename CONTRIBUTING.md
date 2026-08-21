# Contributing to FinSight Pro

Thank you for your interest in contributing to FinSight Pro! This document provides guidelines for contributing to both the open-source CLI engine and the commercial desktop application.

## Project Structure

```
finsight-pro/
├── src/finsight/          # Python analysis engine (open-source, MIT)
├── tests/               # Test suite
├── examples/            # Sample data files
├── desktop/             # Commercial desktop application
━── electron/           # Electron main process
━── frontend/           # React + TypeScript GUI
━── api/               # FastAPI backend wrapping the engine
├── landing/             # Marketing website
├── docs/                # Documentation
└── .github/             # GitHub templates and workflows
```

## Open-Source CLI Contributions

The Python analysis engine (`src/finsight/`) is open-source under the MIT License. Contributions are welcome!

### How to Contribute

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** with clear commit messages
4. **Add tests** for any new functionality
5. **Run tests**: `python -m pytest tests/ -v`
6. **Submit a Pull Request** to the `main` branch

### Code Standards

- Python 3.10+
- Follow PEP 8 style guidelines
- All financial formulas must include a docstring explaining the calculation
- Use type hints for all function signatures
- Maintain test coverage above 80%

### Reporting Bugs

Please use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) when reporting issues. Include:
- The input file that caused the error (sanitized if necessary)
- The full error traceback
- Your Python version and operating system

### Suggesting Features

Feature suggestions for the open-source CLI are welcome via the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md).

## Commercial Desktop Application

The desktop application (`desktop/`) is proprietary software. External contributions to this portion are handled differently:

- **Bug bounty program** for security vulnerabilities
- **Beta testing program** for users who want early access
- **Translation contributions** via Crowdin (coming soon)

See the [landing page](https://finsightpro.com) for information about the Pro version.

## License

- **CLI Engine** (`src/finsight/`): MIT License
- **Desktop App** (`desktop/`): Proprietary - see LICENSE_DESKTOP
- **Documentation**: CC BY 4.0
