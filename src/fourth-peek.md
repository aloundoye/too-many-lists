# Peeking

Alright, we made it through `push` and `pop`. I'm not gonna lie, it got a
bit emotional there. Compile-time correctness is a hell of a drug.

Let's cool off by doing something simple: let's just implement `peek_front`.
That was always really easy before. Gotta still be easy, right?

Right?

In fact, I think I can just copy-paste it!

```rust ,ignore
pub fn peek_front(&self) -> Option<&T> {
    self.head.as_ref().map(|node| &node.elem)
}
```

Wait. Not this time.

```rust ,ignore
pub fn peek_front(&self) -> Option<&T> {
    self.head.as_ref().map(|node| {
        // BORROW!!!!
        &node.borrow().elem
    })
}
```

HAH.

```text
cargo build

error[E0515]: cannot return value referencing temporary value
  --> src/fourth.rs:66:13
   |
66 |             &node.borrow().elem
   |             ^   ----------^^^^^
   |             |   |
   |             |   temporary value created here
   |             |
   |             returns a value referencing data owned by the current function
```

Ok I'm just burning my computer.

This is exactly the same logic as our singly-linked stack. Why are things
different. WHY.

The answer is really the whole moral of this chapter: RefCells make everything
sadness. Up until now, RefCells have just been a nuisance. Now they're going to
become a nightmare.

So what's going on? To understand that, we need to go back to the definition of
`borrow`:

```rust ,ignore
fn borrow<'a>(&'a self) -> Ref<'a, T>
fn borrow_mut<'a>(&'a self) -> RefMut<'a, T>
```

In the layout section we said:

> `RefCell` checks borrowing rules at runtime: `borrow` and `borrow_mut` panic
> when a requested borrow would break those rules, while `try_borrow` and
> `try_borrow_mut` return errors. The returned `Ref` and `RefMut` values are
> guards that keep the borrow active until they are dropped. **We'll get to that later.**

It's later.

Rust 2024 drops some tail-expression temporaries earlier than older editions.
That does not let a returned reference outlive a `Ref` guard: the guard still
has to stay alive for every use of a reference borrowed through it.

`Ref` and `RefMut` implement `Deref` and `DerefMut`, so Rust lets us use them
much like `&T` and `&mut T`. But each one is a guard, not just a reference:
the borrow must stay active for as long as the guard is alive. The reference
you access through it cannot outlive that guard, which is why returning a bare
`&T` from `peek_front` does not work.

This is in fact necessary for correctness. When a Ref gets dropped, it tells
the RefCell that it's not borrowed anymore. So if we *did* manage to hold onto our
reference longer than the Ref existed, we could get a RefMut while a reference
was kicking around and totally break Rust's type system in half.

So where does that leave us? We only want to return a reference, but we need
to keep this Ref thing around. But as soon as we return the reference from
`peek`, the function is over and the `Ref` goes out of scope.

😖

As far as I know, we're actually totally dead in the water here. You can't
totally encapsulate the use of RefCells like that.

But... what if we just give up on totally hiding our implementation details?
What if we returns Refs?

```rust ,ignore
pub fn peek_front(&self) -> Option<Ref<'_, T>> {
    self.head.as_ref().map(|node| {
        node.borrow()
    })
}
```

```text
> cargo build

error[E0412]: cannot find type `Ref` in this scope
  --> src/fourth.rs:63:40
   |
63 |     pub fn peek_front(&self) -> Option<Ref<'_, T>> {
   |                                        ^^^ not found in this scope
help: possible candidates are found in other modules, you can import them into scope
   |
1  | use core::cell::Ref;
   |
1  | use std::cell::Ref;
   |
```

Blurp. Gotta import some stuff.


```rust ,ignore
use std::cell::{Ref, RefCell};
```

```text
> cargo build

error[E0308]: mismatched types
  --> src/fourth.rs:64:9
   |
64 | /         self.head.as_ref().map(|node| {
65 | |             node.borrow()
66 | |         })
   | |__________^ expected type parameter, found struct `fourth::Node`
   |
   = note: expected type `std::option::Option<std::cell::Ref<'_, T>>`
              found type `std::option::Option<std::cell::Ref<'_, fourth::Node<T>>>`
```

Hmm... that's right. We have a `Ref<Node<T>>`, but we want a `Ref<T>`. We could
abandon all hope of encapsulation and just return that. We could also make
things even more complicated and wrap `Ref<Node<T>>` in a new type to only
expose access to an `&T`.

Both of those options are *kinda* lame.

Instead, we're going to go deeper down. Let's
have some *fun*. Our source of fun is *this beast*:

```rust ,ignore
map<U, F>(orig: Ref<'b, T>, f: F) -> Ref<'b, U>
    where F: FnOnce(&T) -> &U,
          U: ?Sized
```

> Make a new Ref for a component of the borrowed data.

Yes: just like you can map over an Option, you can map over a Ref.

I'm sure someone somewhere is really excited because *monads* or whatever but
I don't care about any of that. Also I don't think it's a proper monad since
there's no None-like case, but I digress.

It's cool and that's all that matters to me. *I need this*.

```rust ,ignore
pub fn peek_front(&self) -> Option<Ref<'_, T>> {
    self.head.as_ref().map(|node| {
        Ref::map(node.borrow(), |node| &node.elem)
    })
}
```

```text
> cargo build
```

Awww yissss

Let's make sure this is working by munging up the test from our stack. We need
to do some munging to deal with the fact that Refs don't implement comparisons.

```rust ,ignore
#[test]
fn peek() {
    let mut list = List::new();
    assert!(list.peek_front().is_none());
    list.push_front(1); list.push_front(2); list.push_front(3);

    assert_eq!(&*list.peek_front().unwrap(), &3);
}
```


```text
> cargo test

     Running target/debug/lists-5c71138492ad4b4a

running 10 tests
test first::test::basics ... ok
test fourth::test::basics ... ok
test second::test::basics ... ok
test fourth::test::peek ... ok
test second::test::iter_mut ... ok
test second::test::into_iter ... ok
test third::test::basics ... ok
test second::test::peek ... ok
test second::test::iter ... ok
test third::test::iter ... ok

test result: ok. 10 passed; 0 failed; 0 ignored; 0 measured

```

Great!
