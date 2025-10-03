message(STATUS "Conan: Using CMakeDeps conandeps_legacy.cmake aggregator via include()")
message(STATUS "Conan: It is recommended to use explicit find_package() per dependency instead")

find_package(jsoncpp)
find_package(flatbuffers)
find_package(CURL)
find_package(libgpiod)
find_package(mosquitto)
find_package(OpenSSL)
find_package(ZLIB)

set(CONANDEPS_LEGACY  JsonCpp::JsonCpp  flatbuffers::flatbuffers  CURL::libcurl  libgpiod::libgpiod  mosquitto::mosquitto  openssl::openssl  ZLIB::ZLIB )
