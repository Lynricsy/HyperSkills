#include <stdint.h>

/* Returned by a synchronous C callback. The packet and its payload remain live
 * and unmodified only until the callback returns. No ownership is transferred.
 * enabled is a byte: 0 = disabled, 1 = enabled; other values must be rejected.
 * data may be NULL only when len is zero. Nonempty payloads are initialized
 * bytes in a single allocation of at least len bytes. len may exceed the Rust
 * application's 4096-byte limit. The packet pointer is properly aligned.
 */
struct packet {
    uint8_t enabled;
    uint32_t len;
    const uint8_t *data;
};
