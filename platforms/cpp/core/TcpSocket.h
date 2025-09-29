#pragma once
#include <string>
#include <vector>
#include <memory>

class TcpSocket {
public:
    TcpSocket(const std::string& host, uint16_t port);
    ~TcpSocket();

    bool connect();
    bool isConnected() const;
    void disconnect();

    bool send(const void* data, size_t size);
    bool receive(std::vector<uint8_t>& buffer);
    bool receiveExact(std::vector<uint8_t>& buffer, size_t expectedSize);

private:
    int sockfd_;
    std::string host_;
    uint16_t port_;
    bool connected_;
};