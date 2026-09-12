#include <coroutine>
#include <exception>
#include <iostream>
#include <memory>
#include <string>
#include <utility>
#include <vector>

class Task {
public:
    struct promise_type {
        Task get_return_object() {
            return Task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_always initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_void() noexcept {}
        void unhandled_exception() { std::terminate(); }
    };
    explicit Task(std::coroutine_handle<promise_type> handle) : handle_(handle) {}
    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;
    Task(Task&& other) noexcept : handle_(std::exchange(other.handle_, {})) {}
    Task& operator=(Task&& other) noexcept {
        if (this != &other) {
            if (handle_) handle_.destroy();
            handle_ = std::exchange(other.handle_, {});
        }
        return *this;
    }
    ~Task() { if (handle_) handle_.destroy(); }
    bool resume() {
        if (!handle_ || handle_.done()) return false;
        handle_.resume();
        return !handle_.done();
    }
private:
    std::coroutine_handle<promise_type> handle_;
};

class Scheduler {
public:
    void add(Task task) { pending_.push_back(std::move(task)); }
    void drain() {
        for (auto& task : pending_) while (task.resume()) {}
        pending_.clear();
    }
    void cancel() { pending_.clear(); }
private:
    std::vector<Task> pending_;
};

struct Report { std::string title; };

std::weak_ptr<Report> submit(Scheduler& scheduler, std::vector<std::string>& output,
                             std::string title) {
    auto report = std::make_shared<Report>(Report{std::move(title)});
    std::weak_ptr<Report> observer = report;
    auto export_report = [report = std::move(report), &output]() -> Task {
        co_await std::suspend_always{};
        output.push_back(report->title);
    };
    scheduler.add(export_report());
    return observer;
}

int main() {
    Scheduler scheduler;
    std::vector<std::string> output;
    auto completed = submit(scheduler, output, "daily");
    if (completed.expired()) {
        std::cerr << "report expired while queued\n";
        return 1;
    }
    scheduler.drain();
    if (output != std::vector<std::string>{"daily"} || !completed.expired()) return 2;
    auto cancelled = submit(scheduler, output, "discard");
    if (cancelled.expired()) return 3;
    scheduler.cancel();
    if (!cancelled.expired() || output != std::vector<std::string>{"daily"}) return 4;
    std::cout << "completion and cancellation release reports\n";
}
