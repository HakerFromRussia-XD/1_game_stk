#!/bin/zsh
# Measure the actual iOS Simulator FPS of every curated Fluxara event.
# The script targets only the already-installed Simulator build: it never
# selects a device SDK and does not rebuild, install, or save high scores.
set -euo pipefail

SIMULATOR_ID="${FLUXARA_SIMULATOR_ID:-FB96D76C-E9A8-4DCF-ABA9-7E270D079049}"
BUNDLE_ID="io.fluxara.drift"
ROOT="${0:A:h:h}"
MANIFEST="${ROOT}/iosApp/FluxaraResources/fluxara-campaign.xml"
REPORT="${FLUXARA_PERFORMANCE_REPORT:-/private/tmp/fluxara-performance-probe.tsv}"
SAMPLE_SECONDS="${FLUXARA_PERFORMANCE_SAMPLE_SECONDS:-4}"
START_INDEX="${FLUXARA_PERFORMANCE_START_INDEX:-1}"
LIMIT="${FLUXARA_PERFORMANCE_LIMIT:-0}"
APPEND="${FLUXARA_PERFORMANCE_APPEND:-0}"

[[ -f "${MANIFEST}" ]] || { print -u2 "Missing ${MANIFEST}"; exit 2; }
[[ "${SAMPLE_SECONDS}" -gt 0 ]] || { print -u2 "SAMPLE_SECONDS must be positive"; exit 2; }

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

if [[ "${APPEND}" != "1" || ! -f "${REPORT}" ]]; then
    print $'index\tevent\tmode\ttrack\tsamples\tmin_fps\tavg_fps\tmax_fps\tstatus' > "${REPORT}"
fi

integer source_index=0 measured=0 failures=0
while IFS='|' read -r event_id mode track; do
    (( ++source_index ))
    (( source_index < START_INDEX )) && continue
    (( LIMIT > 0 && measured >= LIMIT )) && break
    (( ++measured ))

    mode_command="$(mode_args "${mode}")" || {
        print -u2 "${event_id}\tunsupported-mode=${mode}"
        print "${source_index}\t${event_id}\t${mode}\t${track}\t0\t0\t0\t0\tunsupported" >> "${REPORT}"
        (( ++failures ))
        continue
    }
    args=( ${(z)mode_command} )
    launch="$(xcrun simctl launch --terminate-running-process "${SIMULATOR_ID}" "${BUNDLE_ID}" \
        --no-start-screen --no-high-scores --fps-debug \
        "--fluxara-event=${event_id}" "--track=${track}" "${args[@]}")" || {
        print -u2 "${event_id}\tlaunch-failed"
        print "${source_index}\t${event_id}\t${mode}\t${track}\t0\t0\t0\t0\tlaunch-failed" >> "${REPORT}"
        (( ++failures ))
        continue
    }
    pid="${launch##*: }"
    sleep "${SAMPLE_SECONDS}"
    # The engine's wall-clock debug counter can emit a one-frame
    # multi-million FPS spike when the simulator clock resolution rounds
    # below one microsecond. Such a value is not a rendered-frame rate;
    # retain the physically meaningful range around the configured 120Hz
    # ceiling while still preserving a genuine 1 FPS regression.
    metrics="$(
        xcrun simctl spawn "${SIMULATOR_ID}" log show --last 90s --style compact \
            --predicate "processID == ${pid}" 2>/dev/null | { rg 'fps ' || true; } | \
            tail -n 600 | awk '{for (i=1; i<NF; i++) if ($i=="fps") {v=$(i+1)+0; if(v>=1 && v<=240) {n++; s+=v; if(n==1||v<min)min=v; if(v>max)max=v}}} END {if(n) printf("%d\t%.1f\t%.1f\t%.1f",n,min,s/n,max)}'
    )"
    if [[ -z "${metrics}" ]]; then
        print -u2 "${event_id}\tno-fps-samples pid=${pid}"
        print "${source_index}\t${event_id}\t${mode}\t${track}\t0\t0\t0\t0\tno-fps" >> "${REPORT}"
        (( ++failures ))
    else
        print "${source_index}\t${event_id}\t${mode}\t${track}\t${metrics}\tok" >> "${REPORT}"
        print "${event_id}\t${metrics}"
    fi
done < <(ruby -rrexml/document -e '
  doc=REXML::Document.new(File.read(ARGV.fetch(0)))
  doc.elements.each("campaign/event") do |event|
    puts [event.attributes["id"], event.attributes["mode"],
          event.attributes["track"]].join("|")
  end
' "${MANIFEST}")

print "FLUXARA_PERFORMANCE_PROBE events=${measured} failures=${failures} report=${REPORT}"
(( failures == 0 ))
