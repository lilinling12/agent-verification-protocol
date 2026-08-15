"""Canonicalize non-semantic archive metadata in a Python source distribution.

File bytes and tar member order are preserved. Timestamps, ownership metadata,
PAX headers, and gzip wrapper metadata are normalized so repeated builds can be
compared byte-for-byte without masking real content or ordering drift.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import io
import tarfile
from pathlib import Path


class NormalizationError(ValueError):
    """Raised when the requested source distribution cannot be normalized."""


def _canonical_member(member: tarfile.TarInfo, *, mtime: int) -> tarfile.TarInfo:
    canonical = copy.copy(member)
    canonical.mtime = mtime
    canonical.uid = 0
    canonical.gid = 0
    canonical.uname = ""
    canonical.gname = ""
    canonical.pax_headers = {}
    return canonical


def normalize(path: Path, *, mtime: int) -> None:
    if mtime < 0:
        raise NormalizationError("mtime must be non-negative")
    if not path.is_file() or not path.name.endswith(".tar.gz"):
        raise NormalizationError(f"expected an existing .tar.gz source distribution: {path}")

    try:
        with tarfile.open(path, mode="r:gz") as source:
            members = source.getmembers()
            payloads: list[tuple[tarfile.TarInfo, bytes | None]] = []
            for member in members:
                extracted = source.extractfile(member) if member.isfile() else None
                payloads.append((member, extracted.read() if extracted is not None else None))
    except (OSError, EOFError, tarfile.TarError) as exc:
        raise NormalizationError(f"unable to read source distribution archive: {exc}") from exc

    tar_buffer = io.BytesIO()
    try:
        with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as target:
            for member, payload in payloads:
                canonical = _canonical_member(member, mtime=mtime)
                fileobj = io.BytesIO(payload) if payload is not None else None
                target.addfile(canonical, fileobj=fileobj)
    except (OSError, tarfile.TarError) as exc:
        raise NormalizationError(f"unable to write canonical tar archive: {exc}") from exc

    gzip_buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gzip_buffer, mtime=mtime) as target:
        target.write(tar_buffer.getvalue())
    path.write_bytes(gzip_buffer.getvalue())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--mtime", type=int, required=True)
    args = parser.parse_args()
    try:
        normalize(args.path, mtime=args.mtime)
    except NormalizationError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"canonical sdist archive metadata OK: {args.path}")


if __name__ == "__main__":
    main()
