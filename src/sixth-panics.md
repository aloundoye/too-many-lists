# Drop and Panic Safety

So hey, did you notice this comment:

```rust
// Note that we don't need to mess around with `take` anymore
// because everything is Copy and there are no dtors that will
// run if we mess up... right? :) Riiiight? :)))
```

Is it right? 

Sorry did you forget the book you're reading? Of course it's wrong! (Sort Of.)

Let's look at the inner body of pop_front again:

```rust ,ignore
// Rebuild the owning Box from the raw pointer. This transfers
// ownership of the allocation back to Box.
let boxed_node = Box::from_raw(node.as_ptr());
let result = boxed_node.elem;

// Make the next node into the new front.
self.front = boxed_node.back;
if let Some(new) = self.front {
    // Cleanup its reference to the removed node
    (*new.as_ptr()).front = None;
} else {
    // If the front is now null, then this list is now empty!
    debug_assert!(self.len == 1);
    self.back = None;
}

self.len -= 1;
result
// When boxed_node leaves scope, Rust drops its remaining fields
// and frees the node allocation. The moved element is returned.
```

Do you see the bug? Horrifyingly, it's actually this line:

```rust ,ignore
debug_assert!(self.len == 1);
```

*Really*? Our friggin' integrity check for tests is a bug?? Yes!!! Well, if we implement our collection right it *shouldn't* be, but it can turn something benign like "oh we are doing a bad job of keeping len up to date" into *An Exploitable Memory Safety Bug*! Why? Because it can panic! Most of the time you don't have to think or worry about panics, but once you start writing *really* unsafe code and playing fast and loose with "invariants", you need to become hyper-vigilant about panics!

We've gotta talk about [*exception safety*](https://doc.rust-lang.org/nomicon/exception-safety.html) (AKA panic safety, AKA unwind safety, ...).

With Rust's default panic strategy, panics *unwind*. Unwinding is a fancy way to say that the stack is walked back and each function returns early while its local values are dropped. A crate can instead be built with `panic = "abort"`, in which case a panic terminates the process without unwinding. With unwinding, you might think "if everyone returns then the program is about to die, so why care about it?", but you'd be wrong!

We have to care for two reasons: destructors run when a function returns, and the unwind can be *caught*. In both cases, code can keep running after a panic, so we need to be very careful and make sure our unsafe collections are always in *some* kind of coherent state whenever a panic could occur, because each panic is an implicit early return!

Let's think about what state our collection is in when we get to that line:

We have our boxed_node on the stack, and we've extracted the element from it. If we were to return at this point, the Box would be dropped, and the node would be freed. Do you see it now..? self.back is still pointing at that freed node! Once we implement the rest of our collection and start using self.back for things, this could result in a use-after-free! Yikes!

Interestingly, this line has similar problems, but it's much safer:

```rust ,ignore
self.len -= 1;
```

By default in debug builds Rust checks for underflows and overflows and will panic when they happen. Yes, every arithmetic operation is a panic-safety hazard! This one is *better* because it happens after we've repaired all of our invariants, so it won't cause memory-safety issues... as long as we don't trust len to be right, but then, if we underflow it's definitely wrong, so we were dead either way! The debug assert is in some sense *worse* because it can escalate a minor issue into a critical one!

I've brought up the term "invariants" a few times, and that's because it's a really useful concept for panic-safety! Basically, to an outside observer of our collection, there are certain property we're always upholding. For a LinkedList, one of those is that any node that is reachable in our list is still allocated and initialized.

*Inside* the implementation we have a bit more flexibility to break invariants *temporarily* as long as we make sure to repair them *before anyone notices*. This is actually one of the "killer apps" of Rust's ownership and borrowing system for collections: if an operation requires an `&mut Self`, then we are *guaranteed* that we have exclusive access to our collection and that it's fine for us to temporarily break invariants, safe in the knowledge that no one can sneakily mess with it.

Perhaps the greatest expression of this is [Vec::drain](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.drain), which actually lets you completely smash a core invariant of Vec and start moving values out from the *front* or even *middle* of a Vec. The reason this is *sound* is because the Drain iterator that we return holds an `&mut` to the Vec, and so all access is gated behind it! No one can observe the Vec until the Drain iterator goes away, and then its destructor can "repair" the Vec before anyone can notice, it's perfe--

[It's not perfect](https://doc.rust-lang.org/nomicon/leaking.html#drain). Unfortunately, you [can't rely on destructors in code you don't control to run](https://doc.rust-lang.org/std/mem/fn.forget.html). When `Vec::drain(range)` starts, it shortens the vector's length to the start of the drained range. When the `Drain` is dropped, it drops the removed values and shifts the untouched tail back into place. If the iterator is leaked instead, the `Vec` still has a valid length, but values after that prefix can be leaked too. That's how `Drain` keeps the vector safe even when its destructor never runs: it may lose data, but the vector's length never includes moved or uninitialized elements. You leak me? I leak you! An eye for an eye! True justice! See [`Vec::drain`'s leaking behavior](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.drain).

For a situation where you *can* actually use destructors for panic-safety, check out the [BinaryHeap::sift_up case study](https://doc.rust-lang.org/nomicon/exception-safety.html#binaryheapsift_up).

Anyway, we won't be needing all of this fancy stuff for our LinkedLists, we just need to be a bit more vigilant about where we break our invariants, what we trust/require to be correct, and to avoid introducing unnecessary unwinds in the middle of hairy tasks.

In this case, we have two options to make our code a bit more robust:

* Use operations like Option::take a lot more aggressively, because they are more "transactional" and have a tendency to preserve invariants.

* Kill the debug_asserts and trust ourselves to write better tests with dedicated "integrity check" functions that won't run in user code ever.

In principle I like the first option, but it doesn't actually work great for a doubly-linked list, because everything is doubly-redundantly encoded. Option::take wouldn't fix the problem here, but moving the debug_assert down a line would. But really, why make things harder for ourselves? Let's just remove those debug_asserts, and make sure anything can panic is at the start or end of our methods, where our invariants should be known to hold.

(In this way it's perhaps more accurate to think of them as *preconditions* and *postconditions* but you really should endeavour to treat them as invariants as much as possible!)

Here's our full implementation now:

```rust
use std::ptr::NonNull;
use std::marker::PhantomData;

pub struct LinkedList<T> {
    front: Link<T>,
    back: Link<T>,
    len: usize,
    _boo: PhantomData<T>,
}

type Link<T> = Option<NonNull<Node<T>>>;

struct Node<T> {
    front: Link<T>,
    back: Link<T>,
    elem: T, 
}

impl<T> LinkedList<T> {
    pub fn new() -> Self {
        Self {
            front: None,
            back: None,
            len: 0,
            _boo: PhantomData,
        }
    }

    pub fn push_front(&mut self, elem: T) {
        // SAFETY: it's a linked-list, what do you want?
        unsafe {
            let new = NonNull::new_unchecked(Box::into_raw(Box::new(Node {
                front: None,
                back: None,
                elem,
            })));
            if let Some(old) = self.front {
                // Put the new front before the old one
                (*old.as_ptr()).front = Some(new);
                (*new.as_ptr()).back = Some(old);
            } else {
                // If there's no front, then we're the empty list and need 
                // to set the back too.
                self.back = Some(new);
            }
            // These things always happen!
            self.front = Some(new);
            self.len += 1;
        }
    }

    pub fn pop_front(&mut self) -> Option<T> {
        unsafe {
            // Only have to do stuff if there is a front node to pop.
            self.front.map(|node| {
                // Rebuild the owning Box from the raw pointer. This transfers
                // ownership of the allocation back to Box.
                let boxed_node = Box::from_raw(node.as_ptr());
                let result = boxed_node.elem;

                // Make the next node into the new front.
                self.front = boxed_node.back;
                if let Some(new) = self.front {
                    // Cleanup its reference to the removed node
                    (*new.as_ptr()).front = None;
                } else {
                    // If the front is now null, then this list is now empty!
                    self.back = None;
                }

                self.len -= 1;
                result
                // When boxed_node leaves scope, Rust drops its remaining fields
                // and frees the node allocation. The moved element is returned.
            })
        }
    }

    pub fn len(&self) -> usize {
        self.len
    }
}
```

What can panic here? Well, knowing that honestly requires you to be a bit of a Rust expert, but thankfully, I am!

The length arithmetic can panic on overflow in debug builds, so we need to know exactly what state the list is in when it runs. `Box::new` can fail to allocate; in a normal `std` program, the default response to allocation failure is to abort rather than unwind. Even if allocation-error handling is customized to unwind, this allocation happens before we change any links, so the list is still intact. Both cases are easier to reason about than a panic halfway through pointer updates.

Try to keep operations that can unwind away from the middle of pointer updates, and leave the collection in a valid state before returning or unwinding.

