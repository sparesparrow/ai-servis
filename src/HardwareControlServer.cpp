#include "HardwareControlServer.h"
#include <iostream>
#include <sstream>
#include <unistd.h>
#include <cstring>

CHardwareControlServer::CHardwareControlServer(int port)
    : m_port(port), m_serverSocket(-1), m_running(false) {
}

CHardwareControlServer::~CHardwareControlServer() {
    Stop();
}

bool CHardwareControlServer::Start() {
    if (!InitializeGPIO()) {
        std::cerr << "Failed to initialize GPIO" << std::endl;
        return false;
    }

    if (!SetupServerSocket()) {
        std::cerr << "Failed to setup server socket" << std::endl;
        return false;
    }

    m_running = true;
    m_acceptThread = std::thread(&CHardwareControlServer::AcceptConnections, this);

    std::cout << "Hardware Control Server started on port " << m_port << std::endl;
    return true;
}

void CHardwareControlServer::Stop() {
    m_running = false;

    if (m_acceptThread.joinable()) {
        m_acceptThread.join();
    }

    if (m_serverSocket != -1) {
        close(m_serverSocket);
        m_serverSocket = -1;
    }

    m_activeLines.clear();
    std::cout << "Hardware Control Server stopped" << std::endl;
}

bool CHardwareControlServer::InitializeGPIO() {
    try {
        m_chip = std::make_unique<gpiod::chip>("gpiochip0");
        std::cout << "Hardware Control Server: GPIO chip initialized" << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Hardware Control Server: Failed to initialize GPIO chip: " << e.what() << std::endl;
        return false;
    }
}

bool CHardwareControlServer::SetupServerSocket() {
    m_serverSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (m_serverSocket == -1) {
        std::cerr << "Failed to create socket" << std::endl;
        return false;
    }

    int opt = 1;
    if (setsockopt(m_serverSocket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1) {
        std::cerr << "Failed to set socket options" << std::endl;
        return false;
    }

    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(m_port);

    if (bind(m_serverSocket, reinterpret_cast<sockaddr*>(&serverAddr), sizeof(serverAddr)) == -1) {
        std::cerr << "Failed to bind socket" << std::endl;
        return false;
    }

    if (listen(m_serverSocket, 5) == -1) {
        std::cerr << "Failed to listen on socket" << std::endl;
        return false;
    }

    return true;
}

void CHardwareControlServer::AcceptConnections() {
    while (m_running) {
        sockaddr_in clientAddr{};
        socklen_t clientAddrLen = sizeof(clientAddr);

        int clientSocket = accept(m_serverSocket, reinterpret_cast<sockaddr*>(&clientAddr), &clientAddrLen);
        if (clientSocket == -1) {
            if (m_running) {
                std::cerr << "Failed to accept connection" << std::endl;
            }
            continue;
        }

        std::cout << "Client connected" << std::endl;
        std::thread(&CHardwareControlServer::HandleClient, this, clientSocket).detach();
    }
}

void CHardwareControlServer::HandleClient(int clientSocket) {
    char buffer[4096];

    while (m_running) {
        ssize_t bytesRead = recv(clientSocket, buffer, sizeof(buffer) - 1, 0);
        if (bytesRead <= 0) {
            break;
        }

        buffer[bytesRead] = '\0';
        std::string request(buffer);
        std::string response = HandleGPIOControl(request);

        send(clientSocket, response.c_str(), response.length(), 0);
    }

    close(clientSocket);
    std::cout << "Client disconnected" << std::endl;
}

std::string CHardwareControlServer::HandleGPIOControl(const std::string& jsonRequest) {
    Json::Value params;
    Json::Value response;
    Json::Reader reader;

    try {
        if (!reader.parse(jsonRequest, params)) {
            response["success"] = false;
            response["error"] = "Invalid JSON request";
            return Json::FastWriter().write(response);
        }

        // Extract parameters
        int pin = params.get("pin", -1).asInt();
        std::string direction = params.get("direction", "").asString();
        int value = params.get("value", -1).asInt();

        // Validate pin
        if (pin < 0 || pin > 40) {
            response["success"] = false;
            response["error"] = "Invalid pin number. Must be between 0 and 40.";
            return Json::FastWriter().write(response);
        }

        // Handle direction configuration
        if (!direction.empty()) {
            if (direction == "input" || direction == "output") {
                if (ConfigureGPIOPin(pin, direction)) {
                    response["success"] = true;
                    response["message"] = "GPIO pin " + std::to_string(pin) + " configured as " + direction;

                    // If output and value provided, set the value
                    if (direction == "output" && value >= 0) {
                        if (SetGPIOPin(pin, value != 0)) {
                            response["message"] = response["message"].get("message", "").asString() + " and set to " + std::to_string(value);
                        } else {
                            response["success"] = false;
                            response["error"] = "Failed to set GPIO pin value";
                        }
                    }
                    // If input, read the current value
                    else if (direction == "input") {
                        bool currentValue;
                        if (GetGPIOPin(pin, currentValue)) {
                            response["value"] = currentValue ? 1 : 0;
                        } else {
                            response["success"] = false;
                            response["error"] = "Failed to read GPIO pin value";
                        }
                    }
                } else {
                    response["success"] = false;
                    response["error"] = "Failed to configure GPIO pin";
                }
            } else {
                response["success"] = false;
                response["error"] = "Invalid direction. Must be 'input' or 'output'.";
            }
        }
        // Handle value setting without direction change
        else if (value >= 0) {
            if (SetGPIOPin(pin, value != 0)) {
                response["success"] = true;
                response["message"] = "GPIO pin " + std::to_string(pin) + " set to " + std::to_string(value);
            } else {
                response["success"] = false;
                response["error"] = "Failed to set GPIO pin value. Pin may not be configured as output.";
            }
        }
        // Handle value reading
        else {
            bool currentValue;
            if (GetGPIOPin(pin, currentValue)) {
                response["success"] = true;
                response["value"] = currentValue ? 1 : 0;
                response["message"] = "GPIO pin " + std::to_string(pin) + " value read successfully";
            } else {
                response["success"] = false;
                response["error"] = "Failed to read GPIO pin value. Pin may not be configured as input.";
            }
        }

        return Json::FastWriter().write(response);

    } catch (const std::exception& e) {
        response["success"] = false;
        response["error"] = "GPIO control failed";
        response["details"] = e.what();
        return Json::FastWriter().write(response);
    }
}

bool CHardwareControlServer::ConfigureGPIOPin(int pin, const std::string& direction) {
    if (!m_chip) return false;

    try {
        // Release existing line if it exists
        if (m_activeLines.find(pin) != m_activeLines.end()) {
            m_activeLines.erase(pin);
        }

        // Get and configure the new line
        gpiod::line line = m_chip->get_line(pin);

        if (direction == "input") {
            gpiod::line_request request = {
                "hardware-control-server",
                gpiod::line_request::DIRECTION_INPUT,
                0
            };
            line.request(request);
        } else if (direction == "output") {
            gpiod::line_request request = {
                "hardware-control-server",
                gpiod::line_request::DIRECTION_OUTPUT,
                0
            };
            line.request(request);
        }

        // Store the configured line
        m_activeLines[pin] = std::move(line);
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Failed to configure GPIO pin " << pin << ": " << e.what() << std::endl;
        return false;
    }
}

bool CHardwareControlServer::SetGPIOPin(int pin, bool value) {
    auto it = m_activeLines.find(pin);
    if (it == m_activeLines.end()) return false;

    try {
        it->second.set_value(value ? 1 : 0);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Failed to set GPIO pin " << pin << ": " << e.what() << std::endl;
        return false;
    }
}

bool CHardwareControlServer::GetGPIOPin(int pin, bool& value) {
    auto it = m_activeLines.find(pin);
    if (it == m_activeLines.end()) return false;

    try {
        int val = it->second.get_value();
        value = (val != 0);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Failed to get GPIO pin " << pin << ": " << e.what() << std::endl;
        return false;
    }
}