# Contributing to SOC Risk Engine

Thank you for helping improve the SOC Risk Engine. This guide covers how to contribute, whether you're on a SOC team forking the repo or submitting changes back upstream.

## Getting Started

1. Fork or clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Run the test suite to confirm everything works:
   ```bash
   make test
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run linting and tests:
   ```bash
   make lint
   make test
   ```
4. Commit with a clear message describing the change
5. Push and open a pull request (GitHub) or merge request (GitLab)

## Project Structure

```
SOC-Risk-Engine/
├── risk_engine/           # Python package
│   ├── main.py            # CLI entry point (score, watch, health)
│   ├── config.py          # All scoring parameters and thresholds
│   ├── calculator.py      # Likelihood, impact, ALE/severity math
│   ├── reporter.py        # Markdown report generation
│   ├── models.py          # Data models (Observable, RiskScore, etc.)
│   ├── clients/           # API clients
│   │   ├── thehive.py     # TheHive 5 REST API
│   │   └── cortex.py      # Cortex REST API
│   ├── Dockerfile         # Container definition
│   └── requirements.txt   # Runtime dependencies
├── tests/                 # Unit tests
├── scripts/               # Bootstrap and smoke test scripts
├── docs/                  # Guides (MISP, B2C consumer)
├── docker-compose.yml     # Full stack definition
└── Makefile               # Ergonomic CLI targets
```

## Common Contributions

### Adding a New Exposure Type (B2C)

1. Add the exposure type and weight to `B2C_EXPOSURE_WEIGHTS` in `config.py`:
   ```python
   B2C_EXPOSURE_WEIGHTS = {
       ...
       "passport": 75,  # High — international identity risk
   }
   ```
2. Add a test case in `tests/test_calculator.py`
3. Document the new tag in `docs/B2C-CONSUMER-GUIDE.md`

### Adding a New Asset Tier (B2B)

1. Add the asset type and dollar value to `ASSET_VALUES` in `config.py`
2. Add a test case in `tests/test_calculator.py`
3. Update the `--asset-type` help text in `main.py`

### Adjusting Risk Thresholds

Edit the relevant threshold dictionary in `config.py`:
- `RISK_THRESHOLDS` for B2B ALE thresholds
- `B2C_SEVERITY_THRESHOLDS` for consumer severity thresholds

Always add or update tests to cover the new boundaries.

### Adding Cortex Analyzer Support

The risk engine works with any Cortex analyzer that produces taxonomies. To optimize for a specific analyzer:

1. Check how it reports verdicts in `clients/cortex.py` > `extract_verdicts()`
2. If it uses non-standard taxonomy levels, add a mapping
3. Document the analyzer in the relevant guide

## Testing

### Running Tests

```bash
# All tests
make test

# With coverage
make test-coverage

# Specific test file
python -m pytest tests/test_calculator.py -v

# Specific test class
python -m pytest tests/test_calculator.py::TestComputeImpactB2C -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Use fixtures from `tests/conftest.py` for sample data
- Test both B2B and B2C code paths
- Use `pytest.approx()` for floating-point comparisons

## Code Style

- Python 3.10+ (use type hints)
- Lint with `ruff` (configuration follows defaults)
- Docstrings on all public functions
- Use `logger` for runtime messages, not `print`

## Pull Request Guidelines

- Keep PRs focused on a single change
- Include tests for new functionality
- Update documentation if the change affects user-facing behavior
- Ensure `make lint` and `make test` pass before submitting
- Write a clear PR description explaining what and why

## Questions

Open an issue in the repository if you have questions about the architecture, scoring model, or how to contribute a specific feature.
