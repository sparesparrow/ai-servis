# Avoid multiple calls to find_package to append duplicated properties to the targets
include_guard()########### VARIABLES #######################################################################
#############################################################################################
set(jsoncpp_FRAMEWORKS_FOUND_RELEASE "") # Will be filled later
conan_find_apple_frameworks(jsoncpp_FRAMEWORKS_FOUND_RELEASE "${jsoncpp_FRAMEWORKS_RELEASE}" "${jsoncpp_FRAMEWORK_DIRS_RELEASE}")

set(jsoncpp_LIBRARIES_TARGETS "") # Will be filled later


######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
if(NOT TARGET jsoncpp_DEPS_TARGET)
    add_library(jsoncpp_DEPS_TARGET INTERFACE IMPORTED)
endif()

set_property(TARGET jsoncpp_DEPS_TARGET
             APPEND PROPERTY INTERFACE_LINK_LIBRARIES
             $<$<CONFIG:Release>:${jsoncpp_FRAMEWORKS_FOUND_RELEASE}>
             $<$<CONFIG:Release>:${jsoncpp_SYSTEM_LIBS_RELEASE}>
             $<$<CONFIG:Release>:>)

####### Find the libraries declared in cpp_info.libs, create an IMPORTED target for each one and link the
####### jsoncpp_DEPS_TARGET to all of them
conan_package_library_targets("${jsoncpp_LIBS_RELEASE}"    # libraries
                              "${jsoncpp_LIB_DIRS_RELEASE}" # package_libdir
                              "${jsoncpp_BIN_DIRS_RELEASE}" # package_bindir
                              "${jsoncpp_LIBRARY_TYPE_RELEASE}"
                              "${jsoncpp_IS_HOST_WINDOWS_RELEASE}"
                              jsoncpp_DEPS_TARGET
                              jsoncpp_LIBRARIES_TARGETS  # out_libraries_targets
                              "_RELEASE"
                              "jsoncpp"    # package_name
                              "${jsoncpp_NO_SONAME_MODE_RELEASE}")  # soname

# FIXME: What is the result of this for multi-config? All configs adding themselves to path?
set(CMAKE_MODULE_PATH ${jsoncpp_BUILD_DIRS_RELEASE} ${CMAKE_MODULE_PATH})

########## GLOBAL TARGET PROPERTIES Release ########################################
    set_property(TARGET JsonCpp::JsonCpp
                 APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                 $<$<CONFIG:Release>:${jsoncpp_OBJECTS_RELEASE}>
                 $<$<CONFIG:Release>:${jsoncpp_LIBRARIES_TARGETS}>
                 )

    if("${jsoncpp_LIBS_RELEASE}" STREQUAL "")
        # If the package is not declaring any "cpp_info.libs" the package deps, system libs,
        # frameworks etc are not linked to the imported targets and we need to do it to the
        # global target
        set_property(TARGET JsonCpp::JsonCpp
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     jsoncpp_DEPS_TARGET)
    endif()

    set_property(TARGET JsonCpp::JsonCpp
                 APPEND PROPERTY INTERFACE_LINK_OPTIONS
                 $<$<CONFIG:Release>:${jsoncpp_LINKER_FLAGS_RELEASE}>)
    set_property(TARGET JsonCpp::JsonCpp
                 APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                 $<$<CONFIG:Release>:${jsoncpp_INCLUDE_DIRS_RELEASE}>)
    # Necessary to find LINK shared libraries in Linux
    set_property(TARGET JsonCpp::JsonCpp
                 APPEND PROPERTY INTERFACE_LINK_DIRECTORIES
                 $<$<CONFIG:Release>:${jsoncpp_LIB_DIRS_RELEASE}>)
    set_property(TARGET JsonCpp::JsonCpp
                 APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS
                 $<$<CONFIG:Release>:${jsoncpp_COMPILE_DEFINITIONS_RELEASE}>)
    set_property(TARGET JsonCpp::JsonCpp
                 APPEND PROPERTY INTERFACE_COMPILE_OPTIONS
                 $<$<CONFIG:Release>:${jsoncpp_COMPILE_OPTIONS_RELEASE}>)

########## For the modules (FindXXX)
set(jsoncpp_LIBRARIES_RELEASE JsonCpp::JsonCpp)
