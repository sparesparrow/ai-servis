#include "FlatBuffersRequestWriter.h"
#include "TcpSocket.h"
#include "webgrab_generated.h"
#include <cstring>
#include <arpa/inet.h>

FlatBuffersRequestWriter::FlatBuffersRequestWriter(std::shared_ptr<TcpSocket> socket)
    : socket_(socket) {}

FlatBuffersRequestWriter::~FlatBuffersRequestWriter() {
    close();
}

bool FlatBuffersRequestWriter::send(const DownloadRequest& req) {
    builder_.Clear();
    auto url_offset = builder_.CreateString(req.url);
    auto fb_req = webgrab::CreateDownloadRequest(builder_, url_offset);
    builder_.Finish(fb_req);
    return sendMessage(builder_.GetBufferPointer(), builder_.GetSize());
}

bool FlatBuffersRequestWriter::send(const DownloadStatusRequest& req) {
    builder_.Clear();
    auto fb_req = webgrab::CreateDownloadStatusRequest(builder_, req.sessionId);
    builder_.Finish(fb_req);
    return sendMessage(builder_.GetBufferPointer(), builder_.GetSize());
}

bool FlatBuffersRequestWriter::send(const DownloadAbortRequest& req) {
    builder_.Clear();
    auto fb_req = webgrab::CreateDownloadAbortRequest(builder_, req.sessionId);
    builder_.Finish(fb_req);
    return sendMessage(builder_.GetBufferPointer(), builder_.GetSize());
}

bool FlatBuffersRequestWriter::send(const ShutdownRequest& req) {
    builder_.Clear();
    auto fb_req = webgrab::CreateShutdownRequest(builder_);
    builder_.Finish(fb_req);
    return sendMessage(builder_.GetBufferPointer(), builder_.GetSize());
}

bool FlatBuffersRequestWriter::sendRaw(std::span<const uint8_t> data) {
    return sendMessage(data.data(), data.size());
}

void FlatBuffersRequestWriter::close() {
    if (socket_) {
        socket_->disconnect();
    }
}

bool FlatBuffersRequestWriter::write(const void* buffer, size_t size) {
    return socket_ && socket_->send(buffer, size);
}

bool FlatBuffersRequestWriter::sendMessage(const void* data, size_t size) {
    if (!socket_ || !socket_->isConnected()) return false;

    // Send length prefix (big-endian uint32)
    uint32_t length = htonl(static_cast<uint32_t>(size));
    if (!write(&length, sizeof(length))) return false;

    // Send data
    return write(data, size);
}