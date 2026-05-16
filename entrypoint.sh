#!/bin/bash
# =============================================================================
# entrypoint.sh
#
# QLever indexing and server startup. Runs as the `qlever` service.
#
# By the time this runs, docker-compose has already waited for the
# `ontology-prep` service to exit successfully (condition:
# service_completed_successfully), so the .nq files are guaranteed to exist
# in /data/ontologies/converted/.
#
# Note on `qlever ui`:
#   The UI is NOT started here. Launching it from inside this container would
#   require Docker-in-Docker. The qlever-ui service in docker-compose.yml
#   handles it and talks to this container on port 7001 via the shared network.
# =============================================================================

set -euo pipefail

CONVERTED_DIR="/data/ontologies/converted"
MARKER="/data/.prep_done"

# ---------------------------------------------------------------------------
# Safety check — abort clearly if prep did not complete
# ---------------------------------------------------------------------------
if [[ ! -f "$MARKER" ]]; then
    echo "ERROR: preparation marker not found at $MARKER"
    echo "       Run the ontology-prep service first:"
    echo "       docker compose run --rm ontology-prep"
    exit 1
fi

cd "$CONVERTED_DIR"

# Copy Qleverfile from the safe baked location (not from /data, which is a
# bind mount that would have shadowed a Qleverfile placed there at build time).
#
# NOTE: `qlever setup-config default` is intentionally NOT called here.
# It refuses to run if a Qleverfile already exists and exits with code 1,
# causing a crash loop. More importantly, it would overwrite your custom
# settings (input files, index name, etc.) with generic defaults.
# The qlever CLI already applies the one thing setup-config would add on top —
# SYSTEM = native — automatically via the QLEVER_IS_RUNNING_IN_CONTAINER
# environment variable that the adfreiburg/qlever base image sets.
cp /etc/qlever/Qleverfile ./Qleverfile

echo "=== [1/2] qlever index --overwrite-existing --parallel-parsing false ==="
qlever index --overwrite-existing --parallel-parsing false

echo ""
echo "=== [2/2] qlever start ==="
qlever start

echo ""
echo "=== QLever SPARQL endpoint is up on port 7001 ==="
echo "    SPARQL endpoint : http://localhost:7001"
echo "    QLever UI       : http://localhost:8176"
echo ""

# Keep the container alive and stream the server log.
# qlever start daemonises ServerMain, so without this the container would exit.
SERVER_LOG="$(ls -t "$CONVERTED_DIR"/*.server-log 2>/dev/null | head -1 || true)"
if [[ -n "$SERVER_LOG" ]]; then
    echo "Tailing server log: $SERVER_LOG"
    tail -f "$SERVER_LOG"
else
    echo "Server log not found at expected path; keeping container alive."
    tail -f /dev/null
fi
