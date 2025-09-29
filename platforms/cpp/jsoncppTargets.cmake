# Load the debug and release variables
file(GLOB DATA_FILES "${CMAKE_CURRENT_LIST_DIR}/jsoncpp-*-data.cmake")

foreach(f ${DATA_FILES})
    include(${f})
endforeach()

# Create the targets for all the components
foreach(_COMPONENT ${jsoncpp_COMPONENT_NAMES} )
    if(NOT TARGET ${_COMPONENT})
        add_library(${_COMPONENT} INTERFACE IMPORTED)
        message(${jsoncpp_MESSAGE_MODE} "Conan: Component target declared '${_COMPONENT}'")
    endif()
endforeach()

if(NOT TARGET JsonCpp::JsonCpp)
    add_library(JsonCpp::JsonCpp INTERFACE IMPORTED)
    message(${jsoncpp_MESSAGE_MODE} "Conan: Target declared 'JsonCpp::JsonCpp'")
endif()
if(NOT TARGET jsoncpp_lib)
    add_library(jsoncpp_lib INTERFACE IMPORTED)
    set_property(TARGET jsoncpp_lib PROPERTY INTERFACE_LINK_LIBRARIES JsonCpp::JsonCpp)
endif()
if(NOT TARGET jsoncpp_static)
    add_library(jsoncpp_static INTERFACE IMPORTED)
    set_property(TARGET jsoncpp_static PROPERTY INTERFACE_LINK_LIBRARIES JsonCpp::JsonCpp)
endif()
if(NOT TARGET jsoncpp_lib_static)
    add_library(jsoncpp_lib_static INTERFACE IMPORTED)
    set_property(TARGET jsoncpp_lib_static PROPERTY INTERFACE_LINK_LIBRARIES JsonCpp::JsonCpp)
endif()
# Load the debug and release library finders
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_LIST_DIR}/jsoncpp-Target-*.cmake")

foreach(f ${CONFIG_FILES})
    include(${f})
endforeach()