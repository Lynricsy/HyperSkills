#include <functional>
#include <iostream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

// The event loop runs queued callbacks only after the current request returns.
class EventLoop {
public:
    void post(std::function<void()> callback) { pending_.push_back(std::move(callback)); }
    void drain() {
        auto current = std::move(pending_);
        for (auto& callback : current) callback();
    }
private:
    std::vector<std::function<void()>> pending_;
};

void queue_labels(EventLoop& loop, std::vector<std::string>& output) {
    std::vector<std::string> labels;
    labels.reserve(1);
    labels.emplace_back("alpha");
    std::string_view first = labels.front();
    loop.post([first, &output] { output.emplace_back(first); });
    labels.emplace_back("beta");
    labels.front() = "edited";
    loop.post([label = std::string_view(labels.back()), &output] {
        output.emplace_back(label);
    });
}

int main() {
    EventLoop loop;
    std::vector<std::string> output;
    queue_labels(loop, output);
    loop.drain();
    for (const auto& label : output) std::cout << label << '\n';
    return output == std::vector<std::string>{"alpha", "beta"} ? 0 : 1;
}
