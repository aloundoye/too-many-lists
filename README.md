# Learn Rust by writing Entirely Too Many Linked Lists
[![Build Status](https://travis-ci.org/rust-unofficial/too-many-lists.svg?branch=master)](https://travis-ci.org/rust-unofficial/too-many-lists)

Read the pretty version at https://rust-unofficial.github.io/too-many-lists/.

# Building

Building requires mdbook, which can be installed from crates.io:

```sh
cargo install mdbook
```

Assuming you've placed the install directory `~/.cargo/bin` into your system PATH, then run from the root of your local copy:

```sh
mdbook build
```

---

If you'd prefer, this project can also be built with
[GitBook](https://github.com/GitbookIO/gitbook), although GitBook
is not officially supported and compatibility is therefore
uncertain and incidental.


## Checking the modernized examples

Use Rust 2024 (Rust 1.85 or newer) and mdBook 0.5.4 or newer.

```sh
cargo test --manifest-path lists/Cargo.toml
python3 scripts/check_examples.py
mdbook build
mdbook test
# Optional nightly checks, also run in CI:
rustup +nightly component add miri
CHECK_MIRI=1 python3 scripts/check_examples.py
python3 scripts/check_aliasing.py
```

The listing checker tests the code extracted from the book, including Chapter
6's embedded compile-fail doctest, without adding a public library module.
See [the modernization audit](MODERNIZATION_AUDIT.md) for narrative decisions.
