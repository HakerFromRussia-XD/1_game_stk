cmake_minimum_required(VERSION 3.12)

# libopusfile has an Autotools upstream build. Fluxara needs only the local
# file decoder (not HTTP), so keep a compact static CMake target alongside the
# vendored source and avoid external runtime dependencies on iOS.
add_library(fluxara_opusfile STATIC
    src/info.c
    src/internal.c
    src/opusfile.c
    src/stream.c)

target_include_directories(fluxara_opusfile
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(fluxara_opusfile PUBLIC opus ${OGGVORBIS_OGG_LIBRARY})

if(NOT WIN32)
    target_link_libraries(fluxara_opusfile PRIVATE m)
endif()
