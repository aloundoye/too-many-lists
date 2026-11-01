# Layout

The key to our design is the `RefCell` type. The heart of
RefCell is a pair of methods:

```rust ,ignore
fn borrow(&self) -> Ref<'_, T>;
fn borrow_mut(&self) -> RefMut<'_, T>;
```

The borrowing rules match those of `&T` and `&mut T`: you can have several
shared borrows at once, or one exclusive mutable borrow. You cannot have both
at the same time.

Rust normally checks these rules at compile time. `RefCell` checks them at
runtime instead: `borrow` and `borrow_mut` panic if a requested borrow would
break the rules, while `try_borrow` and `try_borrow_mut` return an error. The
returned `Ref` and `RefMut` values are *guards*: they act like shared and
mutable references to the contents and keep the corresponding borrow active
until the guard is dropped. They are not owning pointers like `Rc`.

Now with `Rc<RefCell<T>>` we can share ownership and mutate through shared
owners in one thread. Strong `Rc` cycles keep their nodes alive, so they can
leak; reference counting is not tracing garbage collection. Y-yaaaaay...

Alright, we want to be *doubly-linked*. This means each node has a pointer to
the previous and next node. Also, the list itself has a pointer to the
first and last node. This gives us fast insertion and removal on *both*
ends of the list.

So we probably want something like:

```rust ,ignore
use std::rc::Rc;
use std::cell::RefCell;

pub struct List<T> {
    head: Link<T>,
    tail: Link<T>,
}

type Link<T> = Option<Rc<RefCell<Node<T>>>>;

struct Node<T> {
    elem: T,
    next: Link<T>,
    prev: Link<T>,
}
```

```text
> cargo build

warning: field is never used: `head`
 --> src/fourth.rs:5:5
  |
5 |     head: Link<T>,
  |     ^^^^^^^^^^^^^
  |
  = note: #[warn(dead_code)] on by default

warning: field is never used: `tail`
 --> src/fourth.rs:6:5
  |
6 |     tail: Link<T>,
  |     ^^^^^^^^^^^^^

warning: field is never used: `elem`
  --> src/fourth.rs:12:5
   |
12 |     elem: T,
   |     ^^^^^^^

warning: field is never used: `next`
  --> src/fourth.rs:13:5
   |
13 |     next: Link<T>,
   |     ^^^^^^^^^^^^^

warning: field is never used: `prev`
  --> src/fourth.rs:14:5
   |
14 |     prev: Link<T>,
   |     ^^^^^^^^^^^^^
```

Hey, it built! Lots of dead code warnings, but it built! Let's try to use it.
