"""Materialize the supplied three-package Cargo reproduction; no downloads or builds."""
from pathlib import Path

FILES = {
    "Cargo.toml": '''[workspace]
resolver = "2"
members = ["codec", "sdk", "cli"]

[workspace.package]
edition = "2021"
rust-version = "1.74"
''',
    "codec/Cargo.toml": '''[package]
name = "codec"
version = "0.1.0"
edition.workspace = true
rust-version.workspace = true

[features]
default = []
alloc = []
''',
    "codec/src/lib.rs": '''#![no_std]
#[cfg(feature = "alloc")]
extern crate alloc;

#[cfg(feature = "alloc")]
pub fn encode(input: &[u8]) -> alloc::vec::Vec<u8> {
    input.iter().map(|byte| byte ^ 0x5a).collect()
}
''',
    "sdk/Cargo.toml": '''[package]
name = "sdk"
version = "0.1.0"
edition.workspace = true
rust-version.workspace = true

[dependencies]
codec = { path = "../codec", version = "0.1.0", default-features = false }
''',
    "sdk/src/lib.rs": '''#![no_std]
extern crate alloc;

pub fn encode_request(input: &[u8]) -> alloc::vec::Vec<u8> {
    codec::encode(input)
}
''',
    "cli/Cargo.toml": '''[package]
name = "client-cli"
version = "0.1.0"
edition.workspace = true
rust-version.workspace = true

[dependencies]
sdk = { path = "../sdk", version = "0.1.0" }
codec = { path = "../codec", version = "0.1.0", features = ["alloc"] }
''',
    "cli/src/main.rs": '''fn main() {
    println!("{:?}", sdk::encode_request(b"request"));
}
''',
}

root = Path("workspace")
for relative, content in FILES.items():
    target = root / relative
    if target.exists():
        raise SystemExit(f"Refusing to overwrite {target}; use a fresh directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
print("Created workspace/. Run Cargo from that directory.")
