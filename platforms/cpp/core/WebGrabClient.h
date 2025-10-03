#pragma once
#include <memory>
#include <string>

class IRequestWriter;
class IResponseReader;

class WebGrabClient {
private:
    std::unique_ptr<IRequestWriter> writer_;
    std::unique_ptr<IResponseReader> reader_;
    std::shared_ptr<class TcpSocket> socket_;

public:
    WebGrabClient(const std::string& host, uint16_t port);
    ~WebGrabClient();

    bool connect();
    bool executeDownload(const std::string& url);
    bool executeStatus(uint32_t sessionId);
    bool executeAbort(uint32_t sessionId);
    bool executeQuit();
};
