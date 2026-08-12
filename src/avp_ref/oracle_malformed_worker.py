"""Conformance fixture that intentionally violates the Oracle worker protocol."""

import sys


if __name__ == "__main__":
    sys.stdin.buffer.read()
    sys.stdout.buffer.write(b"not-json\n")
    sys.stdout.buffer.flush()
