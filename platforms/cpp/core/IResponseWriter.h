#pragma once
#include <string>
#include <cstdint>

class IResponseWriter {
public:
    virtual ~IResponseWriter() = default;
    virtual bool write(const DownloadResponse& resp) = 0;
    virtual bool write(const StatusResponse& resp) = 0;
    virtual bool write(const ErrorResponse& resp) = 0;
    virtual bool flush() = 0;
    virtual void close() = 0;
};