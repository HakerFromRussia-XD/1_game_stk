# Compile protected copies only in ReleaseProtected. No binary patching and
# no third-party ABI, Objective-C selector or on-disk resource-name changes.
function(fluxara_protect_release target)
    # Swift is enabled later than the initial build-type setup.
    if(CMAKE_Swift_COMPILER)
        set(CMAKE_Swift_FLAGS_RELEASEPROTECTED "${CMAKE_Swift_FLAGS_RELEASE}"
            CACHE STRING "Swift flags for protected release builds" FORCE)
    endif()
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    set(output "${CMAKE_BINARY_DIR}/protected")
    set(inputs)
    set(outputs "${output}/protected_strings.cpp" "${output}/protected_strings.hpp"
        "${output}/protected_symbols.hpp" "${output}/manifest.json"
        "${output}/states_screens/fluxara_event.hpp")
    foreach(screen home campaign kart race_setup race_result settings)
        set(source "src/states_screens/fluxara_${screen}_screen.cpp")
        list(APPEND inputs "${PROJECT_SOURCE_DIR}/${source}")
        list(APPEND outputs "${output}/${source}")
        get_target_property(sources ${target} SOURCES)
        list(REMOVE_ITEM sources "${source}" "${PROJECT_SOURCE_DIR}/${source}")
        set_property(TARGET ${target} PROPERTY SOURCES "${sources}")
        # Xcode requires the same source-file list in every configuration.
        # Generated wrappers include the untouched original outside protection.
        target_sources(${target} PRIVATE "${output}/${source}")
    endforeach()
    add_custom_command(OUTPUT ${outputs}
        COMMAND "${Python3_EXECUTABLE}" "${PROJECT_SOURCE_DIR}/tools/protect_fluxara_sources.py"
            --root "${PROJECT_SOURCE_DIR}" --output "${output}"
        DEPENDS ${inputs} "${PROJECT_SOURCE_DIR}/src/states_screens/fluxara_event.hpp"
            "${PROJECT_SOURCE_DIR}/tools/protect_fluxara_sources.py"
        COMMENT "Generate protected Fluxara sources and reversible symbol map"
        VERBATIM)
    add_custom_target(fluxara_protected_sources DEPENDS ${outputs})
    add_dependencies(${target} fluxara_protected_sources)
    target_sources(${target} PRIVATE "${output}/protected_strings.cpp")
    target_include_directories(${target} BEFORE PRIVATE
        "$<$<CONFIG:ReleaseProtected>:${output}>")
    target_compile_definitions(${target} PRIVATE
        "$<$<CONFIG:ReleaseProtected>:FLUXARA_PROTECTED_RELEASE=1>")
    target_compile_options(${target} PRIVATE
        "$<$<CONFIG:ReleaseProtected>:-fvisibility=hidden>"
        "$<$<AND:$<CONFIG:ReleaseProtected>,$<COMPILE_LANGUAGE:CXX,OBJCXX>>:-fvisibility-inlines-hidden>"
        "$<$<CONFIG:ReleaseProtected>:-fmacro-prefix-map=${PROJECT_SOURCE_DIR}=fluxara>"
        "$<$<CONFIG:ReleaseProtected>:-fmacro-prefix-map=${CMAKE_BINARY_DIR}=fluxara-build>"
        "$<$<CONFIG:ReleaseProtected>:-include${output}/protected_symbols.hpp>")
    # __FILE__ in bundled libraries is also part of the shipped executable.
    # Remap macro paths without changing third-party source or external ABI.
    get_all_targets(protection_targets "${PROJECT_SOURCE_DIR}")
    foreach(protection_target IN LISTS protection_targets)
        if(protection_target STREQUAL target)
            continue()
        endif()
        get_target_property(protection_type ${protection_target} TYPE)
        if(protection_type MATCHES "^(STATIC_LIBRARY|SHARED_LIBRARY|MODULE_LIBRARY|OBJECT_LIBRARY|EXECUTABLE)$")
            target_compile_options(${protection_target} PRIVATE
                "$<$<AND:$<CONFIG:ReleaseProtected>,$<COMPILE_LANGUAGE:C,CXX,OBJC,OBJCXX>>:-fmacro-prefix-map=${PROJECT_SOURCE_DIR}=fluxara>"
                "$<$<AND:$<CONFIG:ReleaseProtected>,$<COMPILE_LANGUAGE:C,CXX,OBJC,OBJCXX>>:-fmacro-prefix-map=${CMAKE_BINARY_DIR}=fluxara-build>")
        endif()
    endforeach()
    set_target_properties(${target} PROPERTIES
        XCODE_ATTRIBUTE_LLVM_LTO "$<IF:$<CONFIG:ReleaseProtected>,YES,NO>"
        XCODE_ATTRIBUTE_GCC_GENERATE_DEBUGGING_SYMBOLS YES
        XCODE_ATTRIBUTE_DEBUG_INFORMATION_FORMAT "dwarf-with-dsym"
        XCODE_ATTRIBUTE_DEPLOYMENT_POSTPROCESSING "$<IF:$<CONFIG:ReleaseProtected>,YES,NO>"
        XCODE_ATTRIBUTE_STRIP_INSTALLED_PRODUCT "$<IF:$<CONFIG:ReleaseProtected>,YES,NO>"
        XCODE_ATTRIBUTE_STRIP_STYLE "non-global"
        XCODE_ATTRIBUTE_DEAD_CODE_STRIPPING YES)
    if(CMAKE_GENERATOR MATCHES "Xcode")
        file(READ "${PROJECT_SOURCE_DIR}/cmake/FluxaraDrift.xcscheme" protected_scheme)
        string(REPLACE "buildConfiguration = \"Release\""
            "buildConfiguration = \"ReleaseProtected\"" protected_scheme "${protected_scheme}")
        string(REPLACE "@FLUXARA_XCODE_CONTAINER@" "${FLUXARA_XCODE_CONTAINER}"
            protected_scheme "${protected_scheme}")
        # Archive post-actions run after Xcode has collected the final product
        # and dSYM. Preserve mappings/generated lines outside the signed app.
        string(REGEX MATCH "<BuildableReference[^>]*>[\r\n ]*</BuildableReference>"
            protection_reference "${protected_scheme}")
        if(NOT protection_reference)
            message(FATAL_ERROR "Protected scheme has no archive environment buildable")
        endif()
        set(protection_script "set -e\n\"${Python3_EXECUTABLE}\" \"${PROJECT_SOURCE_DIR}/tools/save_fluxara_protection_snapshot.py\" --archive \"$ARCHIVE_PATH\" --build \"${CMAKE_BINARY_DIR}\" --root \"${PROJECT_SOURCE_DIR}\"\n")
        string(REPLACE "&" "&amp;" protection_script "${protection_script}")
        string(REPLACE "\"" "&quot;" protection_script "${protection_script}")
        string(REPLACE "<" "&lt;" protection_script "${protection_script}")
        string(REPLACE ">" "&gt;" protection_script "${protection_script}")
        string(REPLACE "\n" "&#10;" protection_script "${protection_script}")
        set(protection_action "      <PostActions>\n         <ExecutionAction ActionType=\"Xcode.IDEStandardExecutionActionsCore.ExecutionActionType.ShellScriptAction\">\n            <ActionContent title=\"Save Fluxara protection snapshot\" scriptText=\"${protection_script}\">\n               <EnvironmentBuildable>\n                  ${protection_reference}\n               </EnvironmentBuildable>\n            </ActionContent>\n         </ExecutionAction>\n      </PostActions>\n")
        string(REPLACE "   </ArchiveAction>" "${protection_action}   </ArchiveAction>"
            protected_scheme "${protected_scheme}")
        file(WRITE "${CMAKE_BINARY_DIR}/${PROJECT_NAME}.xcodeproj/xcshareddata/xcschemes/Fluxara Protected.xcscheme"
            "${protected_scheme}")
    endif()
endfunction()
