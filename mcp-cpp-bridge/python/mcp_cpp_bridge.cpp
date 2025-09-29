#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <nlohmann/json.hpp>
#include "mcp/server/server.hpp"
#include "mcp/client/client.hpp"
#include "mcp/transport/stdio_transport.hpp"
#include "mcp/transport/tcp_transport.hpp"
#include "mcp/transport/websocket_transport.hpp"

namespace py = pybind11;
using namespace mcp;

// JSON conversion helpers
namespace {
    py::object json_to_python(const nlohmann::json& j) {
        if (j.is_null()) return py::none();
        if (j.is_boolean()) return py::bool_(j.get<bool>());
        if (j.is_number_integer()) return py::int_(j.get<int64_t>());
        if (j.is_number_float()) return py::float_(j.get<double>());
        if (j.is_string()) return py::str(j.get<std::string>());
        
        if (j.is_array()) {
            py::list lst;
            for (const auto& item : j) {
                lst.append(json_to_python(item));
            }
            return lst;
        }
        
        if (j.is_object()) {
            py::dict d;
            for (const auto& [key, value] : j.items()) {
                d[py::str(key)] = json_to_python(value);
            }
            return d;
        }
        
        return py::none();
    }
    
    nlohmann::json python_to_json(const py::handle& obj) {
        if (obj.is_none()) return nullptr;
        if (py::isinstance<py::bool_>(obj)) return obj.cast<bool>();
        if (py::isinstance<py::int_>(obj)) return obj.cast<int64_t>();
        if (py::isinstance<py::float_>(obj)) return obj.cast<double>();
        if (py::isinstance<py::str>(obj)) return obj.cast<std::string>();
        
        if (py::isinstance<py::list>(obj) || py::isinstance<py::tuple>(obj)) {
            nlohmann::json j = nlohmann::json::array();
            for (const auto& item : obj) {
                j.push_back(python_to_json(item));
            }
            return j;
        }
        
        if (py::isinstance<py::dict>(obj)) {
            nlohmann::json j = nlohmann::json::object();
            for (const auto& item : obj.cast<py::dict>()) {
                j[item.first.cast<std::string>()] = python_to_json(item.second);
            }
            return j;
        }
        
        throw std::runtime_error("Unsupported Python type for JSON conversion");
    }
}

PYBIND11_MODULE(mcp_cpp_bridge, m) {
    m.doc() = "MCP C++ Bridge - High-performance Model Context Protocol implementation";
    
    // Protocol module
    auto protocol = m.def_submodule("protocol", "MCP Protocol definitions");
    
    py::enum_<Protocol::ErrorCode>(protocol, "ErrorCode")
        .value("ParseError", Protocol::ErrorCode::ParseError)
        .value("InvalidRequest", Protocol::ErrorCode::InvalidRequest)
        .value("MethodNotFound", Protocol::ErrorCode::MethodNotFound)
        .value("InvalidParams", Protocol::ErrorCode::InvalidParams)
        .value("InternalError", Protocol::ErrorCode::InternalError)
        .value("ResourceNotFound", Protocol::ErrorCode::ResourceNotFound)
        .value("ResourceAccessDenied", Protocol::ErrorCode::ResourceAccessDenied)
        .value("ToolExecutionError", Protocol::ErrorCode::ToolExecutionError)
        .value("PromptRejected", Protocol::ErrorCode::PromptRejected);
    
    py::class_<Tool>(protocol, "Tool")
        .def(py::init<>())
        .def_readwrite("name", &Tool::name)
        .def_readwrite("description", &Tool::description)
        .def_property("input_schema",
            [](const Tool& t) { return json_to_python(t.input_schema); },
            [](Tool& t, py::object obj) { t.input_schema = python_to_json(obj); })
        .def("set_handler", [](Tool& t, py::function handler) {
            t.handler = [handler](const nlohmann::json& params) -> nlohmann::json {
                py::gil_scoped_acquire acquire;
                auto result = handler(json_to_python(params));
                return python_to_json(result);
            };
        });
    
    py::class_<Resource>(protocol, "Resource")
        .def(py::init<>())
        .def_readwrite("uri", &Resource::uri)
        .def_readwrite("name", &Resource::name)
        .def_readwrite("description", &Resource::description)
        .def_readwrite("mime_type", &Resource::mime_type);
    
    py::class_<Prompt>(protocol, "Prompt")
        .def(py::init<>())
        .def_readwrite("name", &Prompt::name)
        .def_readwrite("description", &Prompt::description)
        .def_readwrite("arguments", &Prompt::arguments);
    
    // Server module
    auto server_module = m.def_submodule("server", "MCP Server implementation");
    
    py::class_<ServerCapabilities>(server_module, "ServerCapabilities")
        .def(py::init<>())
        .def_readwrite("tools", &ServerCapabilities::tools)
        .def_readwrite("prompts", &ServerCapabilities::prompts)
        .def_readwrite("resources", &ServerCapabilities::resources)
        .def_readwrite("logging", &ServerCapabilities::logging);
    
    py::class_<server::Server::Config>(server_module, "ServerConfig")
        .def(py::init<>())
        .def_readwrite("name", &server::Server::Config::name)
        .def_readwrite("version", &server::Server::Config::version)
        .def_readwrite("capabilities", &server::Server::Config::capabilities)
        .def_readwrite("worker_threads", &server::Server::Config::worker_threads)
        .def_readwrite("max_concurrent_requests", &server::Server::Config::max_concurrent_requests)
        .def_readwrite("request_timeout", &server::Server::Config::request_timeout);
    
    py::class_<server::Server::Stats>(server_module, "ServerStats")
        .def_readonly("requests_received", &server::Server::Stats::requests_received)
        .def_readonly("requests_processed", &server::Server::Stats::requests_processed)
        .def_readonly("requests_failed", &server::Server::Stats::requests_failed)
        .def_readonly("notifications_received", &server::Server::Stats::notifications_received)
        .def_readonly("avg_response_time", &server::Server::Stats::avg_response_time);
    
    py::class_<server::Server>(server_module, "Server")
        .def(py::init<server::Server::Config>(), py::arg("config") = server::Server::Config{})
        .def("register_tool", &server::Server::register_tool)
        .def("unregister_tool", &server::Server::unregister_tool)
        .def("register_resource", &server::Server::register_resource)
        .def("unregister_resource", &server::Server::unregister_resource)
        .def("register_prompt", &server::Server::register_prompt)
        .def("unregister_prompt", &server::Server::unregister_prompt)
        .def("start", &server::Server::start)
        .def("stop", &server::Server::stop)
        .def("is_running", &server::Server::is_running)
        .def("get_stats", &server::Server::get_stats);
    
    py::class_<server::ServerBuilder>(server_module, "ServerBuilder")
        .def(py::init<>())
        .def("with_name", &server::ServerBuilder::with_name)
        .def("with_version", &server::ServerBuilder::with_version)
        .def("with_capabilities", &server::ServerBuilder::with_capabilities)
        .def("with_worker_threads", &server::ServerBuilder::with_worker_threads)
        .def("with_max_concurrent_requests", &server::ServerBuilder::with_max_concurrent_requests)
        .def("add_tool", &server::ServerBuilder::add_tool)
        .def("add_resource", &server::ServerBuilder::add_resource)
        .def("add_prompt", &server::ServerBuilder::add_prompt)
        .def("build", &server::ServerBuilder::build);
    
    // Version info
    m.attr("__version__") = "1.0.0";
    m.attr("__author__") = "AI-SERVIS Team";
}