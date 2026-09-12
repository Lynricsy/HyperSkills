#pragma once
#include <cstddef>
#include <cstdint>

struct Packet {
#ifdef PACKET_EXTENDED
    std::uint64_t sequence;
#endif
    std::uint32_t payload;
};

std::size_t library_packet_size();
void initialize_packet(Packet& packet);
