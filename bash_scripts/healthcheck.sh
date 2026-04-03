#!/usr/bin/env bash
set -u -o pipefail

LOCK="/home/integration_server/.run/healthcheck.lock"
mkdir -p "/home/integration_server/.run"

LOG="/var/log/healthcheck/healthcheck.log"
mkdir -p "$(dirname "$LOG")"

ENV_FILE="${HEALTHCHECK_ENV_FILE:-/etc/integration_server/healthcheck.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

CHECK_SYSTEM_BOT_TOKEN="${CHECK_SYSTEM_BOT_TOKEN:-}"
CHECK_SYSTEM_CHAT_ID="${CHECK_SYSTEM_CHAT_ID:-}"
CHECK_SYSTEM_INFO_THREAD_ID="${CHECK_SYSTEM_INFO_THREAD_ID:-4}"
CHECK_SYSTEM_WARNING_THREAD_ID="${CHECK_SYSTEM_WARNING_THREAD_ID:-6}"
CHECK_SYSTEM_ERROR_THREAD_ID="${CHECK_SYSTEM_ERROR_THREAD_ID:-2}"

exec 9>"$LOCK"
flock -n 9 || exit 0

ts() { date -Is; }

tg_info=()
tg_errors=()

tg_send() {
  local level="$1"; shift
  local text="$*"

  # ADDED:
  [[ -n "$CHECK_SYSTEM_BOT_TOKEN" && -n "$CHECK_SYSTEM_CHAT_ID" ]] || return 0

  command -v curl >/dev/null 2>&1 || return 0

  local thread_id="$CHECK_SYSTEM_INFO_THREAD_ID"
  case "$level" in
    info) thread_id="$CHECK_SYSTEM_INFO_THREAD_ID" ;;
    warning) thread_id="$CHECK_SYSTEM_WARNING_THREAD_ID" ;;
    error) thread_id="$CHECK_SYSTEM_ERROR_THREAD_ID" ;;
  esac

  curl -fsS --max-time 5 \
    -d "chat_id=$CHECK_SYSTEM_CHAT_ID" \
    -d "message_thread_id=$thread_id" \
    --data-urlencode "text=$text" \
    "https://api.telegram.org/bot${CHECK_SYSTEM_BOT_TOKEN}/sendMessage" >/dev/null 2>&1 || true
}

log_line() {
  local level="$1"; shift
  local msg="$*"
  printf '%s level=%s %s\n' "$(ts)" "$level" "$msg" | tee -a "$LOG" >/dev/null
  case "$level" in
    info) logger -t healthcheck -p user.info -- "$msg" ;;
    warning) logger -t healthcheck -p user.warning -- "$msg" ;;
    error) logger -t healthcheck -p user.err -- "$msg" ;;
    *) logger -t healthcheck -p user.notice -- "$msg" ;;
  esac
}

fail=0

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    log_line warning "missing_cmd cmd=$cmd"
    tg_info+=("cmd $cmd: missing")
    return 1
  }
}

check_service() {
  local svc="$1"
  if systemctl is-active --quiet "$svc"; then
    log_line info "service=$svc status=active"
    tg_info+=("service $svc: ok")
  else
    log_line error "service=$svc status=DOWN"
    tg_info+=("service $svc: DOWN")
    tg_errors+=("service=$svc DOWN")
    fail=1
  fi
}

check_cmd() {
  local name="$1" timeout_s="$2"; shift 2
  if timeout "$timeout_s" "$@" >/dev/null 2>&1; then
    log_line info "check=$name ok=1"
    tg_info+=("check $name: ok")
  else
    log_line error "check=$name ok=0"
    tg_info+=("check $name: FAILED")
    tg_errors+=("check=$name failed")
    fail=1
  fi
}

check_disk() {
  local path="$1" max_pct="$2"
  local used
  used=$(df -P "$path" | awk 'NR==2{gsub("%","",$5);print $5}')
  if [[ "${used:-0}" -ge "$max_pct" ]]; then
    log_line error "disk path=$path used_pct=$used"
    tg_info+=("disk $path: ${used}% (limit ${max_pct}%)")
    tg_errors+=("disk $path ${used}%")
    fail=1
  else
    log_line info "disk path=$path used_pct=$used"
    tg_info+=("disk $path: ${used}%")
  fi
}

check_mem() {
  local max_pct="$1"
  local used
  used=$(free | awk '/Mem:/ {printf "%.0f", $3*100/$2}')
  if [[ "${used:-0}" -ge "$max_pct" ]]; then
    log_line error "mem used_pct=$used"
    tg_info+=("mem: ${used}% (limit ${max_pct}%)")
    tg_errors+=("mem ${used}%")
    fail=1
  else
    log_line info "mem used_pct=$used"
    tg_info+=("mem: ${used}%")
  fi
}

check_tcp() {
  local name="$1" host="$2" port="$3" timeout_s="${4:-3}"
  if timeout "$timeout_s" bash -c ">/dev/tcp/$host/$port" 2>/dev/null; then
    log_line info "tcp name=$name host=$host port=$port ok=1"
    tg_info+=("tcp $name: ok")
  else
    log_line error "tcp name=$name host=$host port=$port ok=0"
    tg_info+=("tcp $name: FAILED")
    tg_errors+=("tcp $name $host:$port")
    fail=1
  fi
}

check_http_ok() {
  local name="$1" url="$2" host="$3" timeout_s="${4:-3}"
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "$timeout_s" -H "Host: $host" "$url" 2>/dev/null || echo 000)"
  if [[ "$code" =~ ^2|^3 ]]; then
    log_line info "http name=$name code=$code url=$url host=$host"
    tg_info+=("http $name: ok ($code)")
  else
    log_line error "http name=$name code=$code url=$url host=$host"
    tg_info+=("http $name: FAILED ($code)")
    tg_errors+=("http $name $code")
    fail=1
  fi
}

for svc in cron nginx postgresql redis-server; do
  check_service "$svc"
done

require_cmd pg_isready && check_cmd "postgres_ready" 3 pg_isready -q || fail=1
require_cmd redis-cli && check_cmd "redis_ping" 3 redis-cli ping || fail=1

check_disk "/" 90
check_disk "/var" 90
check_mem 90

require_cmd curl && check_http_ok "scanner_contract" "http://127.0.0.1:80/scanner_contract/" "oauthbtr.stilkuhni.com" 3 || fail=1

tg_report="$(printf '%s\n' "${tg_info[@]}")"

if [[ "$fail" -eq 0 ]]; then
  log_line info "summary ok=1"
  tg_send info "healthcheck ok $(hostname)\n${tg_report}"
  exit 0
fi

log_line error "summary ok=0"
tg_send info "healthcheck FAILED $(hostname)\n${tg_report}"
tg_send error "healthcheck FAILED: ${tg_errors[*]}"
exit 1