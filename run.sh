#!/usr/bin/env bash
# One-shot launcher for Lifesign (User Status & Health Telemetry Server).
# Single process, single port.
#
# Usage:  ./run.sh          # foreground
#         ./run.sh start    # background, pidfile in .run/
#         ./run.sh stop
#         ./run.sh status
#
# Port: 8764 (single port — /ingest + /query_all + /mcp all on it)
set -euo pipefail

cd "$(dirname "$0")"
export PATH="$PWD/.venv/bin:$PATH"

PORT="${USER_STATUS_PORT:-8764}"
RUN_DIR="$PWD/.run"
mkdir -p "$RUN_DIR"

start() {
  if [[ -f "$RUN_DIR/main.pid" ]] && kill -0 "$(cat "$RUN_DIR/main.pid")" 2>/dev/null; then
    echo "already running (pid $(cat "$RUN_DIR/main.pid"))"
  else
    nohup uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info \
      > "$RUN_DIR/main.log" 2>&1 &
    echo $! > "$RUN_DIR/main.pid"
    echo "started on :$PORT (pid $(cat "$RUN_DIR/main.pid"))"
  fi
}

stop() {
  local pidfile="$RUN_DIR/main.pid"
  if [[ -f "$pidfile" ]]; then
    kill "$(cat "$pidfile")" 2>/dev/null || true
    rm -f "$pidfile"
    echo "stopped"
  fi
}

status() {
  local pidfile="$RUN_DIR/main.pid"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "running (pid $(cat "$pidfile"))"
  else
    echo "stopped"
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) start ;;
esac