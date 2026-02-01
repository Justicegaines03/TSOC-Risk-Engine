# TSOC Risk Engine

A platform to quantify risk powered by TheHive for incident response and case management.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- `docker-compose` CLI (included with Docker Desktop)

## Quick Start

1. **Start Docker Desktop** and ensure the whale icon in your menu bar is steady (not animating)

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Wait for initialization** (~1-2 minutes on first run):
   ```bash
   docker-compose logs -f thehive
   ```
   Wait until you see the application is ready.

4. **Access TheHive:** Open http://localhost:9000

## Default Credentials

| Service  | Username              | Password |
|----------|-----------------------|----------|
| TheHive  | `admin@thehive.local` | `secret` |

> **Important:** Change the default password after first login.

## Services

| Service       | Port | Description                          |
|---------------|------|--------------------------------------|
| TheHive       | 9000 | Incident response platform           |
| Cassandra     | 9042 | Database backend                     |
| Elasticsearch | 9200 | Search and indexing engine           |

## Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f thehive

# Restart a specific service
docker-compose restart thehive

# Check service status
docker-compose ps
```

## Troubleshooting

### "Cannot connect to the Docker daemon"
Make sure Docker Desktop is running (whale icon in menu bar).

### TheHive not accessible
Wait 1-2 minutes after starting. Check logs with:
```bash
docker-compose logs thehive
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```
> **Warning:** This deletes all data.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   TheHive                       │
│              (localhost:9000)                   │
└─────────────────┬───────────────┬───────────────┘
                  │               │
        ┌─────────▼─────┐   ┌─────▼─────────────┐
        │   Cassandra   │   │  Elasticsearch    │
        │   (Database)  │   │  (Search Index)   │
        └───────────────┘   └───────────────────┘
```

## License

See [LICENSE](LICENSE) for details.
