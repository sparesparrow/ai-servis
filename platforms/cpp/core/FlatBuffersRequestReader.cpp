#include "FlatBuffersRequestReader.h"
#include "webgrab_generated.h"
#include <flatbuffers/verifier.h>

FlatBuffersRequestReader::FlatBuffersRequestReader()
    : current_type_(RequestType::Unknown) {}

bool FlatBuffersRequestReader::next(RequestEnvelope& out) {
    if (!receiveMessage()) return false;

    // Parse the Message structure
    auto message = webgrab::GetMessage(buffer_.data());
    if (!message) {
        current_type_ = RequestType::Unknown;
        out.type = current_type_;
        return false;
    }

    // Determine type based on request_type
    switch (message->request_type()) {
    case webgrab::Request_DownloadRequest:
        current_type_ = RequestType::Download;
        break;
    case webgrab::Request_DownloadStatusRequest:
        current_type_ = RequestType::Status;
        break;
    case webgrab::Request_DownloadAbortRequest:
        current_type_ = RequestType::Abort;
        break;
    case webgrab::Request_ShutdownRequest:
        current_type_ = RequestType::Shutdown;
        break;
    default:
        current_type_ = RequestType::Unknown;
        break;
    }

    out.type = current_type_;
    return true;
}

bool FlatBuffersRequestReader::good() const {
    return !buffer_.empty();
}

void FlatBuffersRequestReader::close() {
    buffer_.clear();
}

bool FlatBuffersRequestReader::read(void* buffer, size_t size) {
    // Placeholder: in real impl, read from socket
    return false;
}

bool FlatBuffersRequestReader::receiveMessage() {
    // Placeholder: read from socket into buffer_
    return !buffer_.empty();
}

std::string FlatBuffersRequestReader::getDownloadUrl() const {
    if (current_type_ == RequestType::Download) {
        auto message = webgrab::GetMessage(buffer_.data());
        if (message) {
            auto req = message->request_as_DownloadRequest();
            if (req && req->url()) {
                return req->url()->str();
            }
        }
    }
    return "";
}

uint32_t FlatBuffersRequestReader::getSessionId() const {
    auto message = webgrab::GetMessage(buffer_.data());
    if (!message) return 0;

    if (current_type_ == RequestType::Status) {
        auto req = message->request_as_DownloadStatusRequest();
        if (req) {
            return req->sessionId();
        }
    } else if (current_type_ == RequestType::Abort) {
        auto req = message->request_as_DownloadAbortRequest();
        if (req) {
            return req->sessionId();
        }
    }
    return 0;
}

bool FlatBuffersRequestReader::isValid() const {
    flatbuffers::Verifier verifier(buffer_.data(), buffer_.size());
    return verifier.VerifyBuffer<webgrab::Message>(nullptr);
}

std::string FlatBuffersRequestReader::getValidationError() const {
    return "Validation failed";
}
