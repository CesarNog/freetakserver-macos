#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

UPSTREAM=https://github.com/FreeTAKTeam/FreeTAKServer.git
UPSTREAM_SHA=19fcc6126f84682d8130823a9ff1b756064aaa3b

command -v docker >/dev/null || { echo "docker not found" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "docker daemon not running" >&2; exit 1; }

if [ ! -d src/.git ]; then
  mkdir -p src
  git -C src init -q
  git -C src remote add origin "$UPSTREAM"
  git -C src fetch -q --depth 1 origin "$UPSTREAM_SHA"
  git -C src checkout -q FETCH_HEAD
fi

for p in patches/*.patch; do
  if git -C src apply --reverse --check "../$p" 2>/dev/null; then
    echo "patch already applied: $p"
  else
    git -C src apply "../$p"
    echo "applied: $p"
  fi
done

if [ ! -f .env ]; then
  umask 077
  {
    echo "FTS_FED_PASSWORD=$(openssl rand -hex 24)"
    echo "FTS_CLIENT_CERT_PASSWORD=$(openssl rand -hex 24)"
    echo "FTS_SECRET_KEY=$(openssl rand -hex 32)"
    echo "FTS_NODE_ID=$(openssl rand -hex 16)"
  } > .env
  echo "generated .env (mode 600)"
fi

docker compose up -d --build

if python3 scripts/wait_ready.py 180; then
  echo "FreeTAKServer up: CoT 8087, SSL CoT 8089, Marti/DP 8443, REST API 19023 (loopback only)"
else
  echo "services not ready after 180s; check: docker compose logs" >&2
  exit 1
fi
