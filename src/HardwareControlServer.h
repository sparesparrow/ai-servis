#pragma once

#include <gpiod.hpp>
#include <unordered_map>
#include <memory>
#include <thread>
#include <atomic>
#include <netinet/in.h>
#include <json/json.h>

/**
 * @brief Simple Hardware Control Server
 *
 * This server provides GPIO control capabilities for Raspberry Pi
 * via TCP connections with JSON messages.
 */
class CHardwareControlServer {
public:
    CHardwareControlServer(int port = 8081);
    ~CHardwareControlServer();

    bool Start();
    void Stop();

private:
    // Server configuration
    int m_port;
    int m_serverSocket;
    std::atomic<bool> m_running;
    std::thread m_acceptThread;

    // GPIO chip and line management
    std::unique_ptr<gpiod::chip> m_chip;
    std::unordered_map<int, gpiod::line> m_activeLines;

    // Server methods
    bool InitializeGPIO();
    bool SetupServerSocket();
    void AcceptConnections();
    void HandleClient(int clientSocket);

    // Hardware control methods
    std::string HandleGPIOControl(const std::string& jsonRequest);
    bool SetGPIOPin(int pin, bool value);
    bool GetGPIOPin(int pin, bool& value);
    bool ConfigureGPIOPin(int pin, const std::string& direction);
};