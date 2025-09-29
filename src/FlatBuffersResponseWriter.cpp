#include "FlatBuffersResponseWriter.h"
#include "TcpSocket.h"
#include "webgrab_generated.h"
#include <cstring>
#include <arpa/inet.h>

FlatBuffersResponseWriter::FlatBuffersResponseWriter(std::shared_ptr<TcpSocket> client_socket)
    : client_socket_(client_socket) {}

FlatBuffersResponseWriter::~FlatBuffersResponseWriter() {
    close();
}

bool FlatBuffersResponseWriter::write(const DownloadResponse& resp) {
    builder_.Clear();
    auto fb_resp = webgrab::CreateDownloadResponse(builder_, resp.sessionId);
    builder_.Finish(fb_resp);
    return sendResponse();
}

bool FlatBuffersResponseWriter::write(const StatusResponse& resp) {
    builder_.Clear();
    auto status_offset = builder_.CreateString(resp.status);
    auto fb_resp = webgrab::CreateDownloadStatusResponse(builder_, resp.sessionId, status_offset);
    builder_.Finish(fb_resp);
    return sendResponse();
}

bool FlatBuffersResponseWriter::write(const ErrorResponse& resp) {
    // Implement
    return true; // Placeholder
}

bool FlatBuffersResponseWriter::flush() {
    // Implement flush
    return true; // Placeholder
}

void FlatBuffersResponseWriter::close() {
    if (client_socket_) {
        client_socket_->disconnect();
    }
}

bool FlatBuffersResponseWriter::write(const void* buffer, size_t size) {
    return client_socket_ && client_socket_->send(buffer, size);
}

bool FlatBuffersResponseWriter::sendResponse() {
    if (!client_socket_ || !client_socket_->isConnected()) return false;

    uint32_t length = htonl(static_cast<uint32_t>(builder_.GetSize()));
    if (!write(&length, sizeof(length))) return false;
    return write(builder_.GetBufferPointer(), builder_.GetSize());
}