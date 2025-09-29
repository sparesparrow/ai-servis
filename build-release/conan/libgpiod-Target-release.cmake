# Avoid multiple calls to find_package to append duplicated properties to the targets
include_guard()########### VARIABLES #######################################################################
#############################################################################################
set(libgpiod_FRAMEWORKS_FOUND_RELEASE "") # Will be filled later
conan_find_apple_frameworks(libgpiod_FRAMEWORKS_FOUND_RELEASE "${libgpiod_FRAMEWORKS_RELEASE}" "${libgpiod_FRAMEWORK_DIRS_RELEASE}")

set(libgpiod_LIBRARIES_TARGETS "") # Will be filled later


######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
if(NOT TARGET libgpiod_DEPS_TARGET)
    add_library(libgpiod_DEPS_TARGET INTERFACE IMPORTED)
endif()

set_property(TARGET libgpiod_DEPS_TARGET
             APPEND PROPERTY INTERFACE_LINK_LIBRARIES
             $<$<CONFIG:Release>:${libgpiod_FRAMEWORKS_FOUND_RELEASE}>
             $<$<CONFIG:Release>:${libgpiod_SYSTEM_LIBS_RELEASE}>
             $<$<CONFIG:Release>:>)

####### Find the libraries declared in cpp_info.libs, create an IMPORTED target for each one and link the
####### libgpiod_DEPS_TARGET to all of them
conan_package_library_targets("${libgpiod_LIBS_RELEASE}"    # libraries
                              "${libgpiod_LIB_DIRS_RELEASE}" # package_libdir
                              "${libgpiod_BIN_DIRS_RELEASE}" # package_bindir
                              "${libgpiod_LIBRARY_TYPE_RELEASE}"
                              "${libgpiod_IS_HOST_WINDOWS_RELEASE}"
                              libgpiod_DEPS_TARGET
                              libgpiod_LIBRARIES_TARGETS  # out_libraries_targets
                              "_RELEASE"
                              "libgpiod"    # package_name
                              "${libgpiod_NO_SONAME_MODE_RELEASE}")  # soname

# FIXME: What is the result of this for multi-config? All configs adding themselves to path?
set(CMAKE_MODULE_PATH ${libgpiod_BUILD_DIRS_RELEASE} ${CMAKE_MODULE_PATH})

########## COMPONENTS TARGET PROPERTIES Release ########################################

    ########## COMPONENT libgpiod::gpiod #############

        set(libgpiod_libgpiod_gpiod_FRAMEWORKS_FOUND_RELEASE "")
        conan_find_apple_frameworks(libgpiod_libgpiod_gpiod_FRAMEWORKS_FOUND_RELEASE "${libgpiod_libgpiod_gpiod_FRAMEWORKS_RELEASE}" "${libgpiod_libgpiod_gpiod_FRAMEWORK_DIRS_RELEASE}")

        set(libgpiod_libgpiod_gpiod_LIBRARIES_TARGETS "")

        ######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
        if(NOT TARGET libgpiod_libgpiod_gpiod_DEPS_TARGET)
            add_library(libgpiod_libgpiod_gpiod_DEPS_TARGET INTERFACE IMPORTED)
        endif()

        set_property(TARGET libgpiod_libgpiod_gpiod_DEPS_TARGET
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_FRAMEWORKS_FOUND_RELEASE}>
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_SYSTEM_LIBS_RELEASE}>
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_DEPENDENCIES_RELEASE}>
                     )

        ####### Find the libraries declared in cpp_info.component["xxx"].libs,
        ####### create an IMPORTED target for each one and link the 'libgpiod_libgpiod_gpiod_DEPS_TARGET' to all of them
        conan_package_library_targets("${libgpiod_libgpiod_gpiod_LIBS_RELEASE}"
                              "${libgpiod_libgpiod_gpiod_LIB_DIRS_RELEASE}"
                              "${libgpiod_libgpiod_gpiod_BIN_DIRS_RELEASE}" # package_bindir
                              "${libgpiod_libgpiod_gpiod_LIBRARY_TYPE_RELEASE}"
                              "${libgpiod_libgpiod_gpiod_IS_HOST_WINDOWS_RELEASE}"
                              libgpiod_libgpiod_gpiod_DEPS_TARGET
                              libgpiod_libgpiod_gpiod_LIBRARIES_TARGETS
                              "_RELEASE"
                              "libgpiod_libgpiod_gpiod"
                              "${libgpiod_libgpiod_gpiod_NO_SONAME_MODE_RELEASE}")


        ########## TARGET PROPERTIES #####################################
        set_property(TARGET libgpiod::gpiod
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_OBJECTS_RELEASE}>
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_LIBRARIES_TARGETS}>
                     )

        if("${libgpiod_libgpiod_gpiod_LIBS_RELEASE}" STREQUAL "")
            # If the component is not declaring any "cpp_info.components['foo'].libs" the system, frameworks etc are not
            # linked to the imported targets and we need to do it to the global target
            set_property(TARGET libgpiod::gpiod
                         APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                         libgpiod_libgpiod_gpiod_DEPS_TARGET)
        endif()

        set_property(TARGET libgpiod::gpiod APPEND PROPERTY INTERFACE_LINK_OPTIONS
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_LINKER_FLAGS_RELEASE}>)
        set_property(TARGET libgpiod::gpiod APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_INCLUDE_DIRS_RELEASE}>)
        set_property(TARGET libgpiod::gpiod APPEND PROPERTY INTERFACE_LINK_DIRECTORIES
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_LIB_DIRS_RELEASE}>)
        set_property(TARGET libgpiod::gpiod APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_COMPILE_DEFINITIONS_RELEASE}>)
        set_property(TARGET libgpiod::gpiod APPEND PROPERTY INTERFACE_COMPILE_OPTIONS
                     $<$<CONFIG:Release>:${libgpiod_libgpiod_gpiod_COMPILE_OPTIONS_RELEASE}>)


    ########## AGGREGATED GLOBAL TARGET WITH THE COMPONENTS #####################
    set_property(TARGET libgpiod::libgpiod APPEND PROPERTY INTERFACE_LINK_LIBRARIES libgpiod::gpiod)

########## For the modules (FindXXX)
set(libgpiod_LIBRARIES_RELEASE libgpiod::libgpiod)
