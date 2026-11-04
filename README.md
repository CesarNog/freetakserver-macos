# freetakserver-macos

[FreeTAKServer](https://github.com/FreeTAKTeam/FreeTAKServer) (FTS) — open-source TAK server (ATAK/WinTAK/iTAK) — running in Docker on macOS (Apple Silicon and Intel), with the fixes the upstream Docker setup needs to actually start.

Not affiliated with FreeTAKTeam. Upstream is fetched at a pinned commit and patched at install time; no upstream code is vendored here.

## Install

Requires Docker Desktop, git, openssl, python3.

```bash
git clone https://github.com/CesarNog/freetakserver-macos.git
cd freetakserver-macos
./install.sh
python3 scripts/test_cot.py   # optional smoke test
```

`install.sh`: fetches upstream at the pinned commit, applies `patches/`, generates random secrets into `.env` (mode 600, git-ignored), builds and starts the stack, waits for the ports.

## Ports (loopback only)

| Port  | Service |
|-------|---------|
| 8087  | CoT (TCP) |
| 8089  | CoT (SSL) |
| 8443  | Marti / Data Package (HTTPS) |
| 19023 | REST API (auth required) |

Federation (9000) is not published. The upstream compose publishes `8080`, which nothing listens on; the REST API is on `19023`. To accept connections from other devices (e.g. a phone running ATAK), change the `127.0.0.1:` prefixes in `compose.yaml` and keep in mind that CoT 8087 is unauthenticated.

The FreeTAKHub web UI is a separate project and is not included.

## What the patch fixes

`patches/0001-dockerfile-macos-arm64.patch` changes only upstream's `Dockerfile`:

1. `AttributeError: property 'span_exporter' of 'BatchSpanProcessor' object has no setter` — DigitalPy assigns that attribute; `opentelemetry-sdk >= 1.34` made it read-only and upstream leaves `opentelemetry-sdk="*"` unpinned. Pinned to `1.33.1`. (Probed: 1.25.0–1.33.1 accept the assignment, 1.34.1+ do not.)
2. Startup exits with `Cannot access configuration path .../FTSDataBase.db` — `MainConfig.validate_and_sanitize_path` requires the DB file and `Logs/` to exist. They are now created in the image, so a fresh named volume is seeded with them.
3. `ENV FTS_DATA_PATH = "/opt/fts/"` (spaces around `=`) is parsed as a literal `= /opt/fts/`. Fixed.

`compose.yaml` also removes the default secrets (`FTS_FED_PASSWORD`, `FTS_SECRET_KEY`, ...) in favor of `.env` values generated per install.

## Validation

- Apple Silicon (arm64), Docker Desktop, fresh `install.sh`: stack starts, no tracebacks, two CoT clients on 8087 receive each other's events, 8443 and 19023 respond. `scripts/test_cot.py` exits 0.
- CI (`.github/workflows/ci.yml`): same install + test on Linux amd64. CI does not cover macOS/arm64 (GitHub runners have no Docker there).

## Known noise (upstream, non-fatal in my tests)

- `failed to register component: ... has no attribute ...` lines at startup (DigitalPy component registry).
- `Data Package service ... table keyword already exists` — logged at startup; the 8443 service still serves.
- `There was an exception sending a single response ... NoneType` on client connect.

Not verified: SSL client certificates / TAK client onboarding via data package, federation, long-running stability.

## Uninstall

```bash
docker compose down -v   # -v deletes the FTS database volume
```

## License

Scripts and patch: EPL-2.0 (same as upstream; see `LICENSE`, `NOTICE`).
