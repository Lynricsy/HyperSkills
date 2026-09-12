#include "packet.hpp"

std::size_t library_packet_size() { return sizeof(Packet); }
void initialize_packet(Packet& packet) {
#ifdef PACKET_EXTENDED
    packet.sequence = 17;
#endif
    packet.payload = 42;
}
