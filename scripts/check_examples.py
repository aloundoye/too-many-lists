#!/usr/bin/env python3
"""Test the actual final listings, including their nested rustdoc tests."""
from pathlib import Path
import re
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='linked-list-examples-') as directory:
    for chapter in ('first', 'second', 'third', 'fourth', 'fifth', 'sixth'):
        source = (ROOT / 'src' / f'{chapter}-final.md').read_text()
        blocks = re.findall(r'^```rust[^\n]*\n(.*?)^```\s*$', source, re.M | re.S)
        assert blocks, chapter
        package = Path(directory) / chapter
        (package / 'src').mkdir(parents=True)
        name = 'linked_list' if chapter == 'sixth' else f'example_{chapter}'
        (package / 'Cargo.toml').write_text(
            f'[package]\nname = "{name}"\nversion = "0.0.0"\nedition = "2024"\n')
        (package / 'src/lib.rs').write_text('\n'.join(blocks))
        if chapter == 'second':
            with (package / 'src/lib.rs').open('a') as output:
                output.write("""
#[test]
fn non_copy_and_long_cleanup() {
    let mut list = List::new();
    list.push(String::from("owned"));
    assert_eq!(list.pop().as_deref(), Some("owned"));
    for _ in 0..10_000 { list.push(String::new()); }
    drop(list);
}
""")
        if chapter == 'third':
            with (package / 'src/lib.rs').open('a') as output:
                output.write("""
#[test]
fn shared_tail_is_dropped_once() {
    use std::cell::Cell;
    struct Counted<'a>(&'a Cell<usize>);
    impl Drop for Counted<'_> {
        fn drop(&mut self) { self.0.set(self.0.get() + 1); }
    }
    let count = Cell::new(0);
    let tail = List::new().prepend(Counted(&count));
    let branch = tail.prepend(Counted(&count));
    drop(branch);
    assert_eq!(count.get(), 1);
    assert!(tail.head().is_some());
    drop(tail);
    assert_eq!(count.get(), 2);
}
""")
        if chapter == 'sixth':
            with (package / 'src/lib.rs').open('a') as output:
                output.write("""
/// Shared iterators cannot send access to a non-Sync Cell across threads.
/// ```compile_fail
/// use linked_list::Iter;
/// use std::cell::Cell;
/// fn require_send<T: Send>() {}
/// require_send::<Iter<'static, Cell<i32>>>();
/// ```
pub struct ThreadSafetyRegression;
#[test]
fn shared_iterator_accepts_sync_only_elements() {
    fn require_send<T: Send>() {}
    // MutexGuard is Sync for i32, but is not Send.
    require_send::<Iter<'static, std::sync::MutexGuard<'static, i32>>>();
}
""")
        command = ['cargo', '+nightly', 'miri', 'test'] if os.environ.get('CHECK_MIRI') == '1' else ['cargo', 'test']
        print(f"{chapter}: {' '.join(command)}", flush=True)
        subprocess.run(command + ['--manifest-path', str(package / 'Cargo.toml')], check=True)

# Keep ownership failures distinct from missing-context/import failures.
failures = {
    'borrowed_field': ('E0507', '''
struct List { head: Option<Box<i32>> }
impl List { fn take_head(&mut self) -> Option<Box<i32>> { self.head } }
fn main() {}
'''),
    'mutable_iteration': ('E0596', '''
struct List { head: Option<Box<i32>> }
impl List { fn iter_mut(&self) -> Option<&mut i32> { self.head.as_deref_mut() } }
fn main() {}
'''),
    'escaping_guard': ('E0515', '''
use std::cell::RefCell;
fn peek(cell: &RefCell<i32>) -> &i32 { &*cell.borrow() }
fn main() {}
'''),
}
with tempfile.TemporaryDirectory(prefix='linked-list-errors-') as directory:
    for name, (error, source) in failures.items():
        path = Path(directory) / f'{name}.rs'
        path.write_text(source)
        result = subprocess.run(['rustc', '--edition=2024', str(path),
                                 '--out-dir', directory], capture_output=True, text=True)
        assert result.returncode != 0 and error in result.stderr, (name, result.stderr)
