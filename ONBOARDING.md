# SOC Risk Engine — Onboarding Guide

This guide walks you through setting up the SOC Risk Engine from scratch. Whether you're mirroring into a GitLab instance (T-SOC) or forking on GitHub, these steps get you from zero to scoring cases.

## Prerequisites

- **Docker Desktop** installed and running ([download](https://www.docker.com/products/docker-desktop/))
- **8 GB RAM minimum** (Cassandra + Elasticsearch + TheHive are memory-hungry)
- **Ports 9000-9001 free** (TheHive and Cortex)
- **Python 3.10+** (only needed for running tests locally)

## Quick Start (One Command)

```bash
git clone <your-repo-url>
cd SOC-Risk-Engine
make setup
```

This runs the bootstrap script which:
1. Generates `.env` with a random TheHive secret
2. Starts the Docker Compose stack (Cassandra, Elasticsearch, Cortex, TheHive)
3. Waits for all services to be healthy
4. Attempts to auto-configure Cortex and generate API keys
5. Starts the risk engine in watch mode
6. Prints a summary with URLs and next steps

## Manual Setup (If `make setup` Doesn't Work)

### Step 1: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set `THEHIVE_SECRET`:

```bash
# Generate a secret
openssl rand -base64 32
# Paste the output as the THEHIVE_SECRET value
```

### Step 2: Start Services

```bash
docker compose up -d
```

Wait 1-2 minutes for initialization:

```bash
docker compose logs -f thehive
# Wait until you see the application is ready, then Ctrl+C
```

### Step 3: Configure Cortex

1. Open http://localhost:9001
2. If prompted, run the database migration
3. Create an organization (e.g., "SOC")
4. Create a user within that org with `orgadmin` role
5. Log in as that user
6. Go to **Organization > Analyzers** and enable your desired analyzers
7. Generate an API key: click your username > **API Key** > **Renew**

### Step 4: Configure TheHive

1. Open http://localhost:9000
2. Log in: `admin@thehive.local` / `secret`
3. **Change the default password immediately**
4. Generate an API key: click your username > **API Key** > **Renew**

### Step 5: Update .env with API Keys

```bash
THEHIVE_API_KEY=<paste TheHive key>
CORTEX_API_KEY=<paste Cortex key>
```

### Step 6: Restart the Risk Engine

```bash
docker compose restart risk_engine
```

## Verifying the Deployment

```bash
# Check all services are running
make status

# Run the smoke test
make smoke

# View risk engine logs
make logs-engine
```

## Creating Your First Case

### B2B (Business) Case

1. In TheHive, click **+ New Case**
2. Set a title (e.g., "Suspicious Network Traffic from 203.0.113.42")
3. Add tags:
   - `asset:server` (options: workstation, server, database, critical_infra)
   - `sensitivity:confidential` (options: public, internal, confidential, restricted)
4. Add observables (the indicators to investigate):
   - Type: `ip`, Value: `203.0.113.42`
5. Run Cortex analyzers on the observables
6. The risk engine will automatically score the case and post a report

### B2C (Consumer) Case

1. In TheHive, click **+ New Case** (or use the Consumer Hotline template)
2. Set a title (e.g., "Identity Theft Report — Jane Doe")
3. Add tags:
   - `profile:consumer` (required — triggers consumer scoring)
   - `exposure:ssn` (see [B2C Consumer Guide](docs/B2C-CONSUMER-GUIDE.md) for all options)
4. Add observables:
   - Type: `mail`, Value: `victim@example.com`
5. Run Cortex analyzers (HaveIBeenPwned, etc.)
6. The risk engine scores the case with a Recovery Difficulty Score

For the full B2C workflow and student analyst guide, see [docs/B2C-CONSUMER-GUIDE.md](docs/B2C-CONSUMER-GUIDE.md).

## Understanding Risk Scores

### B2B: Annualized Loss Expectancy (ALE)

```
ALE = Likelihood x Impact
    = (Cortex verdict weighting) x (Asset Value x Sensitivity Multiplier)
```

| Risk Level | ALE Threshold |
|------------|--------------|
| Critical   | $500,000+    |
| High       | $100,000+    |
| Medium     | $10,000+     |
| Low        | $1,000+      |
| Info       | Below $1,000 |

### B2C: Recovery Difficulty Score

```
Recovery Difficulty = Likelihood x Exposure Severity
```

| Severity Level | Score Threshold |
|---------------|----------------|
| Critical      | 80+            |
| High          | 60+            |
| Medium        | 35+            |
| Low           | 15+            |
| Info          | Below 15       |

## Customization

### Adjusting Scoring Parameters

Edit `risk_engine/config.py` to change:

- **`ASSET_VALUES`** — Dollar values for each asset tier
- **`SENSITIVITY_MULTIPLIERS`** — Impact multipliers for data classification
- **`RISK_THRESHOLDS`** — ALE dollar thresholds for risk levels
- **`B2C_EXPOSURE_WEIGHTS`** — Severity scores for each exposure type
- **`B2C_SEVERITY_THRESHOLDS`** — Score thresholds for consumer severity levels
- **`VERDICT_WEIGHTS`** — How Cortex verdict levels map to likelihood

After changing `config.py`, rebuild and restart:

```bash
docker compose build risk_engine
docker compose restart risk_engine
```

### Adding Cortex Analyzers

1. Log into Cortex at http://localhost:9001
2. Go to **Organization > Analyzers**
3. Enable analyzers (some require API keys):
   - **VirusTotal** — Multi-engine malware/URL scanning
   - **HaveIBeenPwned** — Email breach checking (great for B2C)
   - **AbuseIPDB** — IP reputation
   - **URLhaus** — Malicious URL database
   - **EmailRep** — Email reputation scoring

## MISP Integration

To connect TheHive to your existing MISP instance, see [docs/MISP-INTEGRATION.md](docs/MISP-INTEGRATION.md). MISP is configured per-SOC through the TheHive admin UI — it is not part of this repo's Docker stack.

## T-SOC Specific Notes

### GitLab Mirror Workflow

1. Mirror the GitHub repo into your GitLab instance
2. The `.gitlab-ci.yml` pipeline will run automatically on push
3. Customize the `deploy` stage for your target infrastructure
4. API keys and secrets should be stored as GitLab CI/CD Variables (not in `.env`)

### Internal Network Configuration

If TheHive/Cortex need to reach internal services:

- For services on the Docker host: use `host.docker.internal` (Docker Desktop) or the host's IP
- For services on the internal network: ensure Docker's network can route to them
- Update `THEHIVE_URL` and `CORTEX_URL` in `.env` if pointing to existing instances

### Student Analyst Onboarding

1. Have students read this guide for infrastructure context
2. For B2C hotline work, direct them to [docs/B2C-CONSUMER-GUIDE.md](docs/B2C-CONSUMER-GUIDE.md)
3. Create the "Consumer Hotline" case template in TheHive (instructions in the B2C guide)
4. Students should practice with test cases before handling real consumer calls

## Common Commands

```bash
make setup        # First-time setup
make status       # Check service health
make logs         # Tail all logs
make logs-engine  # Tail risk engine logs
make test         # Run unit tests
make smoke        # Run integration smoke test
make down         # Stop all services
make reset        # Destroy data and re-setup
```

## Troubleshooting

### "Cannot connect to the Docker daemon"
Start Docker Desktop and wait for the whale icon to stop animating.

### Services won't start (out of memory)
Ensure you have at least 8 GB RAM allocated to Docker. Check in Docker Desktop > Settings > Resources.

### Risk engine keeps restarting
Check logs: `make logs-engine`. Common causes:
- Invalid API keys in `.env`
- TheHive or Cortex not yet ready (the engine retries automatically)

### Tests fail locally
Install dev dependencies first: `pip install -r requirements-dev.txt`

### Reset everything
```bash
make reset
```
This destroys all data and re-runs the bootstrap from scratch.
