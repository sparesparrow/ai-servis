#pragma once
#include <optional>
#include <string>
#include <cstdint>
#include <chrono>

struct DownloadResponse {
    uint32_t sessionId;
};

struct StatusResponse {
    uint32_t sessionId;
    std::string status;
};

struct ErrorResponse {
    std::string error;
};

class IResponseReader {
public:
    virtual ~IResponseReader() = default;
    virtual bool recv(DownloadResponse& out) = 0;
    virtual bool recv(StatusResponse& out) = 0;
    virtual bool recv(ErrorResponse& out) = 0;
    virtual bool tryRecv(DownloadResponse& out, std::chrono::milliseconds timeout) = 0;
    virtual bool tryRecv(StatusResponse& out, std::chrono::milliseconds timeout) = 0;
    virtual bool tryRecv(ErrorResponse& out, std::chrono::milliseconds timeout) = 0;
    virtual void close() = 0;
};
