#!/bin/zsh
# Runtime smoke probe for the curated Fluxara campaign.  It deliberately
# targets only the known iOS Simulator and the already-built simulator bundle.
set -euo pipefail

SIMULATOR_ID="${FLUXARA_SIMULATOR_ID:-FB96D76C-E9A8-4DCF-ABA9-7E270D079049}"
BUNDLE_ID="io.fluxara.drift"
ROOT="${0:A:h:h}"
MANIFEST="${ROOT}/iosApp/FluxaraResources/fluxara-campaign.xml"
OUTPUT_DIR="${FLUXARA_PROBE_OUTPUT_DIR:-/tmp/fluxara-event-probe}"
INITIAL_SETTLE_SECONDS="${FLUXARA_PROBE_INITIAL_SETTLE_SECONDS:-1}"
MIN_GAMEPLAY_SECONDS="${FLUXARA_PROBE_MIN_GAMEPLAY_SECONDS:-8}"
READY_TIMEOUT_SECONDS="${FLUXARA_PROBE_READY_TIMEOUT_SECONDS:-35}"
SIMCTL_TIMEOUT_SECONDS="${FLUXARA_SIMCTL_TIMEOUT_SECONDS:-12}"
LIMIT="${FLUXARA_PROBE_LIMIT:-0}"
START_INDEX="${FLUXARA_PROBE_START_INDEX:-1}"

[[ -f "${MANIFEST}" ]] || { print -u2 "Missing ${MANIFEST}"; exit 2; }
mkdir -p "${OUTPUT_DIR}"

mode_args() {
    case "$1" in
        normal) print -- "--mode=0 --numkarts=1 --laps=1" ;;
        time_trial|ghost_geometry) print -- "--mode=1 --numkarts=1 --laps=1" ;;
        follow_leader) print -- "--mode=4 --numkarts=3" ;;
        three_strikes) print -- "--mode=6 --numkarts=3" ;;
        free_for_all) print -- "--mode=2 --battle-mode=0 --numkarts=3" ;;
        soccer) print -- "--mode=3 --numkarts=3" ;;
        capture_the_flag) print -- "--mode=5 --battle-mode=1 --numkarts=1 --capture-limit=3 --time-limit=180" ;;
        egg_hunt) print -- "--mode=8 --numkarts=1" ;;
        lap_trial) print -- "--mode=7 --numkarts=1 --laps=1" ;;
        *) return 1 ;;
    esac
}

wait_for_active_frame() {
    local event_id="$1"
    local track="$2"
    local frame="$3"
    local candidate="${frame}.loading"
    local failed="${frame%.png}.failed.png"
    integer elapsed=0
    integer saw_expected_process=0

    sleep "${INITIAL_SETTLE_SECONDS}"
    while (( elapsed < READY_TIMEOUT_SECONDS )); do
        # A stale SpringBoard or a queued launch can still produce a bright
        # image.  The exact immediate-race process is the minimum contract
        # for calling this event launched; without it, a screenshot is not
        # runtime evidence for the requested event and track.
        # Do not use grep -q here: with pipefail, grep's early exit gives ps
        # SIGPIPE and turns a successful process match into a false failure.
        if ! ps -axo command= | grep -F -- \
            "Fluxara Drift.app/Fluxara Drift --no-start-screen --fluxara-event=${event_id} --track=${track}" >/dev/null; then
            # `simctl launch` completes before UIKit has necessarily spawned
            # the app binary.  Wait for a cold start instead of reporting all
            # following events as failures after an otherwise valid launch.
            # Once the exact process has appeared, its disappearance remains
            # a real failure: a loading splash cannot pass as gameplay.
            if (( saw_expected_process )); then
                return 2
            fi
            sleep 1
            (( ++elapsed ))
            continue
        fi
        saw_expected_process=1
        if ! gtimeout "${SIMCTL_TIMEOUT_SECONDS}" \
            xcrun simctl io "${SIMULATOR_ID}" screenshot "${candidate}" \
            >/dev/null 2>&1; then
            return 3
        fi

        # All racing modes must have completed the requested portrait→landscape
        # transition.  A portrait image here is a menu, splash, or result
        # screen; accepting it would turn an immediately aborted event into a
        # false pass.
        local dimensions="$(magick identify -format '%w %h' "${candidate}" 2>/dev/null)"
        local width="${dimensions%% *}"
        local height="${dimensions##* }"
        if [[ -z "${width}" || -z "${height}" || ${width} -le ${height} ]]; then
            sleep 1
            (( ++elapsed ))
            continue
        fi

        # The Fluxara splash is dark navy (RGB sum about 72 after reducing
        # the complete frame to one pixel); a rendered race/result frame is
        # materially brighter. This prevents a launch from being accepted
        # merely because a screenshot could be captured during loading.
        integer brightness="$(magick "${candidate}" -resize '1x1!' txt:- |
            tail -n 1 |
            sed -E 's/.*\(([0-9]+),([0-9]+),([0-9]+),[0-9]+\).*/\1 \2 \3/' |
            awk '{print $1 + $2 + $3}')"
        if (( brightness >= 100 )); then
            # A bright landscape splash is still not a race.  Keep the
            # requested event alive through a gameplay-sized interval and
            # capture a second frame, so a launch that immediately returns to
            # SpringBoard cannot be reported as one of the 50 working events.
            sleep "${MIN_GAMEPLAY_SECONDS}"
            if ! ps -axo command= | grep -F -- \
                "Fluxara Drift.app/Fluxara Drift --no-start-screen --fluxara-event=${event_id} --track=${track}" >/dev/null; then
                return 2
            fi
            if ! gtimeout "${SIMCTL_TIMEOUT_SECONDS}" \
                xcrun simctl io "${SIMULATOR_ID}" screenshot "${candidate}" \
                >/dev/null 2>&1; then
                return 3
            fi
            dimensions="$(magick identify -format '%w %h' "${candidate}" 2>/dev/null)"
            width="${dimensions%% *}"
            height="${dimensions##* }"
            if [[ -n "${width}" && -n "${height}" && ${width} -gt ${height} ]]; then
                mv "${candidate}" "${frame}"
                return 0
            fi
        fi
        sleep 1
        (( ++elapsed ))
    done
    # Keep a diagnostic image without letting its name masquerade as a
    # successfully activated event.  A complete 50-event run is therefore
    # exactly 50 ordinary *.png frames and no *.failed.png diagnostics.
    [[ -f "${candidate}" ]] && mv "${candidate}" "${failed}"
    return 1
}

integer source_index=0 index=0 failures=0
while IFS='|' read -r event_id mode track; do
    (( ++source_index ))
    if (( source_index < START_INDEX )); then
        continue
    fi
    if (( LIMIT > 0 && index >= LIMIT )); then
        break
    fi
    (( ++index ))
    mode_command="$(mode_args "${mode}")" || {
        print -u2 "${event_id}\tunsupported-mode=${mode}"
        (( ++failures ))
        continue
    }
    args=( ${(z)mode_command} )
    if ! launch_error="$(gtimeout "${SIMCTL_TIMEOUT_SECONDS}" \
        xcrun simctl launch --terminate-running-process "${SIMULATOR_ID}" \
        "${BUNDLE_ID}" --no-start-screen "--fluxara-event=${event_id}" \
        "--track=${track}" "${args[@]}" 2>&1 >/dev/null)"; then
        # This is a host Simulator failure, not an event failure.  Continuing
        # to issue 47 more launch requests only prolongs recovery and makes a
        # short runtime probe needlessly disruptive.
        if [[ "${launch_error}" == *"CoreSimulatorService" ||
              "${launch_error}" == *"Unable to locate device set" ||
              "${launch_error}" == *"Connection refused" ]]; then
            print -u2 "Simulator service unavailable; aborting event probe."
            exit 3
        fi
        print -u2 "${event_id}\tlaunch-failed"
        (( ++failures ))
        continue
    fi
    frame="${OUTPUT_DIR}/${(l:2::0:)source_index}-${event_id}.png"
    if wait_for_active_frame "${event_id}" "${track}" "${frame}"; then
        print "${event_id}\t${mode}\t${track}\t${frame}"
    else
        print -u2 "${event_id}\tinactive-or-screenshot-failed"
        (( ++failures ))
    fi
done < <(ruby -rrexml/document -e '
  doc=REXML::Document.new(File.read(ARGV.fetch(0)))
  doc.elements.each("campaign/event") do |event|
    puts [event.attributes["id"], event.attributes["mode"],
          event.attributes["track"]].join("|")
  end
' "${MANIFEST}")

print "FLUXARA_EVENT_PROBE start=${START_INDEX} events=${index} failures=${failures} frames=${OUTPUT_DIR}"
(( failures == 0 ))
