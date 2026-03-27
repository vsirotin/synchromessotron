#!/usr/bin/env bash
# =============================================================================
# macOS platform test for telegram-cli
# Calls the native binary directly — no Python required.
#
# Scenarios (exit code + line count, no JSON parsing):
#   1. version
#   2. get-dialogs --limit=50 --outdir  (file created)
#   3. backup February 2026 — all media types
#   4. help
#   5. download-media (known voice message, msg 42389, Jan 7 2026)
#   6. send / edit / delete flow
#
# Usage (from dist/ — config.yaml must be present there):
#   cd telegram/telegram-cli/dist
#   bash ../tests/post_build/macos_test/macos_test.sh
#
# Or pass an explicit CLI path as the first argument:
#   bash .../macos_test.sh /path/to/telegram-cli
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="${1:-${SCRIPT_DIR}/../../../dist/telegram-cli}"
DIALOG="-4821106881"
PASS=0
FAIL=0
SEP="============================================================"

# ─── helpers ─────────────────────────────────────────────────────────────────
pass() { printf "[PASS] %s\n" "$*"; PASS=$(( PASS + 1 )); }
fail() { printf "[FAIL] %s\n" "$*"; FAIL=$(( FAIL + 1 )); }

# lines TEXT  →  number of lines (0 if empty)
lines() {
    if [ -z "$1" ]; then echo 0; return; fi
    printf '%s\n' "$1" | wc -l | tr -d ' \t'
}

# run_test LABEL CMD [ARGS...]
# Runs CMD ARGS, checks: exit 0 AND at least one line of output.
run_test() {
    local label="$1"; shift
    local out rc n
    out=$( "$@" 2>&1 )
    rc=$?
    n=$( lines "$out" )
    if [ "$rc" -eq 0 ] && [ "$n" -gt 0 ]; then
        pass "${label}  (${n} lines)"
    else
        fail "${label}  (rc=${rc}, ${n} lines)"
    fi
}

# check_file LABEL PATH  — pass if file exists, report line count
check_file() {
    local label="$1" path="$2" n=0
    if [ -f "$path" ]; then
        n=$( wc -l < "$path" | tr -d ' \t' )
        pass "${label}  (${n} lines)"
    else
        fail "${label}  (not found: ${path})"
    fi
}

# ─── setup ───────────────────────────────────────────────────────────────────
WORK="$( mktemp -d )"
trap 'rm -rf "${WORK}"' EXIT

echo "${SEP}"
echo "telegram-cli macOS platform tests"
printf "CLI:  %s\n" "${CLI}"
echo "${SEP}"
echo ""

# ─── Test 1: version ─────────────────────────────────────────────────────────
echo "[Test 1] version"
run_test "version" "${CLI}" version
echo ""

# ─── Test 2: get-dialogs to file ─────────────────────────────────────────────
echo "[Test 2] get-dialogs --outdir"
DLDIR="${WORK}/dialogs"
run_test "get-dialogs --limit=50 --outdir" \
    "${CLI}" get-dialogs --limit=50 "--outdir=${DLDIR}"
check_file "dialogs.json created" "${DLDIR}/dialogs.json"
echo ""

# ─── Test 3: backup February 2026 — all media types ─────────────────────────
echo "[Test 3] backup February 2026 — all media"
BKDIR="${WORK}/backup_feb"
run_test "backup Feb 2026 (--media --files --music --voice --links)" \
    "${CLI}" backup "${DIALOG}" \
        --limit=500 \
        --since=2026-02-01T00:00:00+00:00 \
        --upto=2026-02-28T23:59:59+00:00 \
        --media --files --music --voice --links \
        "--outdir=${BKDIR}"
# Confirm the dialog subdirectory was created
DDIR=$( find "${BKDIR}" -maxdepth 1 -type d -name "*-4821106881" 2>/dev/null | head -1 )
if [ -n "${DDIR}" ]; then
    pass "backup dialog directory created"
else
    fail "backup dialog directory not found under ${BKDIR}"
fi
echo ""

# ─── Test 4: help ────────────────────────────────────────────────────────────
echo "[Test 4] help"
run_test "help" "${CLI}" help
echo ""

# ─── Test 5: download-media ──────────────────────────────────────────────────
echo "[Test 5] download-media"
DLMDIR="${WORK}/dl"
mkdir -p "${DLMDIR}"
# Message 42389 = voice_2026-01-07_13-09-39.ogg  (dialog -4821106881)
run_test "download-media msg 42389" \
    "${CLI}" download-media "${DIALOG}" 42389 "--dest=${DLMDIR}"
echo ""

# ─── Test 6: send / edit / delete ────────────────────────────────────────────
echo "[Test 6] send / edit / delete"
SEND_OUT=$( "${CLI}" send "${DIALOG}" --text="macOS platform test — please ignore" 2>&1 )
SEND_RC=$?
SEND_N=$( lines "${SEND_OUT}" )

if [ "${SEND_RC}" -eq 0 ] && [ "${SEND_N}" -gt 0 ]; then
    pass "send  (${SEND_N} lines)"
    MSG_ID=$( printf '%s' "${SEND_OUT}" \
        | grep -oE '"id"[[:space:]]*:[[:space:]]*[0-9]+' \
        | grep -oE '[0-9]+$' \
        | head -1 )
    if [ -n "${MSG_ID}" ]; then
        run_test "edit  (id=${MSG_ID})" \
            "${CLI}" edit "${DIALOG}" "${MSG_ID}" \
                --text="macOS platform test — EDITED"
        run_test "delete  (id=${MSG_ID})" \
            "${CLI}" delete "${DIALOG}" "${MSG_ID}"
    else
        fail "edit  (message id not found in send output)"
        fail "delete  (skipped — no message id)"
    fi
else
    fail "send  (rc=${SEND_RC}, ${SEND_N} lines)"
    fail "edit  (skipped — send failed)"
    fail "delete  (skipped — send failed)"
fi

# ─── summary ─────────────────────────────────────────────────────────────────
echo ""
echo "${SEP}"
printf "Results:  PASS=%-3d  FAIL=%d\n" "${PASS}" "${FAIL}"
echo "${SEP}"
[ "${FAIL}" -eq 0 ]
