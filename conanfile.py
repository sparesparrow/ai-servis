from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.layout import basic_layout


class AiServisConan(ConanFile):
    name = "ai-servis"
    version = "1.0"
    description = "AI Service with MCP and Hardware Control"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_hardware": [True, False],
        "with_mcp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_hardware": True,
        "with_mcp": True,
    }

    def configure(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self, src_folder="platforms/cpp")

    def source(self):
        # Set source folder to platforms/cpp
        pass

    def requirements(self):
        # Core dependencies - always required
        self.requires("jsoncpp/1.9.5")  # JSON handling for all components
        self.requires("flatbuffers/23.5.26")  # Serialization for all components
        self.requires("libcurl/8.5.0")  # HTTP client for downloads and APIs
        self.requires("openssl/3.0.8")  # SSL/TLS support
        self.requires("zlib/1.2.13")  # Compression support

        # Hardware-specific dependencies
        if self.options.with_hardware:
            self.requires("libgpiod/1.6.3")  # GPIO control for Raspberry Pi
            self.requires("mosquitto/2.0.18")  # MQTT communication

        # MCP-specific dependencies
        if self.options.with_mcp:
            # MCP integration may need additional deps
            pass

    def build_requirements(self):
        # Tools needed for building
        self.tool_requires("flatbuffers/23.5.26")  # For flatc compiler

    def layout(self):
        basic_layout(self)

    def generate(self):
        # Generate CMake toolchain and dependencies
        tc = CMakeToolchain(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        # Generate FlatBuffers headers before building
        self._generate_flatbuffers()

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _generate_flatbuffers(self):
        """Generate C++ headers from FlatBuffers schema"""
        import os
        from pathlib import Path

        # Find flatc executable
        flatc_path = None
        if hasattr(self, "deps_cpp_info") and self.deps_cpp_info.has_components:
            # Try to get flatc from Conan dependencies
            try:
                flatbuffers_info = self.deps_cpp_info["flatbuffers"]
                flatc_path = os.path.join(flatbuffers_info.bin_paths[0], "flatc")
            except:
                pass

        if not flatc_path or not os.path.exists(flatc_path):
            # Try system flatc
            import shutil

            flatc_path = shutil.which("flatc")

        if not flatc_path:
            self.output.warning(
                "FlatBuffers compiler (flatc) not found. C++ headers will not be generated."
            )
            return

        # Schema and output paths
        schema_dir = os.path.join(self.source_folder, "platforms", "cpp", "core")
        schema_file = os.path.join(schema_dir, "webgrab.fbs")
        output_file = os.path.join(schema_dir, "webgrab_generated.h")

        if not os.path.exists(schema_file):
            self.output.warning(f"FlatBuffers schema not found: {schema_file}")
            return

        # Generate headers
        import subprocess

        cmd = [flatc_path, "--cpp", "--gen-mutable", "-o", schema_dir, schema_file]

        try:
            self.output.info(f"Generating FlatBuffers headers: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.output.info(
                f"FlatBuffers headers generated successfully: {output_file}"
            )
        except subprocess.CalledProcessError as e:
            self.output.error(f"Failed to generate FlatBuffers headers: {e}")
            self.output.error(f"stdout: {e.stdout}")
            self.output.error(f"stderr: {e.stderr}")
            raise

    def package(self):
        # Package the executables and libraries
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # Define library information
        self.cpp_info.libs = ["webgrab_core"]

        if self.options.with_hardware:
            self.cpp_info.libs.append("hardware-server")

        if self.options.with_mcp:
            self.cpp_info.libs.append("mcp-server")

        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "dl", "rt"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "crypt32", "advapi32"]
