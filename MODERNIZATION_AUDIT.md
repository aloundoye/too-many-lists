# Modernization audit

Baseline: original commit `1b0b264`; reference: sibling `too-many-lists-master`.
The sibling is unchanged. This revision starts from the original, so removed
educational material is preserved rather than copied back from the sibling.

## Reference decisions

| Chapter | Decision |
| --- | --- |
| `README.md` | Adapt: select Rust 2024 and distinguish edition support from illustrative diagnostics; preserve the introduction. |
| `SUMMARY.md` | Reject renaming: keep original chapter labels and ordering. |
| `fifth-basics.md` | Adapt pointer safety explanation; preserve the intentionally broken boxed queue and its ordinary passing test before Miri rejects it. |
| `fifth-extras.md` | Adapt Miri commands; preserve the iterator derivation and PhantomData investigation. |
| `fifth-layout-basics-redux.md` | Adapt commands and shorthand; retain the explicit old/new layout comparison and raw ownership algorithm. |
| `fifth-miri.md` | Adapt setup and dated-nightly explanation; preserve dialogue, first UB report, stack-trace investigation, and transition to aliasing. |
| `fifth-stacked-borrows.md` | Adapt default-check commands and model terminology; retain the borrow-stack derivation and raw-pointer heuristic. |
| `fifth-testing-stacked-borrows.md` | Adapt commands and modern lint explanation; test all executable experiments and both compiler-rejected intermediate casts/borrows. |
| `fifth-unsafe.md` | Adapt unsafe-function/block distinction, pointer access requirements and Rust 2024 lint; retain raw-pointer introduction. |
| `first-drop.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first-final.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first-layout.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first-new.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first-ownership.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first-pop.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first-push.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first-test.md` | Reject narrative compression and early Option representation; retain original progression. |
| `first.md` | Reject narrative compression and early Option representation; retain original progression. |
| `fourth-breaking.md` | Adapt Result/Option and Debug-bound reasoning; retain the failed unwrap and ok().unwrap() workaround. |
| `fourth-building.md` | Adapt the structural-owner invariant to distinguish temporary Rc clones; preserve all pointer updates. |
| `fourth-final.md` | Retain explicit guard lifetimes; keep the final algorithm and test cases. |
| `fourth-layout.md` | Adapt RefCell borrowing guards, runtime failure, and strong cycles; preserve the doubly-linked layout. |
| `fourth-peek.md` | Adapt guard lifetimes and explicit elision; retain failed reference returns and Ref::map solution, with a 2024 temporary-scope note. |
| `fourth-symmetry.md` | Adapt guard lifetimes and shorthand consistently with peek and final code. |
| `second-into-iter.md` | Retain original has-next/get-next reasoning and wrapper derivation; clarify the inherent method versus IntoIterator trait. |
| `second-iter.md` | Retain lifetime derivation, failed attempts and elision comparisons; clarify inferred use regions rather than lexical scope guarantees. |
| `second-option.md` | Reject narrative compression and early Option representation; retain original progression. |
| `sixth-basics.md` | Adapt PhantomData and partial-move/deallocation comments; preserve the intentionally failed NonNull dereference attempt. |
| `sixth-combinatorics.md` | Adapt lifetimes and ownership comments across repeated implementations; preserve the trait derivations. |
| `sixth-cursors-intro.md` | Retain cursor design trade-offs; fix iter.next() receiver and iterator mutability. |
| `sixth-cursors-testing.md` | Remove obsolete Miri environment flag; preserve cursor test scenarios. |
| `sixth-final.md` | Adapt lifetimes, shared Iter Send bound and partial moves; use mem::take only after Default has been taught. |
| `sixth-layout.md` | Retain original type layout and cursor motivation; qualify the historical standard-library cursor link. |
| `sixth-panics.md` | Adapt unwind/abort, allocation failure and drain leakage; preserve the panic-safety reasoning and examples. |
| `sixth-random-bits.md` | Adapt explicit lifetimes and ownership comments; preserve trait implementations and repeated code. |
| `sixth-send-sync.md` | Adapt shared iterator Send to T: Sync and explain the reference relationship; preserve compile-test and invariance reasoning. |
| `sixth-testing.md` | Remove obsolete Miri flag; retain ordinary tests and comparison with dynamic checks. |
| `sixth-variance.md` | Adapt guarantees versus private NonNull representation, covariance and PhantomData; correct compile_fail annotation and preserve counterexamples. |
| `sixth.md` | Retain chapter framing and historical authorial context. |
| `third-arc.md` | Adapt Arc bounds, atomics and interior mutability; preserve the Rc/Arc cost comparison. |
| `third-basics.md` | Adapt cloning semantics and shorthand; preserve shared-tail construction and Option cloning. |
| `third-layout.md` | Retain original shared-tail diagram and GC trade-offs; qualify mutation and extraction restrictions under shared ownership. |

Executable reference changes: reject Chapter 1's Option conversion; retain
explicit lifetimes in second/fourth. Configuration: retain Rust 2024 and authors
array, and additionally select Rust 2024 for mdBook. Preserve algorithms and
public methods. Field shorthand is applied consistently to repeated listings.

## Verification

Run `cargo test --manifest-path lists/Cargo.toml`,
`python3 scripts/check_examples.py`, `mdbook build`, and `mdbook test`.
The extraction checks include the real nested Chapter 6 rustdoc test using a
crate named linked_list. Context-dependent cursor fragments are explicitly
ignored; their complete implementation is tested through the final listing.
Miri uses nightly; historical transcripts are identified rather than presented
as current captured output. Miri execution and the wider prose accuracy review
must be reported separately from ordinary test results.

## Verification record

Status: the stable crate tests, all six extracted listings, actual Miri
listing checks, aliasing experiments, book build and book tests pass.
The crate also passes its 19 tests under Miri.


The earlier claim that CHECK_MIRI verified the final listings was incorrect:
the script ignored the environment variable. It now explicitly chooses and
prints `cargo +nightly miri test` when CHECK_MIRI=1. The rerun actually invokes
Miri for every extracted package.

Commands: `cargo test --manifest-path lists/Cargo.toml`,
`python3 scripts/check_examples.py`, `CHECK_MIRI=1 python3 scripts/check_examples.py`,
`python3 scripts/check_aliasing.py`, `mdbook build`, `mdbook test`.
The aliasing checker executes all 21 executable experiments (three compiler
errors, seven UB reports, eleven successful runs), excludes the two stdlib type
illustrations, and reconstructs the original broken queue from chapter excerpts
to confirm its UB report. The double-cast experiment alone permits the current
invalid_reference_casting lint so Miri can demonstrate its dynamic failure.
All captured diagnostic transcripts remain illustrative rather than golden output.

Rendered HTML: 61 pages checked for local target paths and fragment identifiers;
zero broken links. Browser visual inspection of local files was blocked by the
browser URL policy; no visual screenshot review is claimed.

Tested tools: Rust 1.98.1; mdBook 0.5.4; nightly Rust 1.100.0
(420ed2a0c, 2026-09-18). CI selects stable for ordinary tests and nightly for
Miri; it does not pin or change the existing publication branch behavior.

## Idioms retained intentionally

Chapter 1 uses a custom enum and mem::replace to teach replacement through a
borrow. Chapter 2 translates it to Option before introducing take and map.
Later closure projections use expression bodies; cursor whole-list replacement
uses mem::take with an explanation grounded in the already-introduced Default.
The explicit Box::into_raw/from_raw ownership cycle, Ref::map guards, manual
iterator implementations and Rc::try_unwrap(...).ok().unwrap() remain because
they teach the chapter's ownership, Debug-bound, and lifetime mechanisms.
New trait implementations or pointer abstractions are not introduced just to
silence stylistic lints before readers have the necessary context.
