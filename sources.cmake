# Modify this file to change the last-modified date when you add/remove a file.
# This will then trigger a new cmake run automatically. 
file(GLOB_RECURSE FLUXARA_DRIFT_HEADERS RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "src/*.hpp")
file(GLOB_RECURSE FLUXARA_DRIFT_SOURCES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "src/*.cpp")
file(GLOB_RECURSE FLUXARA_DRIFT_SHADERS RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "data/shaders/*")
file(GLOB_RECURSE FLUXARA_DRIFT_RESOURCES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "${PROJECT_BINARY_DIR}/tmp/*.rc")
