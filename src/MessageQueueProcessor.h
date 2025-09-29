#pragma once
#include <memory>
#include <string>
#include <unordered_map>
#include <mutex>

enum class JobStatus { Queued, Downloading, Completed, Failed, Aborted };

struct JobInfo {
    uint32_t sessionId;
    std::string url;
    JobStatus status;
    std::string filePath;
};

class IRequestReader;
class IResponseWriter;

class MessageQueueProcessor {
public:
    MessageQueueProcessor(const std::string& workingDir);
    ~MessageQueueProcessor();

    std::unique_ptr<class IJob> processMessage(std::unique_ptr<IRequestReader> reader, IResponseWriter* writer);

private:
    std::string workingDir_;
    std::unordered_map<uint32_t, JobInfo> jobs_;
    std::mutex jobs_mutex_;
    uint32_t next_session_id_;

    void enqueueJob(const std::string& url, IResponseWriter* writer);
};