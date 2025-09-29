#include "FlatBuffersRequestReader.h"
#include "webgrab_generated.h"
#include <flatbuffers/verifier.h>

FlatBuffersRequestReader::FlatBuffersRequestReader()
    : current_type_(RequestType::Unknown) {}

bool FlatBuffersRequestReader::next(RequestEnvelope& out) {
    if (!receiveMessage()) return false;

    // Determine type
    if (webgrab::GetDownloadRequest(buffer_.data())) {
        current_type_ = RequestType::Download;
    } else if (webgrab::GetDownloadStatusRequest(buffer_.data())) {
        current_type_ = RequestType::Status;
    } else if (webgrab::GetDownloadAbortRequest(buffer_.data())) {
        current_type_ = RequestType::Abort;
    } else if (webgrab::GetShutdownRequest(buffer_.data())) {
        current_type_ = RequestType::Shutdown;
    } else {
        current_type_ = RequestType::Unknown;
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
        auto req = webgrab::GetDownloadRequest(buffer_.data());
        return req->url()->str();
    }
    return "";
}

uint32_t FlatBuffersRequestReader::getSessionId() const {
    if (current_type_ == RequestType::Status) {
        auto req = webgrab::GetDownloadStatusRequest(buffer_.data());
        return req->sessionId();
    } else if (current_type_ == RequestType::Abort) {
        auto req = webgrab::GetDownloadAbortRequest(buffer_.data());
        return req->sessionId();
    }
    return 0;
}

bool FlatBuffersRequestReader::isValid() const {
    flatbuffers::Verifier verifier(buffer_.data(), buffer_.size());
    switch (current_type_) {
    case RequestType::Download:
        return verifier.VerifyBuffer<webgrab::DownloadRequest>(nullptr);
    case RequestType::Status:
        return verifier.VerifyBuffer<webgrab::DownloadStatusRequest>(nullptr);
    case RequestType::Abort:
        return verifier.VerifyBuffer<webgrab::DownloadAbortRequest>(nullptr);
    case RequestType::Shutdown:
        return verifier.VerifyBuffer<webgrab::ShutdownRequest>(nullptr);
    default:
        return false;
    }
}

std::string FlatBuffersRequestReader::getValidationError() const {
    return "Validation failed";
}