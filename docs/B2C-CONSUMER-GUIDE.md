# Consumer Identity-Theft Scoring Guide

This guide is for SOC analysts (including T-SOC students) handling consumer hotline cases — individuals who are victims of identity theft, data breaches, or similar personal cybersecurity threats.

The SOC Risk Engine scores these cases automatically using the **consumer** profile, producing a **Recovery Difficulty Score** instead of the business ALE metric.

## Prerequisites

- TheHive running and accessible
- Cortex running with at least one consumer-relevant analyzer enabled (see below)
- Risk Engine running in watch mode or available for manual scoring

## How It Works

The consumer profile uses the same pipeline as business (B2B) scoring:

1. **Create a case** in TheHive with the right tags
2. **Add observables** (the victim's leaked email, phone, etc.)
3. **Cortex analyzes** the observables automatically
4. **Risk Engine scores** the case and posts a report to the case

The difference is in the scoring model:

| | Business (B2B) | Consumer (B2C) |
|---|---|---|
| **Input** | Asset type + data sensitivity | Exposure type |
| **Impact metric** | Dollar value (SLE) | Exposure severity (0-100) |
| **Composite score** | ALE in dollars | Recovery Difficulty (0-100) |
| **Recommendations** | SOC incident response actions | Consumer recovery steps |

## Step 1: Create a Consumer Hotline Case

### Option A: Use a Case Template (Recommended)

Create a reusable "Consumer Hotline" case template in TheHive:

1. Go to **Organization** > **Templates** > **Case Templates**
2. Click **+ Create Template**
3. Configure:
   - **Name:** `Consumer Hotline`
   - **Prefix:** `HOTLINE`
   - **Severity:** 2 (Medium) — adjust per intake
   - **Tags:** `profile:consumer` (required for auto-detection)
   - **Tasks:**
     - `Intake` — Record caller details and incident description
     - `Risk Assessment` — Auto-populated by the risk engine
     - `Recovery Actions` — Track recommended steps taken
     - `Follow-Up` — 30-day check-in with the consumer
4. Save the template

When a consumer calls, create a new case from this template.

### Option B: Manual Case Creation

Create a case and add these tags manually:

- `profile:consumer` — **Required.** Tells the risk engine to use consumer scoring.
- `exposure:<type>` — **Required.** Describes what was compromised. See tagging conventions below.

## Step 2: Tagging Conventions

The `exposure:` tag tells the engine how severe the compromise is. Choose the tag that best matches the **most sensitive** data exposed:

| Tag | Severity | Description |
|-----|----------|-------------|
| `exposure:email_only` | 15/100 | Email address leaked. Low risk — password change and MFA. |
| `exposure:phone` | 25/100 | Phone number leaked. SIM swap risk. |
| `exposure:credit_card` | 40/100 | Credit card number compromised. Replaceable, fraud protection exists. |
| `exposure:bank_account` | 60/100 | Bank account details leaked. Direct financial access risk. |
| `exposure:drivers_license` | 70/100 | Driver's license number leaked. Synthetic identity risk. |
| `exposure:medical_records` | 80/100 | Medical records exposed. Medical identity theft risk. |
| `exposure:ssn` | 85/100 | Social Security Number leaked. Credit fraud, tax fraud, long recovery. |
| `exposure:ssn_and_dl` | 95/100 | SSN and driver's license both leaked. Full identity takeover. |

**When in doubt, tag with the most severe exposure.** The engine uses worst-case scoring.

### Multiple Exposures

If multiple types of data were exposed, use the **most severe** single tag. For example, if both an email and SSN were leaked, tag as `exposure:ssn`.

## Step 3: Add Observables

Enter the victim's compromised data as observables in the case. These are what Cortex will analyze.

| Data Type | Observable Type in TheHive | Example |
|-----------|---------------------------|---------|
| Email address | `mail` | `victim@example.com` |
| Phone number | `phone` | `+15551234567` |
| IP address (attacker) | `ip` | `203.0.113.42` |
| Domain (phishing site) | `domain` | `fake-bank-login.com` |
| URL (malicious link) | `url` | `https://phish.example.com/login` |
| Hash (malicious file) | `hash` | `d41d8cd98f00b204e9800998ecf8427e` |

**Important:** Be cautious with PII. Set the TLP (Traffic Light Protocol) appropriately:
- **TLP:RED (3)** for SSN, bank account, medical data
- **TLP:AMBER (2)** for personal email, phone
- **TLP:GREEN (1)** for publicly known attacker indicators

## Step 4: Cortex Enrichment

Cortex automatically analyzes the observables. These free analyzers are recommended for consumer cases:

### Recommended Analyzers

| Analyzer | What It Does | Observable Types |
|----------|-------------|------------------|
| **HaveIBeenPwned** | Checks if an email appears in known data breaches | `mail` |
| **EmailRep** | Reputation score for an email address | `mail` |
| **AbuseIPDB** | Checks if an IP is associated with abuse/attacks | `ip` |
| **URLhaus** | Checks if a URL is associated with malware | `url` |
| **VirusTotal** | Multi-engine scan for IPs, domains, URLs, hashes | `ip`, `domain`, `url`, `hash` |

### Enabling Analyzers in Cortex

1. Log into Cortex at `http://localhost:9001`
2. Go to **Organization** > **Analyzers**
3. Search for the analyzer name
4. Click **Enable** and configure the API key if required
   - HaveIBeenPwned requires a free API key from [haveibeenpwned.com/API](https://haveibeenpwned.com/API)
   - VirusTotal requires a free API key from [virustotal.com](https://www.virustotal.com/)

## Step 5: Reading the Report

After the risk engine scores the case, a report is posted to the **Risk Assessment** task. Here's how to interpret it:

### Recovery Difficulty Score

The composite score (0-100) represents how difficult recovery will be for the victim:

| Score Range | Severity | What It Means |
|-------------|----------|---------------|
| 80-100 | **Critical** | Full identity compromise. Extensive, long-term recovery. |
| 60-79 | **High** | Significant exposure. Active intervention needed immediately. |
| 35-59 | **Medium** | Moderate exposure. Preventive measures needed promptly. |
| 15-34 | **Low** | Limited exposure. Basic hygiene steps sufficient. |
| 0-14 | **Info** | Minimal or no confirmed exposure. |

### Walking the Consumer Through Recovery

The report includes specific recommended recovery actions. As an analyst, walk the consumer through each step:

1. **Read the recommendations aloud** — explain each action in plain language
2. **Help them prioritize** — Critical/High actions should be done immediately, on the call if possible
3. **Provide resource links:**
   - Credit freeze: [Equifax](https://www.equifax.com/personal/credit-report-services/credit-freeze/), [Experian](https://www.experian.com/freeze/center.html), [TransUnion](https://www.transunion.com/credit-freeze)
   - FTC report: [IdentityTheft.gov](https://www.identitytheft.gov/)
   - Annual credit report: [AnnualCreditReport.com](https://www.annualcreditreport.com/)
   - IRS identity protection: [irs.gov/identity-theft-central](https://www.irs.gov/identity-theft-central)
4. **Document what was completed** in the `Recovery Actions` task
5. **Schedule follow-up** in the `Follow-Up` task (typically 30 days)

## Step 6: Escalation Path

Escalate to a senior analyst when:

- **Recovery Difficulty is Critical (80+)** — full identity takeover requires coordinated response
- **Multiple breach sources confirmed** — HIBP shows the email in 5+ breaches
- **Active fraud detected** — the consumer reports unauthorized transactions or accounts
- **Minor involved** — victim is under 18 (special legal protections apply)
- **Unsure about guidance** — when in doubt, escalate

## CLI Usage

### Score a consumer case manually

```bash
# Auto-detect profile from case tags
python -m risk_engine score --case-id ~123456

# Override profile and exposure type
python -m risk_engine score --case-id ~123456 --profile consumer --exposure-type ssn
```

### Watch mode (scores both B2B and B2C automatically)

```bash
python -m risk_engine watch
```

Watch mode detects the profile from each case's tags — no configuration needed.

## Example Scenario

**Call:** "Someone opened a credit card in my name. I also got a letter from the IRS saying someone filed taxes using my SSN."

**Analyst steps:**

1. Create case from "Consumer Hotline" template
2. Add tags: `profile:consumer`, `exposure:ssn`
3. Add observables:
   - Victim's email as `mail` observable
   - Any suspicious IP addresses from account logs as `ip`
4. Wait for Cortex to enrich (or trigger manually)
5. Risk engine scores: SSN exposure (85) x high likelihood = **Critical**
6. Walk consumer through: credit freeze, FTC report, IRS identity protection, police report
7. Document completed steps in the Recovery Actions task
8. Schedule 30-day follow-up
