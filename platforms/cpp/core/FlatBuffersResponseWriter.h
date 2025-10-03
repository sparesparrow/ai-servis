#pragma once
#include "IResponseReader.h"
#include "IResponseWriter.h"
#include "IWriter.h"
#include <memory>
#include <flatbuffers/flatbuffers.h>

class TcpSocket; // Forward declaration

class FlatBuffersResponseWriter : public IResponseWriter, public IWriter {
private:
    std::shared_ptr<TcpSocket> client_socket_;
    flatbuffers::FlatBufferBuilder builder_;

public:
    explicit FlatBuffersResponseWriter(std::shared_ptr<TcpSocket> client_socket);
    ~FlatBuffersResponseWriter() override;

    // IResponseWriter
    bool write(const webgrab::DownloadResponse& resp) override;
    bool write(const webgrab::StatusResponse& resp) override;
    bool write(const webgrab::ErrorResponse& resp) override;
    bool flush() override;
    void close() override;

    // IWriter
    bool write(const void* buffer, size_t size) override;

private:
    bool sendResponse();
};
