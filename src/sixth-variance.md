# Variance and PhantomData

It's going to be annoying to punt on this now and fix it later, so we're going to do the Hardcore Layout stuff now.

There are five terrible horsemen of making unsafe Rust collections:

1. [Variance](https://doc.rust-lang.org/nomicon/subtyping.html)
2. [Drop Check](https://doc.rust-lang.org/nomicon/dropck.html)
3. [NonNull Optimizations](https://doc.rust-lang.org/std/ptr/struct.NonNull.html)
4. [The isize::MAX Allocation Rule](https://doc.rust-lang.org/nomicon/vec/vec-alloc.html)
5. [Zero-Sized Types](https://doc.rust-lang.org/nomicon/vec/vec-zsts.html)

Mercifully, the last 2 aren't going to be a problem for us. 

The third we *could* make into our problem but it's more trouble than it's worth -- if you've opted into a LinkedList you've already given up the battle on memory-effeciency 100-fold already.

The second is something that I used to insist was really important and that std messes around with, but the defaults are safe, the ways to mess with it are unstable, and you need to try *so very hard* to ever notice the limitations of the defaults, so, don't worry about it.

That just leaves us with Variance. To be honest, you can probably punt on this one too, but I still have my pride as a Collections Person, so we're going to Do The Variance Thing.

So, surprise: Rust has subtyping. In particular, `&'big T` is a *subtype* of `&'small T`. Why? Well because if some code needs a reference that lives for some particular region of the program, it's usually perfectly fine to give it a reference that lives for *longer*. Like, intuitively that's just true, right?

Why is this important? Well imagine some code that takes two values with the same type:

```rust ,ignore
fn take_two<T>(_val1: T, _val2: T) { }
```

This is some deeply boring code, and so we should expect it to work with T=&u32 fine, right?

```rust
fn two_refs<'big: 'small, 'small>(
    big: &'big u32, 
    small: &'small u32,
) {
    take_two(big, small);
}

fn take_two<T>(_val1: T, _val2: T) { }
```

Yep, that compiles fine!

Now let's have some fun and wrap it in, oh, I don't know, `std::cell::Cell`:

```rust ,compile_fail
use std::cell::Cell;

fn two_refs<'big: 'small, 'small>(
    // NOTE: these two lines changed
    big: Cell<&'big u32>, 
    small: Cell<&'small u32>,
) {
    take_two(big, small);
}

fn take_two<T>(_val1: T, _val2: T) { }
```

```text
error[E0623]: lifetime mismatch
 --> src/main.rs:7:19
  |
4 |     big: Cell<&'big u32>, 
  |               ---------
5 |     small: Cell<&'small u32>,
  |                 ----------- these two types are declared with different lifetimes...
6 | ) {
7 |     take_two(big, small);
  |                   ^^^^^ ...but data from `small` flows into `big` here
```

Huh??? We didn't touch the lifetimes, why's the compiler angry now!?

Ah well, the lifetime "subtyping" stuff must be really simple, so it falls over if you wrap the references in anything, see look it breaks with Vec too:

```rust
fn two_refs<'big: 'small, 'small>(
    big: Vec<&'big u32>, 
    small: Vec<&'small u32>,
) {
    take_two(big, small);
}

fn take_two<T>(_val1: T, _val2: T) { }
```

```text
    Finished dev [unoptimized + debuginfo] target(s) in 1.07s
     Running `target/debug/playground`
```

See it doesn't compile eith-- wait what??? Vec is magic??????

Well, yes. But also, no. The magic was inside us all along, and that magic is ✨*Variance*✨.

Read the [Nomicon's chapter on subtyping](https://doc.rust-lang.org/nomicon/subtyping.html) if you want all the gory details, but basically subtyping *isn't* always safe. In particular it's not safe when mutable references are involved because you can use things like `mem::swap` and suddenly oops dangling pointers!

Types that can both read and replace a `T` through shared access must be
*invariant* in `T`: they cannot allow a longer-lived `T` to be treated as a
shorter-lived one (or vice versa). `&mut T` is invariant in `T`, and `Cell<T>`
is invariant because its methods can replace the stored value through `&Cell<T>`.

Almost everything that isn't invariant is *covariant*, and that just means that subtyping "passes through" it and continues to work normally (there are also contravariant types that make subtyping go backwards but they are really rare and no one likes them so I won't mention them again).

Collections often contain mutable pointers internally, but an owning
collection can still be covariant. For example, `Vec<T>` owns its elements;
replacing or mutating them requires exclusive access to the vector. That means
it can safely allow the same lifetime shortening as `T`, so `Vec<T>` is
covariant in `T`.

Unfortunately, this definition is invariant:

```rust
pub struct LinkedList<T> {
    front: Link<T>,
    back: Link<T>,
    len: usize,
}

type Link<T> = *mut Node<T>;

struct Node<T> {
    front: Link<T>,
    back: Link<T>,
    elem: T, 
}
```

But how is Rust actually deciding the variance of things? Well in the good-old-days before 1.0 we messed around with just letting people specify the variance they wanted and... it was an absolute train-wreck! Subtyping and variance is really hard to wrap your head around, and core developers genuinely disagreed on basic terminology! So we moved to a "variance by example" approach: the compiler just looks at your fields and copies their variances. If there's any kind of disagreement, then invariance always wins, because that's safe.

So what's in our type definitions that Rust is getting mad about? `*mut`!

Raw pointers in Rust really just try to let you do whatever, but they have exactly one safety feature: because most people have no idea that variance and subtyping are a thing in Rust, and being *incorrectly* covariant would be horribly dangerous, `*mut T` is invariant, because there's a good chance it's being used "as" `&mut T`.

This is extremely annoying for Exactly Me as a person who has spent a lot of time writing collections in Rust. This is why when I made [std::ptr::NonNull](https://doc.rust-lang.org/std/ptr/struct.NonNull.html), I added this little piece of magic:

> Unlike `*mut T`, `NonNull<T>` was chosen to be covariant over `T`. This makes it possible to use `NonNull<T>` when building covariant types, but introduces the risk of unsoundness if used in a type that shouldn’t actually be covariant.

But hey, its interface is built around `*mut T`, so how can it be covariant?
The important part for us is the documented behavior: `NonNull<T>` is a
non-null raw pointer wrapper that is covariant over `T`. Its private
representation is an implementation detail, so we should not depend on the
field layout. A pointer wrapper could achieve covariance by storing a
`*const T` internally and exposing the appropriate raw-pointer operations, but
that is only an illustration of the idea, not a promise about `NonNull`'s
internals.

NOPE. NO MAGIC HERE! The useful lesson is that `NonNull` gives collections the
covariance they need, while still allowing raw-pointer operations. This choice
is only correct when the containing type is itself soundly covariant; if it can
replace a `T` through shared access, it needs an invariant marker instead.
Enjoy your subtyping footgun!

The solution to all your problems is to use NonNull, and then if you want to have nullable pointers again, use `Option<NonNull<T>>`. Are we really going to bother doing that..?

Yep! It sucks, but we're making *production grade linked lists* so we're going to eat all our vegetables and do things the hard way (we could just use bare `*const T` and cast everywhere, but I genuinely want to see how painful this is... for Ergonomics Science).


So here's our final type definitions:

```rust
use std::ptr::NonNull;

// !!!This changed!!!
pub struct LinkedList<T> {
    front: Link<T>,
    back: Link<T>,
    len: usize,
}

type Link<T> = Option<NonNull<Node<T>>>;

struct Node<T> {
    front: Link<T>,
    back: Link<T>,
    elem: T, 
}
```

...wait, one last thing. Our links use raw pointers, so their fields do not
show that the list owns the values in its separately allocated nodes. We can
express that relationship with a zero-sized marker:

```rust ,ignore
use std::marker::PhantomData;

pub struct LinkedList<T> {
    front: Link<T>,
    back: Link<T>,
    len: usize,
    /// We semantically store values of T by-value.
    _boo: PhantomData<T>,
}
```

`PhantomData` is not a safety shield that belongs beside every raw pointer.
Use it when the real relationship between your type and some `T` or lifetime
is missing from its fields. Here, `LinkedList<T>` owns `T` values through its
allocated nodes, but its links are raw pointers, so `_boo: PhantomData<T>`
tells the compiler to treat the list as though it owns `T`. That affects
properties such as drop checking and auto traits; it does not validate a
pointer or make an unsafe operation sound by itself.

The exact interaction with [drop checking](https://doc.rust-lang.org/nomicon/dropck.html)
is subtle, so we will use the marker that matches this list's ownership and
leave the full rules for another time. (The `Node<T>` itself stores `T`
directly, so it does not need this marker.)


...ok for real we're done with layout now! On to actual basic functionality!
