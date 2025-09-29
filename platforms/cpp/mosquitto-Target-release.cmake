# Avoid multiple calls to find_package to append duplicated properties to the targets
include_guard()########### VARIABLES #######################################################################
#############################################################################################
set(mosquitto_FRAMEWORKS_FOUND_RELEASE "") # Will be filled later
conan_find_apple_frameworks(mosquitto_FRAMEWORKS_FOUND_RELEASE "${mosquitto_FRAMEWORKS_RELEASE}" "${mosquitto_FRAMEWORK_DIRS_RELEASE}")

set(mosquitto_LIBRARIES_TARGETS "") # Will be filled later


######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
if(NOT TARGET mosquitto_DEPS_TARGET)
    add_library(mosquitto_DEPS_TARGET INTERFACE IMPORTED)
endif()

set_property(TARGET mosquitto_DEPS_TARGET
             APPEND PROPERTY INTERFACE_LINK_LIBRARIES
             $<$<CONFIG:Release>:${mosquitto_FRAMEWORKS_FOUND_RELEASE}>
             $<$<CONFIG:Release>:${mosquitto_SYSTEM_LIBS_RELEASE}>
             $<$<CONFIG:Release>:openssl::openssl;mosquitto::libmosquitto>)

####### Find the libraries declared in cpp_info.libs, create an IMPORTED target for each one and link the
####### mosquitto_DEPS_TARGET to all of them
conan_package_library_targets("${mosquitto_LIBS_RELEASE}"    # libraries
                              "${mosquitto_LIB_DIRS_RELEASE}" # package_libdir
                              "${mosquitto_BIN_DIRS_RELEASE}" # package_bindir
                              "${mosquitto_LIBRARY_TYPE_RELEASE}"
                              "${mosquitto_IS_HOST_WINDOWS_RELEASE}"
                              mosquitto_DEPS_TARGET
                              mosquitto_LIBRARIES_TARGETS  # out_libraries_targets
                              "_RELEASE"
                              "mosquitto"    # package_name
                              "${mosquitto_NO_SONAME_MODE_RELEASE}")  # soname

# FIXME: What is the result of this for multi-config? All configs adding themselves to path?
set(CMAKE_MODULE_PATH ${mosquitto_BUILD_DIRS_RELEASE} ${CMAKE_MODULE_PATH})

########## COMPONENTS TARGET PROPERTIES Release ########################################

    ########## COMPONENT mosquitto::libmosquittopp #############

        set(mosquitto_mosquitto_libmosquittopp_FRAMEWORKS_FOUND_RELEASE "")
        conan_find_apple_frameworks(mosquitto_mosquitto_libmosquittopp_FRAMEWORKS_FOUND_RELEASE "${mosquitto_mosquitto_libmosquittopp_FRAMEWORKS_RELEASE}" "${mosquitto_mosquitto_libmosquittopp_FRAMEWORK_DIRS_RELEASE}")

        set(mosquitto_mosquitto_libmosquittopp_LIBRARIES_TARGETS "")

        ######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
        if(NOT TARGET mosquitto_mosquitto_libmosquittopp_DEPS_TARGET)
            add_library(mosquitto_mosquitto_libmosquittopp_DEPS_TARGET INTERFACE IMPORTED)
        endif()

        set_property(TARGET mosquitto_mosquitto_libmosquittopp_DEPS_TARGET
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_FRAMEWORKS_FOUND_RELEASE}>
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_SYSTEM_LIBS_RELEASE}>
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_DEPENDENCIES_RELEASE}>
                     )

        ####### Find the libraries declared in cpp_info.component["xxx"].libs,
        ####### create an IMPORTED target for each one and link the 'mosquitto_mosquitto_libmosquittopp_DEPS_TARGET' to all of them
        conan_package_library_targets("${mosquitto_mosquitto_libmosquittopp_LIBS_RELEASE}"
                              "${mosquitto_mosquitto_libmosquittopp_LIB_DIRS_RELEASE}"
                              "${mosquitto_mosquitto_libmosquittopp_BIN_DIRS_RELEASE}" # package_bindir
                              "${mosquitto_mosquitto_libmosquittopp_LIBRARY_TYPE_RELEASE}"
                              "${mosquitto_mosquitto_libmosquittopp_IS_HOST_WINDOWS_RELEASE}"
                              mosquitto_mosquitto_libmosquittopp_DEPS_TARGET
                              mosquitto_mosquitto_libmosquittopp_LIBRARIES_TARGETS
                              "_RELEASE"
                              "mosquitto_mosquitto_libmosquittopp"
                              "${mosquitto_mosquitto_libmosquittopp_NO_SONAME_MODE_RELEASE}")


        ########## TARGET PROPERTIES #####################################
        set_property(TARGET mosquitto::libmosquittopp
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_OBJECTS_RELEASE}>
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_LIBRARIES_TARGETS}>
                     )

        if("${mosquitto_mosquitto_libmosquittopp_LIBS_RELEASE}" STREQUAL "")
            # If the component is not declaring any "cpp_info.components['foo'].libs" the system, frameworks etc are not
            # linked to the imported targets and we need to do it to the global target
            set_property(TARGET mosquitto::libmosquittopp
                         APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                         mosquitto_mosquitto_libmosquittopp_DEPS_TARGET)
        endif()

        set_property(TARGET mosquitto::libmosquittopp APPEND PROPERTY INTERFACE_LINK_OPTIONS
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_LINKER_FLAGS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquittopp APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_INCLUDE_DIRS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquittopp APPEND PROPERTY INTERFACE_LINK_DIRECTORIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_LIB_DIRS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquittopp APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_COMPILE_DEFINITIONS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquittopp APPEND PROPERTY INTERFACE_COMPILE_OPTIONS
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquittopp_COMPILE_OPTIONS_RELEASE}>)


    ########## COMPONENT mosquitto::libmosquitto #############

        set(mosquitto_mosquitto_libmosquitto_FRAMEWORKS_FOUND_RELEASE "")
        conan_find_apple_frameworks(mosquitto_mosquitto_libmosquitto_FRAMEWORKS_FOUND_RELEASE "${mosquitto_mosquitto_libmosquitto_FRAMEWORKS_RELEASE}" "${mosquitto_mosquitto_libmosquitto_FRAMEWORK_DIRS_RELEASE}")

        set(mosquitto_mosquitto_libmosquitto_LIBRARIES_TARGETS "")

        ######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
        if(NOT TARGET mosquitto_mosquitto_libmosquitto_DEPS_TARGET)
            add_library(mosquitto_mosquitto_libmosquitto_DEPS_TARGET INTERFACE IMPORTED)
        endif()

        set_property(TARGET mosquitto_mosquitto_libmosquitto_DEPS_TARGET
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_FRAMEWORKS_FOUND_RELEASE}>
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_SYSTEM_LIBS_RELEASE}>
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_DEPENDENCIES_RELEASE}>
                     )

        ####### Find the libraries declared in cpp_info.component["xxx"].libs,
        ####### create an IMPORTED target for each one and link the 'mosquitto_mosquitto_libmosquitto_DEPS_TARGET' to all of them
        conan_package_library_targets("${mosquitto_mosquitto_libmosquitto_LIBS_RELEASE}"
                              "${mosquitto_mosquitto_libmosquitto_LIB_DIRS_RELEASE}"
                              "${mosquitto_mosquitto_libmosquitto_BIN_DIRS_RELEASE}" # package_bindir
                              "${mosquitto_mosquitto_libmosquitto_LIBRARY_TYPE_RELEASE}"
                              "${mosquitto_mosquitto_libmosquitto_IS_HOST_WINDOWS_RELEASE}"
                              mosquitto_mosquitto_libmosquitto_DEPS_TARGET
                              mosquitto_mosquitto_libmosquitto_LIBRARIES_TARGETS
                              "_RELEASE"
                              "mosquitto_mosquitto_libmosquitto"
                              "${mosquitto_mosquitto_libmosquitto_NO_SONAME_MODE_RELEASE}")


        ########## TARGET PROPERTIES #####################################
        set_property(TARGET mosquitto::libmosquitto
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_OBJECTS_RELEASE}>
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_LIBRARIES_TARGETS}>
                     )

        if("${mosquitto_mosquitto_libmosquitto_LIBS_RELEASE}" STREQUAL "")
            # If the component is not declaring any "cpp_info.components['foo'].libs" the system, frameworks etc are not
            # linked to the imported targets and we need to do it to the global target
            set_property(TARGET mosquitto::libmosquitto
                         APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                         mosquitto_mosquitto_libmosquitto_DEPS_TARGET)
        endif()

        set_property(TARGET mosquitto::libmosquitto APPEND PROPERTY INTERFACE_LINK_OPTIONS
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_LINKER_FLAGS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquitto APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_INCLUDE_DIRS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquitto APPEND PROPERTY INTERFACE_LINK_DIRECTORIES
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_LIB_DIRS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquitto APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_COMPILE_DEFINITIONS_RELEASE}>)
        set_property(TARGET mosquitto::libmosquitto APPEND PROPERTY INTERFACE_COMPILE_OPTIONS
                     $<$<CONFIG:Release>:${mosquitto_mosquitto_libmosquitto_COMPILE_OPTIONS_RELEASE}>)


    ########## AGGREGATED GLOBAL TARGET WITH THE COMPONENTS #####################
    set_property(TARGET mosquitto::mosquitto APPEND PROPERTY INTERFACE_LINK_LIBRARIES mosquitto::libmosquittopp)
    set_property(TARGET mosquitto::mosquitto APPEND PROPERTY INTERFACE_LINK_LIBRARIES mosquitto::libmosquitto)

########## For the modules (FindXXX)
set(mosquitto_LIBRARIES_RELEASE mosquitto::mosquitto)
