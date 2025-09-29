from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.layout import basic_layout


class AiServisConan(ConanFile):
    name = "ai-servis"
    version = "1.0"
    description = "AI Service with MCP and Hardware Control"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def configure(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        # GPIO library for Raspberry Pi hardware control
        self.requires("libgpiod/1.6.3")
        # JSON library for API communication
        self.requires("jsoncpp/1.9.5")
        # MQTT client for ESP32 communication
        self.requires("mosquitto/2.0.18")
        # HTTP client for LLM API calls
        self.requires("libcurl/8.5.0")

    def layout(self):
        basic_layout(self)

    def generate(self):
        # Generate CMake toolchain and dependencies
        tc = CMakeToolchain(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        # Package the hardware server executable
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # Define library information
        self.cpp_info.libs = ["hardware-server"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "dl"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32"]