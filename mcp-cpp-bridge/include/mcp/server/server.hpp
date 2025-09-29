#pragma once

#include "mcp/core/protocol.hpp"
#include "mcp/transport/transport.hpp"
#include <memory>
#include <unordered_map>
#include <mutex>
#include <future>
#include <spdlog/spdlog.h>

namespace mcp::server {

/**
 * @brief Advanced MCP Server implementation with full protocol support
 */
class Server {
public:
    struct Config {
        std::string name = "mcp-cpp-server";
        std::string version = "1.0.0";
        ServerCapabilities capabilities;
        
        // Performance tuning
        size_t worker_threads = 4;
        size_t max_concurrent_requests = 100;
        std::chrono::milliseconds request_timeout{30000};
        
        // Logging
        spdlog::level::level_enum log_level = spdlog::level::info;
    };
    
    explicit Server(Config config = {});
    ~Server();
    
    // Tool management
    void register_tool(Tool tool);
    void unregister_tool(const std::string& name);
    
    // Resource management
    void register_resource(Resource resource);
    void unregister_resource(const std::string& uri);
    
    // Prompt management
    void register_prompt(Prompt prompt);
    void unregister_prompt(const std::string& name);
    
    // Transport management
    void add_transport(std::unique_ptr<transport::Transport> transport);
    
    // Server lifecycle
    void start();
    void stop();
    bool is_running() const;
    
    // Statistics and monitoring
    struct Stats {
        uint64_t requests_received = 0;
        uint64_t requests_processed = 0;
        uint64_t requests_failed = 0;
        uint64_t notifications_received = 0;
        std::chrono::milliseconds avg_response_time{0};
    };
    
    Stats get_stats() const;
    
private:
    class Impl;
    std::unique_ptr<Impl> impl_;
    
    // Request handlers
    void handle_initialize(const Protocol::Request& req);
    void handle_initialized(const Protocol::Notification& notif);
    void handle_shutdown(const Protocol::Request& req);
    
    void handle_tools_list(const Protocol::Request& req);
    void handle_tools_call(const Protocol::Request& req);
    
    void handle_resources_list(const Protocol::Request& req);
    void handle_resources_read(const Protocol::Request& req);
    void handle_resources_subscribe(const Protocol::Request& req);
    
    void handle_prompts_list(const Protocol::Request& req);
    void handle_prompts_get(const Protocol::Request& req);
    
    void handle_logging_setLevel(const Protocol::Request& req);
    
    // Internal message processing
    void process_message(const Protocol::Message& msg, 
                        std::shared_ptr<transport::Transport> transport);
    void send_response(const Protocol::Response& resp,
                       std::shared_ptr<transport::Transport> transport);
    void send_notification(const Protocol::Notification& notif,
                          std::shared_ptr<transport::Transport> transport);
};

/**
 * @brief Builder pattern for Server configuration
 */
class ServerBuilder {
public:
    ServerBuilder& with_name(std::string name);
    ServerBuilder& with_version(std::string version);
    ServerBuilder& with_capabilities(ServerCapabilities caps);
    ServerBuilder& with_worker_threads(size_t count);
    ServerBuilder& with_max_concurrent_requests(size_t max);
    ServerBuilder& with_request_timeout(std::chrono::milliseconds timeout);
    ServerBuilder& with_log_level(spdlog::level::level_enum level);
    
    ServerBuilder& add_tool(Tool tool);
    ServerBuilder& add_resource(Resource resource);
    ServerBuilder& add_prompt(Prompt prompt);
    ServerBuilder& add_transport(std::unique_ptr<transport::Transport> transport);
    
    std::unique_ptr<Server> build();
    
private:
    Server::Config config_;
    std::vector<Tool> tools_;
    std::vector<Resource> resources_;
    std::vector<Prompt> prompts_;
    std::vector<std::unique_ptr<transport::Transport>> transports_;
};

} // namespace mcp::server