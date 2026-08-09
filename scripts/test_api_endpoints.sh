#!/bin/bash
# Local API Test Runner Script for Dota 2 Visualizer Backend (Phase 4)
# Usage: bash scripts/test_api_endpoints.sh [BASE_URL]

BASE_URL="${1:-http://127.0.0.1:8000}"
TEST_STEAM_ID="70388657" # Dendi 32-bit Steam ID

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN} ⚔️  Dota 2 Visualizer API Verification Runner  ⚔️ ${NC}"
echo -e "${CYAN} Base URL: ${BASE_URL}${NC}"
echo -e "${CYAN}====================================================${NC}\n"

# 1. Top-Level Health Check
echo -e "${YELLOW}[1/5] Testing GET /health ...${NC}"
curl -s -X GET "${BASE_URL}/health" | grep -v '^[[:space:]]*$'
echo -e "\n"

# 2. V1 Health Check
echo -e "${YELLOW}[2/5] Testing GET /api/v1/health ...${NC}"
curl -s -X GET "${BASE_URL}/api/v1/health" | grep -v '^[[:space:]]*$'
echo -e "\n"

# 3. Player Match Sync
echo -e "${YELLOW}[3/5] Testing POST /api/v1/players/${TEST_STEAM_ID}/sync ...${NC}"
curl -s -X POST "${BASE_URL}/api/v1/players/${TEST_STEAM_ID}/sync" | grep -v '^[[:space:]]*$'
echo -e "\n"

# 4. Get Player Matches & Profile
echo -e "${YELLOW}[4/5] Testing GET /api/v1/players/${TEST_STEAM_ID}/matches ...${NC}"
curl -s -X GET "${BASE_URL}/api/v1/players/${TEST_STEAM_ID}/matches" | grep -v '^[[:space:]]*$' | head -n 30
echo -e "\n... (truncated for brevity)\n"

# 5. Trigger 90-Day LRU Cache Eviction & Ephemeral 1-Hour Media Purge Tasks
echo -e "${YELLOW}[5/10] Testing POST /api/v1/admin/lru-prune & /admin/ephemeral-purge ...${NC}"
curl -s -X POST "${BASE_URL}/api/v1/admin/lru-prune?days_inactive=90" | grep -v '^[[:space:]]*$'
echo -e "\n"
curl -s -X POST "${BASE_URL}/api/v1/admin/ephemeral-purge?ttl_seconds=3600" | grep -v '^[[:space:]]*$'
echo -e "\n"

# 6. Steam Login Redirect URL
echo -e "${YELLOW}[6/7] Testing GET /api/v1/auth/steam/login ...${NC}"
curl -s -X GET "${BASE_URL}/api/v1/auth/steam/login" | grep -v '^[[:space:]]*$'
echo -e "\n"

# 7. Steam Mock Callback & Get User Profile (/auth/me)
echo -e "${YELLOW}[7/7] Testing GET /api/v1/auth/steam/callback & GET /api/v1/auth/me ...${NC}"
TOKEN_RESP=$(curl -s -X GET "${BASE_URL}/api/v1/auth/steam/callback?mock_steam_id64=76561197960265728")
echo -e "Token Response: ${TOKEN_RESP}"

# Extract access_token value using python
ACCESS_TOKEN=$(echo "${TOKEN_RESP}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "${ACCESS_TOKEN}" ]; then
  echo -e "\nFetching /api/v1/auth/me with Bearer token..."
  curl -s -X GET "${BASE_URL}/api/v1/auth/me" -H "Authorization: Bearer ${ACCESS_TOKEN}" | grep -v '^[[:space:]]*$'
  echo -e "\n"

  echo -e "${YELLOW}[9/9] Testing API Key Management (POST /api/v1/keys, GET /api/v1/keys, DELETE /api/v1/keys/{id}) ...${NC}"
  KEY_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/keys" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"name": "Local Test API Key"}')

  echo -e "Create API Key Response: ${KEY_RESP}"

  KEY_ID=$(echo "${KEY_RESP}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

  echo -e "\nListing user API keys..."
  curl -s -X GET "${BASE_URL}/api/v1/keys" -H "Authorization: Bearer ${ACCESS_TOKEN}" | grep -v '^[[:space:]]*$'
  echo -e "\n"

  if [ -n "${KEY_ID}" ]; then
    echo -e "Revoking API Key ID ${KEY_ID}..."
    curl -s -X DELETE "${BASE_URL}/api/v1/keys/${KEY_ID}" -H "Authorization: Bearer ${ACCESS_TOKEN}" | grep -v '^[[:space:]]*$'
    echo -e "\n"
  fi
fi

# 8. Submit Render Job, Poll Status, List Jobs
echo -e "${YELLOW}[8/9] Testing POST /api/v1/render/jobs & GET /api/v1/render/jobs/{job_id} ...${NC}"
JOB_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/render/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": 70388657,
    "metric": "Hero Versatility",
    "quality": "Draft",
    "aspect_ratio": "9:16",
    "theme": "Midnight Cyberpunk"
  }')

echo -e "Submit Job Response: ${JOB_RESP}"

JOB_ID=$(echo "${JOB_RESP}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null)

if [ -n "${JOB_ID}" ]; then
  echo -e "\nPolling job status for ${JOB_ID}..."
  curl -s -X GET "${BASE_URL}/api/v1/render/jobs/${JOB_ID}" | grep -v '^[[:space:]]*$'
  echo -e "\n"
fi

echo -e "\nListing render jobs for player 70388657..."
curl -s -X GET "${BASE_URL}/api/v1/render/jobs?player_id=70388657" | grep -v '^[[:space:]]*$'
echo -e "\n"

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN} ✅ All API endpoint verification curls complete!   ${NC}"
echo -e "${GREEN}====================================================${NC}"
