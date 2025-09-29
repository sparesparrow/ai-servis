cmake_minimum_required(VERSION 3.20)
project(AiServis VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include Conan toolchain if available
if(EXISTS "${CMAKE_BINARY_DIR}/conan_toolchain.cmake")
    include(${CMAKE_BINARY_DIR}/conan_toolchain.cmake)
endif()

if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup(TARGETS)
endif()

# Find required packages (fallback if not using Conan)
find_package(Threads REQUIRED)

# Core library
add_library(webgrab_core STATIC
    core/FlatBuffersRequestWriter.cpp
    core/FlatBuffersResponseReader.cpp
    core/FlatBuffersRequestReader.cpp
    core/FlatBuffersResponseWriter.cpp
    core/TcpSocket.cpp
    core/WebGrabClient.cpp
    core/WebGrabServer.cpp
    core/MessageQueueProcessor.cpp
    core/DownloadJob.cpp
    core/JobWorker.cpp
    core/TcpListener.cpp
    core/CurlClientWrapper.cpp
)

# Link core library
if(TARGET CONAN_PKG::flatbuffers)
    target_link_libraries(webgrab_core
        CONAN_PKG::jsoncpp
        CONAN_PKG::flatbuffers
        CONAN_PKG::libcurl
        Threads::Threads
    )
else()
    # Fallback for systems without Conan
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(JSONCPP REQUIRED jsoncpp)
    find_library(FLATBUFFERS_LIBRARY flatbuffers REQUIRED)
    find_package(CURL REQUIRED)

    target_link_libraries(webgrab_core
        ${JSONCPP_LIBRARIES}
        ${FLATBUFFERS_LIBRARY}
        CURL::libcurl
        Threads::Threads
    )
    target_include_directories(webgrab_core PRIVATE ${JSONCPP_INCLUDE_DIRS})
endif()

# Hardware Control Server
add_executable(hardware-server
    core/main_hardware_server.cpp
    core/HardwareControlServer.cpp
)

if(TARGET CONAN_PKG::libgpiod)
    target_link_libraries(hardware-server
        webgrab_core
        CONAN_PKG::libgpiod
        CONAN_PKG::mosquitto
    )
else()
    # Fallback
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(GPIOD REQUIRED libgpiod)
    pkg_check_modules(MOSQUITTO REQUIRED libmosquitto)

    target_link_libraries(hardware-server
        webgrab_core
        ${GPIOD_LIBRARIES}
        ${MOSQUITTO_LIBRARIES}
    )
    target_include_directories(hardware-server PRIVATE
        ${GPIOD_INCLUDE_DIRS}
        ${MOSQUITTO_INCLUDE_DIRS}
    )
endif()

# MCP Server with FlatBuffers generation
# Find flatc (should be available via Conan)
find_program(FLATBUFFERS_FLATC_EXECUTABLE flatc)
if(FLATBUFFERS_FLATC_EXECUTABLE)
    # Generate FlatBuffers headers
    set(FLATBUFFERS_SCHEMA_DIR ${CMAKE_CURRENT_SOURCE_DIR}/core)
    set(FLATBUFFERS_OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR})

    add_custom_command(
        OUTPUT ${FLATBUFFERS_OUTPUT_DIR}/webgrab_generated.h
        COMMAND ${FLATBUFFERS_FLATC_EXECUTABLE} --cpp --gen-mutable -o ${FLATBUFFERS_OUTPUT_DIR} ${FLATBUFFERS_SCHEMA_DIR}/webgrab.fbs
        DEPENDS ${FLATBUFFERS_SCHEMA_DIR}/webgrab.fbs
        COMMENT "Generating FlatBuffers C++ headers with Conan flatc"
    )

    add_executable(mcp-server
        core/MCPIntegration/MCPServer/src/WebGrabMCPServer.cpp
        core/MCPIntegration/MCPServer/src/WebGrabMCPServerImpl.cpp
        core/MCPIntegration/MCPServer/src/DownloadTask.cpp
        core/MCPIntegration/MCPServer/src/StatusTask.cpp
        core/MCPIntegration/MCPServer/src/AbortTask.cpp
        core/MCPIntegration/MCPServer/src/GPIOTask.cpp
        core/MCPIntegration/MCPServer/src/WebGrabClientWrapper.cpp
        ${FLATBUFFERS_OUTPUT_DIR}/webgrab_generated.h
    )

    target_include_directories(mcp-server PRIVATE
        ${FLATBUFFERS_OUTPUT_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/core/MCPIntegration/MCPServer/src
    )

    if(TARGET CONAN_PKG::libgpiod)
        target_link_libraries(mcp-server
            webgrab_core
            CONAN_PKG::mosquitto
            CONAN_PKG::libgpiod
        )
    else()
        target_link_libraries(mcp-server
            webgrab_core
            ${MOSQUITTO_LIBRARIES}
            ${GPIOD_LIBRARIES}
        )
        target_include_directories(mcp-server PRIVATE
            ${MOSQUITTO_INCLUDE_DIRS}
            ${GPIOD_INCLUDE_DIRS}
        )
    endif()

    # Copy MCP config
    configure_file(${CMAKE_CURRENT_SOURCE_DIR}/core/MCPIntegration/MCPServer/config.ini
                   ${CMAKE_CURRENT_BINARY_DIR}/config.ini COPYONLY)
else()
    message(WARNING "FlatBuffers compiler (flatc) not found. MCP server will not be built. Install with: conan install ... --build flatbuffers")
endif()

# Legacy executables (for compatibility)
add_executable(webgrab-client core/main_client.cpp)
target_link_libraries(webgrab-client webgrab_core)

add_executable(webgrab-server core/main_server.cpp)
target_link_libraries(webgrab-server webgrab_core)

# Linux-specific builds
if(UNIX AND NOT APPLE)
    add_executable(webgrab-linux-host core/main_linux.cpp core/HotReloadManager.cpp)
    target_link_libraries(webgrab-linux-host webgrab_core dl)

    add_library(webgrab SHARED core/WebGrabDll.cpp)
    target_link_libraries(webgrab webgrab_core)
    set_target_properties(webgrab PROPERTIES
        VERSION 1.0.0
        SOVERSION 1
        OUTPUT_NAME webgrab
    )
endif()

# Windows builds
if(WIN32)
    add_library(webgrab_dll SHARED core/WebGrabDll.cpp)
    target_link_libraries(webgrab_dll webgrab_core)
endif()

# Installation rules
install(TARGETS hardware-server mcp-server webgrab_core
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

if(FLATBUFFERS_FLATC_EXECUTABLE)
    install(FILES ${CMAKE_CURRENT_BINARY_DIR}/config.ini
        DESTINATION etc/aiservis
    )
endif()