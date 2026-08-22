#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${ROOT_DIR}/load_tests/results"
PORT="${FINSIGHT_LOAD_PORT:-8010}"
DURATION="${FINSIGHT_LOAD_DURATION:-20s}"
USERS="${FINSIGHT_LOAD_USERS:-50}"
SPAWN_RATE="${FINSIGHT_LOAD_SPAWN_RATE:-10}"

mkdir -p "${OUTPUT_DIR}"
rm -f "${OUTPUT_DIR}"/finsight_load_*.csv "${OUTPUT_DIR}"/load-test.db

export FINSIGHT_ENV=development
export FINSIGHT_DATABASE_URL="sqlite:///${OUTPUT_DIR}/load-test.db"
export PYTHONPATH="${ROOT_DIR}/load_tests:${ROOT_DIR}/api:${ROOT_DIR}/src"

uvicorn load_test_app:app --host 127.0.0.1 --port "${PORT}" >"${OUTPUT_DIR}/api.log" 2>&1 &
API_PID=$!
cleanup() {
  kill "${API_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for attempt in {1..30}; do
  if curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" >/dev/null; then
    break
  fi
  sleep 0.5
done

curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" >/dev/null
locust \
  -f "${ROOT_DIR}/load_tests/locustfile.py" \
  --host "http://127.0.0.1:${PORT}" \
  --headless \
  --users "${USERS}" \
  --spawn-rate "${SPAWN_RATE}" \
  --run-time "${DURATION}" \
  --csv "${OUTPUT_DIR}/finsight_load" \
  --html "${OUTPUT_DIR}/finsight_load_report.html"

echo "Load-test artifacts: ${OUTPUT_DIR}"
