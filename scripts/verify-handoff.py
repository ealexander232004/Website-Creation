"""Verify every transferred file against the package SHA256SUMS manifest."""
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
count = 0
for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    expected, relative = line.split("  ", 1)
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise SystemExit(f"Unsafe manifest path: {relative}")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch: {relative}")
    count += 1
print(f"Verified {count} files.")
