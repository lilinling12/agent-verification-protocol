"""Canonicalize gzip wrapper metadata for a Python source distribution.

The tar payload is preserved byte-for-byte. Only the gzip container is
re-emitted with a caller-supplied mtime and without an embedded filename so
repeated builds of the same tar payload can be compared byte-for-byte.
"""

from __future__ import annotations

import argparse
import gzip
import io
from pathlib import Path


class NormalizationError(ValueError):
    """Raised when the requested source distribution cannot be normalized."""


def normalize(path: Path, *, mtime: int) -> None:
    if mtime < 0:
        raise NormalizationError("mtime must be non-negative")
    if not path.is_file() or not path.name.endswith(".tar.gz"):
        raise NormalizationError(f"expected an existing .tar.gz source distribution: {path}")

    try:
        with gzip.open(path, "rb") as source:
            tar_payload = source.read()
    except (OSError, EOFError) as exc:
        raise NormalizationError(f"unable to read gzip source distribution: {exc}") from exc

    # Re-emit a canonical gzip wrapper. The uncompressed tar archive itself is
    # deliberately not rewritten: reproducibility must still fail if tar member
    # order, metadata, or file bytes differ between builds.
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=mtime) as target:
        target.write(tar_payload)
    path.write_bytes(buffer.getvalue())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--mtime", type=int, required=True)
    args = parser.parse_args()
    try:
        normalize(args.path, mtime=args.mtime)
    except NormalizationError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"canonical sdist gzip wrapper OK: {args.path}")


if __name__ == "__main__":
    main()
