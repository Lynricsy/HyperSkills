# Build interfaces and diagnostic evidence

Verified against: CMake 4.1.6 documentation (examples require CMake 3.20+),
Clang sanitizer documentation, and C++17/20/23 language floors.
Build and instrumentation claims are [official]; test staging is [community].

## Contents

- Usage requirements belong to the producer
- ABI and ODR need more than a link
- Separate compiler and library support
- Select diagnostics by failure class
- Exercise the actual target

## Usage requirements belong to the producer

Classify a requirement by who needs it, not by a preference for `PRIVATE`:

| Scope | Target being built | Consumers through the target |
|---|---|---|
| `PRIVATE` | Yes | No compile usage requirement |
| `INTERFACE` | No | Yes |
| `PUBLIC` | Yes | Yes |

A macro selecting public structure layout or inline definitions is part of the
contract on both sides. A consumer-only macro can be `INTERFACE`; an internal
implementation switch can be `PRIVATE`. Link dependency propagation for static
archives has additional rules: do not infer that `PRIVATE` erases all downstream
link dependencies merely because compile usage requirements stay private.

For a library whose public headers require C++17 and the specified packet layout,
use a target-level definition, not duplicate flags on the one executable:

```cmake
cmake_minimum_required(VERSION 3.20)
project(packet_example LANGUAGES CXX)
add_library(packet packet.cpp)
target_compile_features(packet PUBLIC cxx_std_17)
target_compile_definitions(packet PUBLIC PACKET_WIDE=1)
target_include_directories(packet PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
  "$<INSTALL_INTERFACE:include>")
add_executable(client client.cpp)
target_link_libraries(client PRIVATE packet)
```

This is a build excerpt requiring the named project files, not a downloadable
example. In a real package, inspect the exported target and its dependency discovery
as well; a build-tree consumer does not verify installed-package completeness.
Keep private warning preferences off the consumer interface. Use imported dependency
targets instead of copying their include paths and guessing library filenames.

## ABI and ODR need more than a link

Compare actual producer and consumer compile commands and preprocessed public
headers. Look for packing, alignment, conditional members, inline bodies, template
definitions, calling conventions, symbol visibility, and exception/RTTI settings.
Macro differences can violate the one-definition rule without a linker diagnostic.
Equal `sizeof` does not prove equal field offsets, definitions, calling convention,
allocator domain or standard-library ABI.

Record architecture and standard-library ABI switches, including debug-iterator
modes when present. Do not mix incompatible binary dependencies by hiding the
failure behind a cast. A stable plugin boundary needs a designed ABI and explicit
allocation/free ownership; serializing the bytes of an arbitrary C++ object is not
a portable wire format. Rebuild all affected binaries after a layout contract
change rather than recompiling only the consumer that crashed.

## Separate compiler and library support

Capture compiler executable/version, standard library identity/version, target
triple or architecture, sysroot, standard mode, and CMake generator/toolchain file.
Clang using libstdc++ does not gain libc++ features from the Clang version number.
`cxx_std_23` requests a mode at least aware of C++23, not every C++23 facility.
`__cplusplus` similarly does not prove that a particular library component exists.

Check the feature-test macro in the appropriate header or `<version>` (C++20),
then compile and link an actual use. Record the macro threshold from the feature's
official documentation instead of guessing a date value. Coroutine language
support starts in C++20; standard `generator` is C++23 and requires implementation
support; no standard C++20 `task` abstraction is implied. Do not use a working-draft
facility merely because its documentation sits beside a C++17 rule.

Preserve extension and warning policy. For a compiler or sysroot change, configure
a new build directory; an existing cache is not a reliable toolchain migration.
For cross-compilation, compile/link availability does not establish runtime behavior
on the target. Run there or state that limitation.

## Select diagnostics by failure class

| Diagnostic | Useful evidence | Important blind spot |
|---|---|---|
| ASan | Instrumented memory errors such as use-after-free and bounds violations | Not a proof of lifetime correctness for every object, input or dependency |
| UBSan | Enabled checks such as signed overflow, alignment and invalid shifts | `undefined` is a check group, not all UB; excludes checks such as `vptr` |
| TSan | Instrumented data races across observed executions | Does not prove all-atomic protocol ordering, deadlock freedom or reclamation correctness |
| Assertions/behavioral checks | Snapshot values, state transitions, cancellation releases | Only the contract and paths actually asserted |

Use ASan plus UBSan for a memory reproducer, and a separate TSan build for races.
Do not combine ASan and TSan. Compile the relevant library sources with the selected
sanitizer, and link the final executable with the compiler driver and sanitizer
runtime. Instrumenting only a test wrapper leaves most accesses unchecked.
UBSan normally recovers for many checks; select `-fno-sanitize-recover=undefined`
when the reproducer must exit unsuccessfully on those reports.

For a standalone C++20 memory reproducer named `repro.cpp`, on a supported Clang
platform, run this command shape; adjust the standard only to the actual project
floor and preserve its required dependency flags:

```sh
clang++ -std=c++20 -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=undefined repro.cpp -o repro-asan
./repro-asan
```

For a threaded reproducer, build separately with `-fsanitize=thread -pthread`.
Do not claim either command was run merely because it is documented here.
Check the installed sanitizer's supported platform and runtime. TSan does not
support statically linked libc/libstdc++; uninstrumented dependencies can hide
races or omit synchronization. A shadow-memory mapping failure is an environment
failure, not a negative race report. Document exclusions instead of adding broad
ignorelists until the report disappears.

## Exercise the actual target

Use the repository's existing presets and runner. Inspect a verbose build for
producer and consumer flags; pass the chosen configuration for multi-config
generators. Enumerate CTest cases with `ctest --test-dir build -N` and execute the
relevant selection with `ctest --test-dir build --output-on-failure -R pattern`.
Replace `build` and `pattern` with the actual directory and test selector, and
confirm the selected set is not empty. Discovery or a zero-test exit is not a run.

Make failure injection deterministic at resource boundaries. For concurrent tests,
control arrival and release through real synchronization and bound hangs. Preserve
ordinary execution alongside instrumented execution because instrumentation changes
timing and layout. Report the command, exit status, observed behavior, and uncovered
configurations. A passing run is evidence for that run, not certification of no UB.

<!-- sources: cmake-buildsystem, cmake-features, clang-asan, clang-ubsan, clang-tsan, ecc-cpp-testing -->
