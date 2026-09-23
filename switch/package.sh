nacptool --create "FluxaraDrift" "Many People" "${PROJECT_VERSION}" control.nacp
elf2nro bin/fluxaradrift.elf bin/fluxara_drift.nro --nacp=control.nacp --icon=../switch/fluxaradrift_256.jpg
