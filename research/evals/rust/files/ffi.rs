// Review this adapter against packet.h. There is no linked C implementation.
use std::slice;

#[repr(C)]
pub struct Packet {
    pub enabled: bool,
    pub len: u32,
    pub data: *const u8,
}

pub fn payload<'a>(packet: *const Packet) -> Result<&'a [u8], &'static str> {
    if packet.is_null() {
        return Err("missing packet");
    }
    let packet = unsafe { &*packet };
    if !packet.enabled {
        return Ok(&[]);
    }
    if packet.len > 4096 {
        return Err("packet too large");
    }
    Ok(unsafe { slice::from_raw_parts(packet.data, packet.len as usize) })
}
