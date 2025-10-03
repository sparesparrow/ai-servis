#include "WebGrabClient.h"
#include <memory>

// C API for shared library
extern "C" {

void* wg_create_client(const char* server_host, uint16_t server_port) {
    try {
        return new WebGrabClient(server_host, server_port);
    } catch (...) {
        return nullptr;
    }
}

void wg_destroy_client(void* client_handle) {
    delete static_cast<WebGrabClient*>(client_handle);
}

bool wg_download(void* client_handle, const char* url, uint32_t* out_session_id) {
    auto client = static_cast<WebGrabClient*>(client_handle);
    // Assume executeDownload sets session_id
    // For simplicity, placeholder
    *out_session_id = 1; // Placeholder
    return client->executeDownload(url);
}

bool wg_get_status(void* client_handle, uint32_t session_id, char* out_status, size_t status_buf_size) {
    auto client = static_cast<WebGrabClient*>(client_handle);
    // Placeholder
    return client->executeStatus(session_id);
}

bool wg_abort(void* client_handle, uint32_t session_id) {
    auto client = static_cast<WebGrabClient*>(client_handle);
    return client->executeAbort(session_id);
}

void wg_shutdown(void* client_handle) {
    auto client = static_cast<WebGrabClient*>(client_handle);
    client->executeQuit();
}

}
