# Arc

One reason to use an immutable linked list is to share data across threads.
After all, shared mutable state is the root of all evil, and one way to solve
that is to kill the *mutable* part forever.

Our `Rc`-based list cannot be sent or shared between threads. Its reference
count uses ordinary, non-atomic updates, so concurrent updates could corrupt
the count and free a node while another owner still uses it.

`Arc` is the thread-safe reference-counted pointer: it updates the shared
reference count atomically. That costs more than `Rc`, so Rust provides both.
For this immutable list, we can replace `Rc` with `std::sync::Arc` to share the
ownership count safely across threads. The data is thread-safe only when the
node contents are too: `Arc<T>` is `Send` and `Sync` only when `T` is both
`Send` and `Sync`. `Arc` makes shared ownership thread-safe; it does not make
an unsafe inner value safe.

But this raises an interesting question: how do we *know* if a type is
thread-safe or not? Can we accidentally mess up?

Rust's type system catches many thread-safety mistakes in safe code, but it
cannot verify an incorrect `unsafe impl`. The two traits Rust uses to express
thread-safety are `Send` and `Sync`.

A type is *Send* if it's safe to *move* to another thread. A type is *Sync* if
it's safe to *share* between multiple threads. That is, if `T` is Sync, `&T` is
Send. Safe in this case means it's impossible to cause *data races*, (not to
be mistaken with the more general issue of *race conditions*).

These are marker traits, which is a fancy way of saying they're traits that
provide absolutely no interface. You either *are* Send, or you aren't. It's just
a property *other* APIs can require. If you aren't appropriately Send,
then it's statically impossible to be sent to a different thread! Sweet!

Send and Sync are also automatically derived traits based on whether you are
totally composed of Send and Sync types. It's similar to how you can only
implement Copy if you're only made of Copy types, but then we just go ahead
and implement it automatically if you are.

Almost every ordinary type is `Send` and `Sync`. A type that owns its data
can usually be moved between threads when its contents are `Send`. Shared
references prevent ordinary mutation, and interior-mutability types must use
appropriate synchronization before they can be `Sync`.

However there are special types that violate these properties: those that have
*interior mutability*. So far we've only really interacted with *inherited
mutability* (AKA external mutability): the mutability of a value is inherited
from the mutability of its container. That is, you can't just randomly mutate
some field of a non-mutable value because you feel like it.

Interior-mutability types allow mutation through a shared reference. `Cell`
and `RefCell` are single-threaded tools; `Mutex` and `RwLock` coordinate access
between threads. Atomics provide individual operations on shared values, such
as incrementing a counter. They are not locks: a lock coordinates access to a
larger piece of data, while an atomic operation applies to its atomic value.

So what does all of this have to do with `Rc` and `Arc`? Their shared
reference counts use interior mutability. `Rc` updates its count without
synchronization, so it cannot be shared between threads. `Arc` uses atomic
operations for that count, which makes shared ownership safe across threads
when `T: Send + Sync`. The atomics protect the count, not the contents of `T`.
For example, `Arc<RefCell<T>>` is still not thread-safe; use a synchronization
type such as `Mutex<T>` when shared mutation across threads is needed.

I really really really don't want to get into the finer details of atomic
memory models or non-derived Send implementations. Needless to say, as you get
deeper into Rust's thread-safety story, stuff gets more complicated. As a
high-level consumer, it all *just works* and you don't really need to think
about it.
