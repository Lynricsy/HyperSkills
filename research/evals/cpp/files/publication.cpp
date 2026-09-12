#include <atomic>
#include <iostream>
#include <thread>

struct Channel {
    std::atomic<int> payload{0};
    std::atomic<bool> ready{false};
};

int main() {
    Channel channel;
    int observed = -1;
    std::thread producer([&] {
        channel.payload.store(42, std::memory_order_relaxed);
        channel.ready.store(true, std::memory_order_relaxed);
    });
    std::thread consumer([&] {
        while (!channel.ready.load(std::memory_order_relaxed)) {
            std::this_thread::yield();
        }
        observed = channel.payload.load(std::memory_order_relaxed);
    });
    producer.join();
    consumer.join();
    std::cout << observed << '\n';
    return observed == 42 ? 0 : 1;
}
