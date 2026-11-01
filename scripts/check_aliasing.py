#!/usr/bin/env python3
"""Execute the book's aliasing experiments; never run UB as native code."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'src/fifth-testing-stacked-borrows.md').read_text()
blocks = list(re.finditer(r'^```rust[^\n]*\n(.*?)^```', source, re.M | re.S))
# Ordinals identify the original progression, including failing intermediate code.
compile_errors = {1: 'E0503', 8: 'E0499', 12: 'E0606'}
undefined = {2, 3, 5, 13, 15, 19, 22}
illustrations = {17, 18}  # stdlib type definitions, not executable experiments
with tempfile.TemporaryDirectory(prefix='list-aliasing-') as directory:
    root = Path(directory)
    (root / 'src').mkdir()
    (root / 'Cargo.toml').write_text('[package]\nname="aliasing_examples"\nversion="0.0.0"\nedition="2024"\n')
    for number, block in enumerate(blocks, 1):
        if number in illustrations:
            continue
        code = block.group(1)
        if number == 13:
            code = blocks[11].group(1).replace('let sref3 = &mref1;', 'let sref3 = &*mref1;').replace('sref3 as *mut i32', 'sref3 as *const i32 as *mut i32')
            # Intentionally bypass the static lint ONLY to demonstrate the dynamic error.
            code = '#[allow(invalid_reference_casting)]\nfn main() {\n' + code + '\n}'
        else:
            code = 'fn main() {\n' + code + '\n}'
        (root / 'src/main.rs').write_text(code)
        command = ['cargo', '+nightly', 'check'] if number in compile_errors else ['cargo', '+nightly', 'miri', 'run']
        result = subprocess.run(command + ['--manifest-path', str(root / 'Cargo.toml')], text=True, capture_output=True)
        if number in compile_errors:
            valid = result.returncode != 0 and compile_errors[number] in result.stderr
            expected = compile_errors[number]
        elif number in undefined:
            valid = result.returncode != 0 and 'Undefined Behavior' in result.stderr
            expected = 'Undefined Behavior'
        else:
            valid = result.returncode == 0
            expected = 'success'
        print(f'example {number}, line {source[:block.start()].count(chr(10))+1}: expected {expected}: {"PASS" if valid else "FAIL"}', flush=True)
        if not valid:
            raise RuntimeError(result.stdout + result.stderr)

# Reconstruct the intentionally broken queue from its actual chapter excerpts.
basics = (ROOT / 'src/fifth-basics.md').read_text()
parts = re.findall(r'^```rust[^\n]*\n(.*?)^```', basics, re.M | re.S)
layout = (ROOT / 'src/fifth-layout-basics-redux.md').read_text()
old_layout = re.findall(r'^```rust[^\n]*\n(.*?)^```', layout, re.M | re.S)[0]
constructor = next(part for part in parts if 'pub fn new()' in part and 'ptr::null_mut()' in part)
push = next(part for part in parts if 'pub fn push(' in part and 'unsafe {' in part)
pop = next(part for part in parts if 'pub fn pop(' in part)
tests = next(part for part in parts if '#[cfg(test)]' in part)
with tempfile.TemporaryDirectory(prefix='broken-queue-') as directory:
    root = Path(directory)
    (root / 'src').mkdir()
    (root / 'Cargo.toml').write_text('[package]\nname="broken_queue"\nversion="0.0.0"\nedition="2024"\n')
    (root / 'src/lib.rs').write_text(old_layout + '\n' + constructor + '\nimpl<T> List<T> {\n' + push + pop + '\n}\n' + tests)
    result = subprocess.run(['cargo', '+nightly', 'miri', 'test', '--manifest-path', str(root / 'Cargo.toml')], text=True, capture_output=True)
    if result.returncode == 0 or 'Undefined Behavior' not in result.stderr:
        raise RuntimeError(result.stdout + result.stderr)
    print('original boxed queue: expected Undefined Behavior: PASS', flush=True)
