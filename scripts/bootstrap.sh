#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# SOC Risk Engine — First-Run Bootstrap
#
# This script automates the entire first-time setup:
#   1. Checks prerequisites (Docker)
#   2. Generates .env with a real secret
#   3. Starts the Docker Compose stack
#   4. Waits for all services to be healthy
#   5. Configures Cortex (org, user, API key)
#   6. Creates a TheHive API key for the risk engine
#   7. Writes API keys back into .env
#   8. Starts the risk engine
#   9. Prints a summary
#
# Usage:  bash scripts/bootstrap.sh
#         make setup
# ---------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
COMPOSE="docker compose"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ---------------------------------------------------------------------------
# 1. Prerequisites
# ---------------------------------------------------------------------------

info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    fail "Docker is not installed. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
fi

if ! docker info &> /dev/null; then
    fail "Docker daemon is not running. Start Docker Desktop and try again."
fi

ok "Docker is running"

# ---------------------------------------------------------------------------
# 2. Generate .env
# ---------------------------------------------------------------------------

if [ -f "$ENV_FILE" ]; then
    warn ".env already exists — keeping existing configuration"
else
    info "Generating .env from .env.example..."
    cp "$PROJECT_DIR/.env.example" "$ENV_FILE"

    # Generate a real secret key
    SECRET=$(openssl rand -base64 32)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|your-secret-key-here|${SECRET}|" "$ENV_FILE"
    else
        sed -i "s|your-secret-key-here|${SECRET}|" "$ENV_FILE"
    fi

    ok ".env created with generated THEHIVE_SECRET"
fi

# ---------------------------------------------------------------------------
# 3. Start the infrastructure stack (without risk engine)
# ---------------------------------------------------------------------------

info "Starting infrastructure services (Cassandra, Elasticsearch, Cortex, TheHive)..."
cd "$PROJECT_DIR"
$COMPOSE up -d cassandra elasticsearch cortex thehive

# ---------------------------------------------------------------------------
# 4. Wait for services to be healthy
# ---------------------------------------------------------------------------

wait_for_service() {
    local name="$1"
    local url="$2"
    local max_attempts="${3:-60}"
    local attempt=0

    info "Waiting for $name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            ok "$name is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    fail "$name did not become ready after $((max_attempts * 5)) seconds"
}

wait_for_service "Elasticsearch" "http://localhost:9200/_cluster/health" 60
wait_for_service "Cortex"        "http://localhost:9001/api/status"     60
wait_for_service "TheHive"       "http://localhost:9000/api/status"     90

# ---------------------------------------------------------------------------
# 5. Configure Cortex (org, user, API key)
# ---------------------------------------------------------------------------

info "Checking Cortex configuration..."

# Check if Cortex has already been initialized (has organizations)
CORTEX_STATUS=$(curl -sf http://localhost:9001/api/status 2>/dev/null || echo '{}')

# Try to create the default org and user via the Cortex maintenance API.
# If Cortex has already been configured, these will 400/409 — that's fine.

# Create organization
CORTEX_ORG_RESP=$(curl -sf -X POST http://localhost:9001/api/organization \
    -H 'Content-Type: application/json' \
    -d '{"name": "SOC", "description": "Default SOC Organization", "status": "Active"}' \
    2>/dev/null || echo '{"already":"exists"}')

# Create orgadmin user
CORTEX_USER_RESP=$(curl -sf -X POST http://localhost:9001/api/user \
    -H 'Content-Type: application/json' \
    -d '{"login": "soc@thehive.local", "name": "SOC Admin", "roles": ["superadmin"], "organization": "SOC", "password": "soc-risk-engine"}' \
    2>/dev/null || echo '{"already":"exists"}')

# Generate Cortex API key (try with the maintenance API first)
CORTEX_API_KEY=$(curl -sf -X POST http://localhost:9001/api/user/soc@thehive.local/key/renew \
    2>/dev/null || echo "")

if [ -n "$CORTEX_API_KEY" ] && [ "$CORTEX_API_KEY" != "null" ]; then
    # Strip quotes if present
    CORTEX_API_KEY=$(echo "$CORTEX_API_KEY" | tr -d '"')
    ok "Cortex API key generated"
else
    warn "Could not auto-generate Cortex API key. You may need to generate one manually in the Cortex UI."
    CORTEX_API_KEY=""
fi

# ---------------------------------------------------------------------------
# 6. Create TheHive API key
# ---------------------------------------------------------------------------

info "Checking TheHive configuration..."

# Log in to get a session, then create an API key
# TheHive 5 default admin credentials
THEHIVE_SESSION=$(curl -sf -X POST http://localhost:9000/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"login": "admin@thehive.local", "password": "secret"}' \
    2>/dev/null || echo "")

THEHIVE_API_KEY=""
if [ -n "$THEHIVE_SESSION" ]; then
    # Extract the auth token
    AUTH_TOKEN=$(echo "$THEHIVE_SESSION" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || echo "")

    if [ -n "$AUTH_TOKEN" ]; then
        # Try to create an API key for the admin user
        THEHIVE_API_KEY=$(curl -sf -X POST http://localhost:9000/api/v1/user/admin@thehive.local/key/renew \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            2>/dev/null || echo "")
        THEHIVE_API_KEY=$(echo "$THEHIVE_API_KEY" | tr -d '"')
    fi
fi

if [ -n "$THEHIVE_API_KEY" ] && [ "$THEHIVE_API_KEY" != "null" ] && [ "$THEHIVE_API_KEY" != "" ]; then
    ok "TheHive API key generated"
else
    warn "Could not auto-generate TheHive API key. You may need to generate one manually in the TheHive UI."
    THEHIVE_API_KEY=""
fi

# ---------------------------------------------------------------------------
# 7. Write API keys back into .env
# ---------------------------------------------------------------------------

if [ -n "$CORTEX_API_KEY" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|CORTEX_API_KEY=.*|CORTEX_API_KEY=${CORTEX_API_KEY}|" "$ENV_FILE"
    else
        sed -i "s|CORTEX_API_KEY=.*|CORTEX_API_KEY=${CORTEX_API_KEY}|" "$ENV_FILE"
    fi
    ok "Cortex API key written to .env"
fi

if [ -n "$THEHIVE_API_KEY" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|THEHIVE_API_KEY=.*|THEHIVE_API_KEY=${THEHIVE_API_KEY}|" "$ENV_FILE"
    else
        sed -i "s|THEHIVE_API_KEY=.*|THEHIVE_API_KEY=${THEHIVE_API_KEY}|" "$ENV_FILE"
    fi
    ok "TheHive API key written to .env"
fi

# ---------------------------------------------------------------------------
# 8. Start the risk engine
# ---------------------------------------------------------------------------

info "Starting risk engine..."
$COMPOSE up -d risk_engine 2>/dev/null || warn "Risk engine service not yet enabled in docker-compose.yml"

# ---------------------------------------------------------------------------
# 9. Summary
# ---------------------------------------------------------------------------

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  SOC Risk Engine — Setup Complete${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  ${CYAN}TheHive:${NC}   http://localhost:9000"
echo -e "             Login: admin@thehive.local / secret"
echo -e "             ${YELLOW}(Change the default password!)${NC}"
echo ""
echo -e "  ${CYAN}Cortex:${NC}    http://localhost:9001"
if [ -n "$CORTEX_API_KEY" ]; then
    echo -e "             API key configured automatically"
else
    echo -e "             ${YELLOW}Manual API key setup required${NC}"
fi
echo ""
echo -e "  ${CYAN}Scoring Profiles:${NC}"
echo -e "    B2B:      Tag cases with asset:<type> and sensitivity:<level>"
echo -e "    Consumer: Tag cases with profile:consumer and exposure:<type>"
echo ""
echo -e "  ${CYAN}Documentation:${NC}"
echo -e "    Onboarding:  ONBOARDING.md"
echo -e "    B2C Guide:   docs/B2C-CONSUMER-GUIDE.md"
echo -e "    MISP:        docs/MISP-INTEGRATION.md"
echo ""
echo -e "  ${CYAN}Next Steps:${NC}"
echo "    1. Change the default TheHive password"
echo "    2. Enable Cortex analyzers (VirusTotal, HIBP, etc.)"
echo "    3. Create a case and test scoring"
echo "    4. Run 'make status' to verify everything is healthy"
echo ""
echo -e "${GREEN}============================================================${NC}"
