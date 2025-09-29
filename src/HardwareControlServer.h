#pragma once

// Third-party includes (alphabetically)
#include <gpiod.hpp>
#include <json/json.h>

// Standard library includes (alphabetically)
#include <atomic>
#include <memory>
#include <netinet/in.h>
#include <string>
#include <thread>
#include <unordered_map>

namespace WebGrab {

/**
 * @brief Hardware Control Server for GPIO operations
 *
 * This server provides GPIO control capabilities for Raspberry Pi
 * via TCP connections with JSON messages. It implements a multi-threaded
 * TCP server that accepts JSON commands for GPIO pin configuration
 * and value reading/writing.
 */
class HardwareControlServer {
public:
    /**
     * @brief Construct a new Hardware Control Server object
     *
     * @param port TCP port to listen on (default: 8081)
     */
    explicit HardwareControlServer(int port = 8081);

    /**
     * @brief Destroy the Hardware Control Server object
     */
    ~HardwareControlServer();

    /**
     * @brief Start the server
     *
     * Initializes GPIO and starts listening for connections.
     *
     * @return true if server started successfully, false otherwise
     */
    bool Start();

    /**
     * @brief Stop the server
     *
     * Stops accepting new connections and cleans up resources.
     */
    void Stop();

private:
    // Server configuration
    int port;
    int serverSocket;
    std::atomic<bool> running;
    std::thread acceptThread;

    // GPIO chip and line management
    std::unique_ptr<gpiod::chip> chip;
    std::unordered_map<int, gpiod::line> activeLines;

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

} // namespace WebGrab