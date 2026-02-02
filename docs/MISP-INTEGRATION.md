# Connecting TheHive to MISP

This guide covers how to connect TheHive to your existing MISP instance for importing threat intelligence and pen test findings into risk assessment cases.

## Prerequisites

- TheHive running (via `docker-compose up -d`)
- Access to your MISP instance
- MISP API key with appropriate permissions

## Step 1: Generate a MISP API Key

1. Log into your MISP instance
2. Go to **Administration > List Users**
3. Click on your user (or create a dedicated sync user)
4. Click **Auth Keys** in the left sidebar
5. Click **Add authentication key**
6. Set an expiration date (or leave empty for no expiration)
7. Copy the generated API key - you'll need this for TheHive

## Step 2: Configure TheHive MISP Connector

1. Log into TheHive at `http://localhost:9000`
   - Default: `admin@thehive.local` / `secret`

2. Navigate to **Platform Management** (gear icon) > **Connectors**

3. Click **+ Add connector** and select **MISP**

4. Fill in the connection details:

   | Field | Value |
   |-------|-------|
   | Name | `Production MISP` (or your preferred name) |
   | URL | `https://your-misp-server.local` |
   | API Key | (paste the key from Step 1) |
   | Verify SSL | Enable if using valid certificates |
   | Max age | `30` (days - how far back to import) |
   | Max attributes | `10000` (adjust based on your needs) |

5. Click **Test** to verify the connection

6. Click **Save**

## Step 3: Configure Import Filters (Optional)

You can filter which MISP events get imported as alerts:

1. In the MISP connector settings, go to **Filters**

2. Configure filters based on:
   - **Tags**: Only import events with specific tags (e.g., `pentest`, `vulnerability`)
   - **Threat Level**: Filter by MISP threat level (1-4)
   - **Organizations**: Only import from specific organizations

Example filter for pen test findings:
```
Tags: pentest, vulnerability-assessment
Threat Level: 1, 2, 3
```

## Step 4: Import MISP Events

### Manual Import

1. Go to **Alerts** in TheHive
2. Click **+ New Alert** > **Import from MISP**
3. Select the events to import
4. Click **Import**

### Automatic Sync

1. In the MISP connector settings, enable **Automatic sync**
2. Set the sync interval (e.g., every 15 minutes)
3. TheHive will automatically create alerts from new MISP events

## Step 5: Convert Alerts to Cases

When a MISP event is imported as an alert:

1. Open the alert in TheHive
2. Click **Create Case** or **Merge into existing case**
3. For risk assessments, merge into your risk assessment case
4. The MISP attributes become **Observables** in the case

## Pen Test Workflow

For your 5-task risk assessment workflow:

### In MISP (Pen Test Task)
1. Create a new **Event** for each pen test engagement
2. Add **Attributes** for each finding:
   - Type: `vulnerability` for CVEs
   - Type: `ip-dst` or `domain` for affected systems
   - Type: `text` for descriptions
3. Tag with severity: `tlp:red`, `severity:critical`, etc.
4. Publish the event

### In TheHive (Risk Heatmap Task)
1. Import the MISP event as an alert
2. Merge into your risk assessment case
3. Review observables and add risk scores via custom fields
4. Use the case dashboard for visualization

## Troubleshooting

### Connection Failed
- Verify MISP URL is reachable from the Docker network
- Check API key permissions in MISP
- Ensure SSL certificates are valid (or disable SSL verification for testing)

### No Events Imported
- Check your import filters aren't too restrictive
- Verify MISP events are **published** (unpublished events won't sync)
- Check the max age setting

### Events Not Appearing as Alerts
- TheHive only imports new events after the connector is configured
- Use manual import for existing events

## Network Configuration

If TheHive is running in Docker and MISP is on your local network:

1. Ensure Docker can reach your MISP server
2. If using hostname, add to `/etc/hosts` or use IP address
3. For Docker Desktop on Mac, use `host.docker.internal` to reach host machine

Example if MISP runs on the same host:
```
URL: http://host.docker.internal:8080
```

## Security Notes

- Use HTTPS for production MISP connections
- Create a dedicated MISP user for TheHive with read-only permissions
- Rotate API keys periodically
- Consider network segmentation between TheHive and MISP
