# A separate, reproducible distribution configuration. Debug and Release
# retain their existing behaviour, including diagnostics.
if(IOS)
    if(CMAKE_CONFIGURATION_TYPES)
        list(APPEND CMAKE_CONFIGURATION_TYPES ReleaseProtected)
        list(REMOVE_DUPLICATES CMAKE_CONFIGURATION_TYPES)
        set(CMAKE_CONFIGURATION_TYPES "${CMAKE_CONFIGURATION_TYPES}" CACHE STRING
            "Available build configurations" FORCE)
    endif()
    foreach(language C CXX OBJC OBJCXX ASM Swift)
        set(CMAKE_${language}_FLAGS_RELEASEPROTECTED
            "${CMAKE_${language}_FLAGS_RELEASE}" CACHE STRING
            "${language} flags for protected release builds")
    endforeach()
    foreach(kind EXE SHARED MODULE STATIC)
        set(CMAKE_${kind}_LINKER_FLAGS_RELEASEPROTECTED
            "${CMAKE_${kind}_LINKER_FLAGS_RELEASE}" CACHE STRING
            "${kind} linker flags for protected release builds")
    endforeach()
endif()
