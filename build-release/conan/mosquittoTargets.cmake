# Load the debug and release variables
file(GLOB DATA_FILES "${CMAKE_CURRENT_LIST_DIR}/mosquitto-*-data.cmake")

foreach(f ${DATA_FILES})
    include(${f})
endforeach()

# Create the targets for all the components
foreach(_COMPONENT ${mosquitto_COMPONENT_NAMES} )
    if(NOT TARGET ${_COMPONENT})
        add_library(${_COMPONENT} INTERFACE IMPORTED)
        message(${mosquitto_MESSAGE_MODE} "Conan: Component target declared '${_COMPONENT}'")
    endif()
endforeach()

if(NOT TARGET mosquitto::mosquitto)
    add_library(mosquitto::mosquitto INTERFACE IMPORTED)
    message(${mosquitto_MESSAGE_MODE} "Conan: Target declared 'mosquitto::mosquitto'")
endif()
# Load the debug and release library finders
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_LIST_DIR}/mosquitto-Target-*.cmake")

foreach(f ${CONFIG_FILES})
    include(${f})
endforeach()