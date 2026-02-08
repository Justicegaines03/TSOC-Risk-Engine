# SOC Risk Engine

A quantitative risk scoring platform for security operations centers, powered by TheHive and Cortex.

Automatically scores SOC cases by enriching observables through Cortex analyzers and computing risk using industry-standard models. Supports both **business (B2B)** cases using Annualized Loss Expectancy and **consumer (B2C)** identity-theft cases using Recovery Difficulty Scoring.

## Quick Start

```bash
git clone <your-repo-url>
cd SOC-Risk-Engine
make setup
```

That's it. The bootstrap script handles environment configuration, service startup, and API key generation.

For detailed setup instructions, see [ONBOARDING.md](ONBOARDING.md).

## Services

| Service       | Port | Description                          |
|---------------|------|--------------------------------------|
| TheHive       | 9000 | Incident response and case management |
| Cortex        | 9001 | Observable analysis engine           |
| Risk Engine   | --   | Automated risk scoring (watch mode)  |
| Cassandra     | 9042 | Database backend                     |
| Elasticsearch | 9200 | Search and indexing                   |

## Dual-Profile Scoring

### Business (B2B) -- ALE Model

Tag cases with `asset:<type>` and `sensitivity:<level>`. The engine calculates Annualized Loss Expectancy:

```
ALE = Likelihood (from Cortex verdicts) x Impact (Asset Value x Sensitivity)
```

### Consumer (B2C) -- Identity Theft

Tag cases with `profile:consumer` and `exposure:<type>`. The engine calculates Recovery Difficulty:

```
Recovery Difficulty = Likelihood x Exposure Severity (0-100)
```

For the full consumer workflow and student analyst guide, see [docs/B2C-CONSUMER-GUIDE.md](docs/B2C-CONSUMER-GUIDE.md).

## Common Commands

```bash
make setup        # First-time setup (one command)
make status       # Check service health
make logs         # Tail all service logs
make test         # Run unit tests
make smoke        # Integration smoke test
make down         # Stop all services
make reset        # Destroy data and re-setup
```

## Documentation

- [ONBOARDING.md](ONBOARDING.md) -- Full setup walkthrough and customization
- [docs/B2C-CONSUMER-GUIDE.md](docs/B2C-CONSUMER-GUIDE.md) -- Consumer identity-theft scoring guide
- [docs/MISP-INTEGRATION.md](docs/MISP-INTEGRATION.md) -- Connecting to your MISP instance
- [CONTRIBUTING.md](CONTRIBUTING.md) -- How to contribute and extend the engine

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Risk Engine                         │
│           (score / watch / health CLI)                  │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │ B2B: ALE Scoring │  │ B2C: Recovery Difficulty │    │
│  └──────────────────┘  └──────────────────────────┘    │
└───────────┬───────────────────────┬─────────────────────┘
            │                       │
    ┌───────▼─────────┐    ┌───────▼──────────┐
    │    TheHive 5    │    │     Cortex       │
    │  (Cases, Tasks) │    │  (Analyzers)     │
    │  localhost:9000 │    │  localhost:9001   │
    └───────┬─────────┘    └──────────────────┘
            │
    ┌───────▼──────────┐   ┌──────────────────┐
    │   Cassandra      │   │  Elasticsearch   │
    │   (Database)     │   │  (Search Index)  │
    └──────────────────┘   └──────────────────┘
```

## Default Credentials

| Service  | Username              | Password |
|----------|-----------------------|----------|
| TheHive  | `admin@thehive.local` | `secret` |

**Change the default password after first login.**

## License

MIT License. See [LICENSE](LICENSE) for details.
