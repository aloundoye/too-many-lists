# Unsafe Rust

This is a serious, big, complicated, and dangerous topic.
It's so serious that I wrote [an entire other book][nom] on it.

The long and the short of it is that *every* language is actually unsafe as soon
as you allow calling into other languages, because you can just have C do
arbitrarily bad things. Yes: Java, Python, Ruby, Haskell... everyone is wildly
unsafe in the face of Foreign Function Interfaces (FFI).

Rust distinguishes safe and unsafe *contexts*, but they are not separate
languages. Safe Rust lets the compiler check memory-safety rules; safe code
cannot cause undefined behavior on its own, assuming any unsafe library
abstractions it calls are implemented correctly. Safe code can still panic or
have ordinary logic bugs.

An `unsafe` block permits operations the compiler cannot verify, such as
dereferencing raw pointers or calling an `unsafe` function. It does not turn
off the borrow checker or make those operations safe. The programmer must
still uphold their safety requirements; getting them wrong can cause
undefined behavior.

Again, this is a really huge topic that has a lot of interesting corner cases.
I *really* don't want to go really deep into it (well, I do. I did. [Read that
book][nom]). That's ok, because with linked lists we can actually ignore almost
all of it.

> **NARRATOR:** This was a lie, but it did seem true in 2015.

The main unsafe tool we'll be using is the *raw pointer*. Raw pointers don't
carry borrow-checked lifetimes, and the compiler doesn't enforce exclusive or
shared access rules when you use them. A raw pointer can be null, dangling, or
misaligned, and it can point at uninitialized memory. Converting a pointer to
another type or to an integer doesn't make the pointed-to value valid. Any
operation that dereferences a raw pointer is unsafe, and the programmer must
still uphold Rust's requirements for validity, alignment, initialization,
provenance, and aliasing. The details matter, and they are a major part of what
makes unsafe code difficult.

> **NARRATOR:** no inherent aliasing rules, eh? Ah, the innocence of youth.

This is some bad stuff and honestly you'll live a happier life never having
to touch these. Unfortunately, we want to write linked lists, and linked lists
are awful. That means we're going to have to use unsafe pointers.

There are two kinds of raw pointer: `*const T` and `*mut T`. The `const` in
`*const T` means the pointer itself cannot be written through directly; it does
not mean the value is globally immutable. The `mut` in `*mut T` allows a write
only when the access rules for that memory permit it. Casting a `*const T` to
`*mut T` does not grant permission to mutate, and writing through it can still
be undefined behavior. Interior-mutable values such as `UnsafeCell<T>` have
their own documented rules. Raw pointers make access the programmer's
responsibility; they do not erase Rust's rules.

In the Rust 2024 edition, an `unsafe fn` declares requirements for its caller,
but unsafe operations inside its body still need explicit `unsafe { ... }`
blocks. The [Edition Guide's `unsafe_op_in_unsafe_fn` section](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html)
explains the lint that warns about missing blocks. This makes each place where
the implementation takes responsibility easy to see. We'll get a better feel
for this as we write code. For now, treat
`*mut T` as an unchecked pointer that may be used to mutate only when the
program can prove that the access is valid and exclusive.

[nom]: https://doc.rust-lang.org/nomicon/
