#include "FlatBuffersResponseReader.h"
#include "TcpSocket.h"
#include "webgrab_generated.h"
#include <cstring>
#include <arpa/inet.h>

FlatBuffersResponseReader::FlatBuffersResponseReader(std::shared_ptr<TcpSocket> socket)
    : socket_(socket) {}

FlatBuffersResponseReader::~FlatBuffersResponseReader() {
    close();
}

bool FlatBuffersResponseReader::recv(DownloadResponse& out) {
    if (!receiveMessage()) return false;
    auto resp = webgrab::GetDownloadResponse(buffer_.data());
    if (!resp) return false;
    out.sessionId = resp->sessionId();
    return true;
}

bool FlatBuffersResponseReader::recv(StatusResponse& out) {
    if (!receiveMessage()) return false;
    auto resp = webgrab::GetDownloadStatusResponse(buffer_.data());
    if (!resp) return false;
    out.sessionId = resp->sessionId();
    out.status = resp->status()->str();
    return true;
}

bool FlatBuffersResponseReader::recv(ErrorResponse& out) {
    // Implement based on schema
    return false; // Placeholder
}

bool FlatBuffersResponseReader::tryRecv(DownloadResponse& out, std::chrono::milliseconds timeout) {
    // Implement with timeout
    return recv(out); // Placeholder
}

bool FlatBuffersResponseReader::tryRecv(StatusResponse& out, std::chrono::milliseconds timeout) {
    // Implement with timeout
    return recv(out); // Placeholder
}

bool FlatBuffersResponseReader::tryRecv(ErrorResponse& out, std::chrono::milliseconds timeout) {
    // Implement with timeout
    return recv(out); // Placeholder
}

void FlatBuffersResponseReader::close() {
    if (socket_) {
        socket_->disconnect();
    }
}

bool FlatBuffersResponseReader::read(void* buffer, size_t size) {
    return socket_ && socket_->receive(static_cast<std::vector<uint8_t>&>(*reinterpret_cast<std::vector<uint8_t>*>(buffer)), size);
}

bool FlatBuffersResponseReader::receiveMessage() {
    if (!socket_ || !socket_->isConnected()) return false;

    // Read length prefix
    std::vector<uint8_t> length_buf(sizeof(uint32_t));
    if (!read(length_buf.data(), sizeof(uint32_t))) return false;
    uint32_t length = ntohl(*reinterpret_cast<uint32_t*>(length_buf.data()));

    // Read data
    buffer_.resize(length);
    return read(buffer_.data(), length);
}