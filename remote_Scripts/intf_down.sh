#!/bin/bash
# intf_down.sh  <interface>  [soft_failure_bool]  [start_epoch]
#
#   <interface>         eth2, ens3, ...
#   [soft_failure_bool] 0|1  (default 0 → hard failure)
#   [start_epoch]       absolute Unix-epoch seconds[.ms] to begin
#
#   Soft failure uses nftables:
#       table netdev starvation
#         chain <intf>_in (ingress) { drop }
#
#   Restore later with:
#       sudo nft delete table netdev starvation
#
# -------------------------------------------------------------------------

set -euo pipefail
LOGFILE="/home/rocky/intf_down.log"

timestamp() { date +"%Y/%m/%d %H:%M:%S.%6N"; }
epoch_ms()  { date +%s.%3N; }

TIME_WRITTEN=0
write_ts_once() {
    if [[ $TIME_WRITTEN -eq 0 ]]; then
        printf "%s\n" "$(timestamp)" > "$LOGFILE"
        TIME_WRITTEN=1
    fi
}

fail() {
    write_ts_once
    echo "ERROR: $1" >> "$LOGFILE"
    echo "ERROR: $1" >&2
    exit 1
}

# ─────────── 0. Parse arguments ──────────────────────────────────────────
[[ $# -ge 1 ]] || fail "Usage: $0 <interface> [soft_bool] [start_epoch]"

INTF="$1"
SOFT="${2:-0}"
START_AT="${3:-}"

case "$SOFT" in
    1|true|yes|y) SOFT=1 ;;
    0|false|no|n|"") SOFT=0 ;;
    *) fail "Invalid soft_failure_bool '$2'" ;;
esac

# ─────────── 1. Optional wait-until ──────────────────────────────────────
if [[ -n "$START_AT" ]]; then
    now=$(epoch_ms)
    wait=$(awk -v t="$START_AT" -v n="$now" 'BEGIN {print t-n}')
    if (( $(awk 'BEGIN {print ('"$wait"' > 0)}') )); then
        sleep "$wait" || fail "sleep interrupted"
    fi
fi

# ─────────── 2. Timestamp (post-wait) ────────────────────────────────────
write_ts_once

# ─────────── 3. Inject failure ───────────────────────────────────────────
if [[ $SOFT -eq 1 ]]; then
    # --- soft: drop every frame that arrives on INTF --------------------
    # remove any old leftovers (ignore if table doesn’t exist)
    sudo nft delete table netdev starvation 2>/dev/null || true

    # create fresh table, chain, and drop rule
    sudo nft add table netdev starvation                                    || fail "nft add table failed"
    sudo nft add chain netdev starvation ${INTF}_in \
        '{ type filter hook ingress device "'"$INTF"'" priority 0; policy accept; }' \
                                                                            || fail "nft add chain failed"
    sudo nft add rule netdev starvation ${INTF}_in drop                     || fail "nft add rule failed"

else
    # --- hard: administratively down the link ---------------------------
    sudo ip link set dev "$INTF" down                                       || fail "ip link down failed"
fi

exit 0   # success → only the timestamp line is in the log
