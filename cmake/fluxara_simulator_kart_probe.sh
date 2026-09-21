#!/bin/zsh
# Starts one runtime garage session for the curated Fluxara karts.
#
# The actual 15-kart visual check must remain in this single session: use the
# garage previous/next buttons to move through the models.  Starting the app
# once per kart is both much slower and does not exercise the real selector.
# UI automation is deliberately kept outside this shell helper, because it
# must use the Simulator's visible controls rather than a test-only launch
# argument.  This helper never selects a device SDK or destination.
set -euo pipefail

SIMULATOR_ID="${FLUXARA_SIMULATOR_ID:-FB96D76C-E9A8-4DCF-ABA9-7E270D079049}"
BUNDLE_ID="io.fluxara.drift"
ROOT="${0:A:h:h}"
KART_ROOT="${ROOT}/iosApp/FluxaraResources/karts"
# An optional initial kart is useful while diagnosing one model, but it never
# changes the one-session rule for the complete visual pass.
INITIAL_KART="${FLUXARA_KART_PROBE_INITIAL_KART:-}"

[[ -d "${KART_ROOT}" ]] || { print -u2 "Missing ${KART_ROOT}"; exit 2; }

typeset -a karts
for descriptor in "${KART_ROOT}"/fluxara-*/kart.xml; do
    [[ -f "${descriptor}" ]] || continue
    karts+=("${descriptor:h:t}")
done
karts=(${(on)karts})
(( ${#karts} == 15 )) || {
    print -u2 "Expected 15 Fluxara karts, found ${#karts}"
    exit 2
}

typeset -a launch_args
launch_args=(--fluxara-screen=garage)
if [[ -n "${INITIAL_KART}" ]]; then
    [[ " ${karts[*]} " == *" ${INITIAL_KART} "* ]] || {
        print -u2 "Unknown Fluxara kart: ${INITIAL_KART}"
        exit 2
    }
    launch_args+=("--kart=${INITIAL_KART}")
fi

xcrun simctl launch --terminate-running-process "${SIMULATOR_ID}" \
    "${BUNDLE_ID}" "${launch_args[@]}" >/dev/null

print "FLUXARA_KART_SESSION karts=15 initial=${INITIAL_KART:-saved-default}"
print "Use the visible previous/next controls to inspect every kart in this one session."
