@echo off

if %PROCESSOR_ARCHITECTURE%==x86 (
Pushd %~dp0\fluxara_drift-code\build-i686\bin\
fluxaradrift.exe
popd
)

if %PROCESSOR_ARCHITECTURE%==AMD64 (
Pushd %~dp0\fluxara_drift-code\build-x86_64\bin\
fluxaradrift.exe
popd
)

if %PROCESSOR_ARCHITECTURE%==ARM64 (
Pushd %~dp0\fluxara_drift-code\build-aarch64\bin\
fluxaradrift.exe
popd
)

if %PROCESSOR_ARCHITECTURE%==ARM (
Pushd %~dp0\fluxara_drift-code\build-armv7\bin\
fluxaradrift.exe
popd
)
