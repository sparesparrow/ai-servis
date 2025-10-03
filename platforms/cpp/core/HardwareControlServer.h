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
#include <mutex>

// Project includes
#include "MessageQueueProcessor.h"
#include "MQTTBridge.h"

namespace WebGrab {

/**
 * @brief Hardware Control Server for GPIO operations
 *
 * This server provides GPIO control capabilities for Raspberry Pi
 * via hybrid TCP + MQTT communication. It implements a multi-threaded
 * TCP server for direct hardware access and MQTT integration for
 * cross-process communication with Python orchestrator.
 *
 * Uses MessageQueueProcessor for job management and MQTTBridge for
 * pub/sub messaging, maintaining compatibility with existing interfaces.
 */
class HardwareControlServer {
public:
    /**
     * @brief Construct a new Hardware Control Server object
     *
     * @param port TCP port to listen on (default: 8081)
     * @param mqtt_host MQTT broker hostname (default: localhost)
     * @param mqtt_port MQTT broker port (default: 1883)
     * @param working_dir Working directory for file operations
     */
    explicit HardwareControlServer(int port = 8081,
                                   const std::string& mqtt_host = "localhost",
                                   int mqtt_port = 1883,
                                   const std::string& working_dir = "/tmp/webgrab");

    /**
     * @brief Destroy the Hardware Control Server object
     */
    ~HardwareControlServer();

    /**
     * @brief Start the server
     *
     * Initializes GPIO, MQTT bridge, and message queue processor.
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

    // MQTT configuration
    std::string mqtt_host;
    int mqtt_port;
    struct mosquitto* mqtt_client;
    std::thread mqttThread;
    std::mutex mqttMutex;

    // GPIO chip and line management
    std::unique_ptr<gpiod::chip> chip;
    std::unordered_map<int, gpiod::line> activeLines;

    // Server methods
    bool InitializeGPIO();
    bool SetupServerSocket();
    bool InitializeMQTT();
    void AcceptConnections();
    void HandleClient(int clientSocket);
    void MQTTLoop();

    // MQTT callbacks
    static void on_mqtt_connect(struct mosquitto* mosq, void* obj, int rc);
    static void on_mqtt_message(struct mosquitto* mosq, void* obj,
                               const struct mosquitto_message* msg);
    void HandleMQTTMessage(const std::string& topic, const std::string& payload);

    // Hardware control methods
    std::string HandleGPIOControl(const std::string& jsonRequest);
    bool SetGPIOPin(int pin, bool value);
    bool GetGPIOPin(int pin, bool& value);
    bool ConfigureGPIOPin(int pin, const std::string& direction);
};

} // namespace WebGrab
