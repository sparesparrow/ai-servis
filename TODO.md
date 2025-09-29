# TODO

The canonical task list lives at: [docs/TODO-master-list.md](docs/TODO-master-list.md)

## ✅ Recently Completed - C++ Platform Integration

### Hybrid MQP + MQTT Architecture
- **Unified Build System**: Consolidated CMakeLists.txt for all C++ components
- **Conan Dependency Management**: FlatBuffers header generation, cross-platform builds
- **MessageQueueProcessor Enhancement**: Now inherits IRequestReader/IResponseWriter
- **MQTT Bridge Implementation**: MQTTReader/MQTTWriter for cross-process communication
- **Schema Updates**: Enhanced FlatBuffers with GPIO and MQTT transport messages
- **CI/CD Pipeline**: Added C++ builds with multi-architecture support
- **Python Bridge**: MCP client and hardware controller for Python ↔ C++ integration

### Architecture Flow
```
Python AI Assistant → MQTT → MQP → C++ Hardware Server → MQP → GPIO Control
```

### Key Deliverables
- `platforms/cpp/`: Unified C++ platform components
- `modules/hardware-bridge/`: Python MCP client and GPIO controller
- Enhanced `conanfile.py`: Automatic FlatBuffers generation
- Updated CI pipeline for cross-platform C++ builds
- Documentation: Hybrid messaging architecture guide
