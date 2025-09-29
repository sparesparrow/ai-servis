cmake_minimum_required(VERSION 3.15)
project(HardwareControlServer)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include Conan build info
include(${CMAKE_BINARY_DIR}/conan_toolchain.cmake)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

# Find required packages
find_package(Threads REQUIRED)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/..)

# Add executable
add_executable(hardware-server
    ../main_hardware_server.cpp
    ../HardwareControlServer.cpp
)

# Link libraries using Conan targets
target_link_libraries(hardware-server
    Threads::Threads
    CONAN_PKG::libgpiod
    CONAN_PKG::jsoncpp
    CONAN_PKG::mosquitto
    CONAN_PKG::libcurl
)