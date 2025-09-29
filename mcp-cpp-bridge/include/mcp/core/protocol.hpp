#pragma once

#include <string>
#include <variant>
#include <optional>
#include <vector>
#include <memory>
#include <functional>
#include <nlohmann/json.hpp>

namespace mcp {

/**
 * @brief Core MCP Protocol implementation following JSON-RPC 2.0
 */
class Protocol {
public:
    using Json = nlohmann::json;
    
    // Request/Response ID type
    using Id = std::variant<std::monostate, int64_t, std::string>;
    
    // Error codes following JSON-RPC 2.0 spec
    enum class ErrorCode : int {
        ParseError = -32700,
        InvalidRequest = -32600,
        MethodNotFound = -32601,
        InvalidParams = -32602,
        InternalError = -32603,
        
        // MCP-specific errors
        ResourceNotFound = -32001,
        ResourceAccessDenied = -32002,
        ToolExecutionError = -32003,
        PromptRejected = -32004
    };
    
    struct Error {
        ErrorCode code;
        std::string message;
        std::optional<Json> data;
        
        Json to_json() const;
    };
    
    struct Request {
        std::string jsonrpc = "2.0";
        std::string method;
        std::optional<Json> params;
        std::optional<Id> id;
        
        static Request from_json(const Json& j);
        Json to_json() const;
    };
    
    struct Response {
        std::string jsonrpc = "2.0";
        std::optional<Json> result;
        std::optional<Error> error;
        Id id;
        
        static Response from_json(const Json& j);
        Json to_json() const;
    };
    
    struct Notification {
        std::string jsonrpc = "2.0";
        std::string method;
        std::optional<Json> params;
        
        static Notification from_json(const Json& j);
        Json to_json() const;
    };
    
    // MCP-specific message types
    using Message = std::variant<Request, Response, Notification>;
    
    // Parse raw JSON into MCP message
    static std::optional<Message> parse(const std::string& json_str);
    static std::optional<Message> parse(const Json& json);
    
    // Serialize MCP message to JSON
    static std::string serialize(const Message& msg);
    static Json to_json(const Message& msg);
};

/**
 * @brief MCP Tool definition
 */
struct Tool {
    std::string name;
    std::string description;
    nlohmann::json input_schema;
    
    // Tool execution handler
    using Handler = std::function<nlohmann::json(const nlohmann::json& params)>;
    Handler handler;
    
    nlohmann::json to_json() const;
};

/**
 * @brief MCP Resource definition
 */
struct Resource {
    std::string uri;
    std::string name;
    std::optional<std::string> description;
    std::optional<std::string> mime_type;
    
    nlohmann::json to_json() const;
};

/**
 * @brief MCP Prompt definition
 */
struct Prompt {
    std::string name;
    std::string description;
    std::vector<std::pair<std::string, std::string>> arguments;
    
    nlohmann::json to_json() const;
};

/**
 * @brief Server capabilities
 */
struct ServerCapabilities {
    std::optional<bool> tools;
    std::optional<bool> prompts;
    std::optional<bool> resources;
    std::optional<bool> logging;
    
    nlohmann::json to_json() const;
};

/**
 * @brief Client capabilities  
 */
struct ClientCapabilities {
    std::optional<bool> sampling;
    std::optional<bool> roots;
    
    nlohmann::json to_json() const;
};

} // namespace mcp