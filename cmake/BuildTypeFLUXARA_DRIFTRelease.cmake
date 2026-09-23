# Build type FLUXARA_DRIFTRelease is similar to Release provided by CMake,
# but it uses a lower optimization level

set(CMAKE_CXX_FLAGS_FLUXARA_DRIFTRELEASE "-O2 -DNDEBUG" CACHE STRING
    "Flags used by the C++ compiler during FLUXARA_DRIFT release builds."
    FORCE)
set(CMAKE_C_FLAGS_FLUXARA_DRIFTRELEASE "-O2 -DNDEBUG" CACHE STRING
    "Flags used by the C compiler during FLUXARA_DRIFT release builds."
    FORCE)
set(CMAKE_EXE_LINKER_FLAGS_FLUXARA_DRIFTRELEASE
    "" CACHE STRING
    "Flags used for linking binaries during FLUXARA_DRIFT release builds."
    FORCE)
set(CMAKE_SHARED_LINKER_FLAGS_FLUXARA_DRIFTRELEASE
    "" CACHE STRING
    "Flags used by the shared libraries linker during FLUXARA_DRIFT release builds."
    FORCE)

mark_as_advanced(
    CMAKE_CXX_FLAGS_FLUXARA_DRIFTRELEASE
    CMAKE_C_FLAGS_FLUXARA_DRIFTRELEASE
    CMAKE_EXE_LINKER_FLAGS_FLUXARA_DRIFTRELEASE
    CMAKE_SHARED_LINKER_FLAGS_FLUXARA_DRIFTRELEASE)

set(CMAKE_BUILD_TYPE "${CMAKE_BUILD_TYPE}" CACHE STRING
    "Choose the type of build, options are: None Debug Release RelWithDebInfo MinSizeRel FLUXARA_DRIFTRelease."
    FORCE)
