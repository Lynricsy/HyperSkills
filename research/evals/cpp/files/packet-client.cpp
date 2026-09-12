#include "packet.hpp"
#include <iostream>

int main() {
    Packet packet{};
    std::cout << "client=" << sizeof(Packet)
              << " library=" << library_packet_size() << '\n';
    initialize_packet(packet);
    return packet.payload == 42 ? 0 : 1;
}
