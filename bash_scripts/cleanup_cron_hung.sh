#!/usr/bin/env bash
# Находит все процессы cron.py и убивает те, что живут >30 мин (1800 сек)

LOG=/var/log/cleanup_cron.log

# ADDED:
ENV_FILE="${CLEANUP_CRON_ENV_FILE:-/etc/integration_server/cleanup_cron.env}"

# ADDED:
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

# CHANGED:
DEBUG_CHAT_ID="${DEBUG_CHAT_ID:-}"
DEBUG_BOT_TOKEN="${DEBUG_BOT_TOKEN:-}"

MAX_AGE=1800
TERM_WAIT=10
KILL_WAIT=2

tg_send() {
  local text="$1"

  # ADDED:
  [[ -n "$DEBUG_BOT_TOKEN" && -n "$DEBUG_CHAT_ID" ]] || return 0

  command -v curl >/dev/null 2>&1 || return 0

  curl -sS -X POST "https://api.telegram.org/bot${DEBUG_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${DEBUG_CHAT_ID}" \
    --data-urlencode "text=${text}" \
    -d "parse_mode=HTML" >/dev/null
}

proc_stat() { ps -p "$1" -o stat= 2>/dev/null | tr -d ' '; }
proc_wchan() { cat /proc/"$1"/wchan 2>/dev/null || echo "-"; }

echo "$(date +'%F %T') --- START cleanup ---" >> "$LOG"
pids=($(pgrep -f '(/| )cron\.py( |$)'))
echo "$(date +'%F %T') found pids: ${pids[*]:-none}" >> "$LOG"

killed_report=""

for pid in "${pids[@]}"; do
  etime=$(ps -p "$pid" -o etimes= | tr -d ' ')
  stat=$(proc_stat "$pid")
  wchan=$(proc_wchan "$pid")

  if [[ "$etime" =~ ^[0-9]+$ ]] && [ "$etime" -gt "$MAX_AGE" ]; then
    if [[ "$stat" == Z* ]]; then
      line="$(date +'%F %T') zombie cron.py pid=$pid (age=${etime}s stat=${stat} wchan=${wchan})"
      echo "$line" >> "$LOG"
      killed_report+="$line"$'\n'
      continue
    fi

    if kill -TERM "$pid" 2>/dev/null; then
      echo "$(date +'%F %T') sent TERM pid=$pid (age=${etime}s stat=${stat} wchan=${wchan})" >> "$LOG"
      sleep "$TERM_WAIT"

      if kill -0 "$pid" 2>/dev/null; then
        stat2=$(proc_stat "$pid")
        wchan2=$(proc_wchan "$pid")

        if [[ "$stat2" == *D* ]]; then
          line="$(date +'%F %T') still alive (D-state) pid=$pid (age=${etime}s stat=${stat2} wchan=${wchan2})"
          echo "$line" >> "$LOG"
          killed_report+="$line"$'\n'
          continue
        fi

        kill -KILL "$pid" 2>/dev/null || true
        sleep "$KILL_WAIT"

        if kill -0 "$pid" 2>/dev/null; then
          stat3=$(proc_stat "$pid")
          wchan3=$(proc_wchan "$pid")
          line="$(date +'%F %T') still alive after KILL pid=$pid (age=${etime}s stat=${stat3} wchan=${wchan3})"
        else
          line="$(date +'%F %T') killed cron.py pid=$pid (age=${etime}s)"
        fi
      else
        line="$(date +'%F %T') killed cron.py pid=$pid (age=${etime}s)"
      fi

      echo "$line" >> "$LOG"
      killed_report+="$line"$'\n'
    else
      line="$(date +'%F %T') failed to signal pid=$pid (age=${etime}s stat=${stat} wchan=${wchan})"
      echo "$line" >> "$LOG"
      killed_report+="$line"$'\n'
    fi
  else
    echo "$(date +'%F %T') skipped pid=$pid (age=${etime}s stat=${stat} wchan=${wchan})" >> "$LOG"
  fi
done

if [[ -n "$killed_report" ]]; then
  tg_send "@avk_its
${killed_report}"
fi