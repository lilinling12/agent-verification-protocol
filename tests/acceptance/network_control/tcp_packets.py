"""Narrow TCP SYN frame parsing used by the concrete TEL-001 Linux witness."""

from __future__ import annotations

import ipaddress
import struct
from dataclasses import dataclass

_ETH_P_IP = 0x0800
_ETH_P_IPV6 = 0x86DD
_ETH_P_8021Q = 0x8100
_ETH_P_8021AD = 0x88A8
_IPPROTO_TCP = 6
_TCP_SYN = 0x02
_TCP_ACK = 0x10


class PacketParseError(ValueError):
    """Raised when a boundary frame cannot be normalized without ambiguity."""


@dataclass(frozen=True, slots=True)
class ParsedSyn:
    family: str
    source_address: str
    source_port: int
    destination_address: str
    destination_port: int
    sequence: int


def parse_initial_syn(frame: bytes) -> ParsedSyn | None:
    """Parse Ethernet/VLAN IPv4/IPv6 TCP initial SYN evidence."""

    if len(frame) < 14:
        raise PacketParseError("truncated-ethernet-frame")
    offset = 14
    ether_type = struct.unpack_from("!H", frame, 12)[0]
    for _ in range(2):
        if ether_type not in {_ETH_P_8021Q, _ETH_P_8021AD}:
            break
        if len(frame) < offset + 4:
            raise PacketParseError("truncated-vlan-header")
        ether_type = struct.unpack_from("!H", frame, offset + 2)[0]
        offset += 4
    if ether_type in {_ETH_P_8021Q, _ETH_P_8021AD}:
        raise PacketParseError("unsupported-vlan-depth")

    if ether_type == _ETH_P_IP:
        return _parse_ipv4_syn(frame, offset)
    if ether_type == _ETH_P_IPV6:
        return _parse_ipv6_syn(frame, offset)
    return None


def build_synthetic_syn_frame(
    *,
    source_address: str,
    destination_address: str,
    source_port: int,
    destination_port: int,
    sequence: int,
) -> bytes:
    """Build checksum-agnostic raw frames for parser/normalizer unit tests."""

    source = ipaddress.ip_address(source_address)
    destination = ipaddress.ip_address(destination_address)
    if source.version != destination.version:
        raise ValueError("synthetic packet endpoints must share an address family")
    ethernet = b"\x00" * 12
    tcp = struct.pack(
        "!HHIIBBHHH",
        source_port,
        destination_port,
        sequence,
        0,
        5 << 4,
        _TCP_SYN,
        65535,
        0,
        0,
    )
    if source.version == 4:
        total_length = 20 + len(tcp)
        ipv4 = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,
            0,
            total_length,
            0,
            0,
            64,
            _IPPROTO_TCP,
            0,
            source.packed,
            destination.packed,
        )
        return ethernet + struct.pack("!H", _ETH_P_IP) + ipv4 + tcp
    ipv6 = struct.pack(
        "!IHBB16s16s",
        6 << 28,
        len(tcp),
        _IPPROTO_TCP,
        64,
        source.packed,
        destination.packed,
    )
    return ethernet + struct.pack("!H", _ETH_P_IPV6) + ipv6 + tcp


def _parse_ipv4_syn(frame: bytes, offset: int) -> ParsedSyn | None:
    if len(frame) < offset + 20:
        raise PacketParseError("truncated-ipv4-header")
    first = frame[offset]
    if first >> 4 != 4:
        raise PacketParseError("invalid-ipv4-version")
    header_length = (first & 0x0F) * 4
    if header_length < 20 or len(frame) < offset + header_length:
        raise PacketParseError("invalid-ipv4-header-length")
    protocol = frame[offset + 9]
    if protocol != _IPPROTO_TCP:
        return None
    flags_fragment = struct.unpack_from("!H", frame, offset + 6)[0]
    # Any fragmentation is outside the trustworthy TEL-001 normalization path.
    # Reject both non-zero offsets and the first fragment carrying MF=1.
    if flags_fragment & 0x3FFF:
        raise PacketParseError("fragmented-initial-ipv4-tcp-syn")
    source = str(ipaddress.ip_address(frame[offset + 12 : offset + 16]))
    destination = str(ipaddress.ip_address(frame[offset + 16 : offset + 20]))
    return _parse_tcp_syn(frame, offset + header_length, "ipv4", source, destination)


def _parse_ipv6_syn(frame: bytes, offset: int) -> ParsedSyn | None:
    if len(frame) < offset + 40:
        raise PacketParseError("truncated-ipv6-header")
    if frame[offset] >> 4 != 6:
        raise PacketParseError("invalid-ipv6-version")
    next_header = frame[offset + 6]
    source = str(ipaddress.ip_address(frame[offset + 8 : offset + 24]))
    destination = str(ipaddress.ip_address(frame[offset + 24 : offset + 40]))
    cursor = offset + 40

    for _ in range(8):
        if next_header == _IPPROTO_TCP:
            return _parse_tcp_syn(frame, cursor, "ipv6", source, destination)
        if next_header in {0, 43, 60}:  # hop-by-hop, routing, destination options
            if len(frame) < cursor + 2:
                raise PacketParseError("truncated-ipv6-extension-header")
            new_next = frame[cursor]
            header_length = (frame[cursor + 1] + 1) * 8
            if len(frame) < cursor + header_length:
                raise PacketParseError("truncated-ipv6-extension-body")
            next_header = new_next
            cursor += header_length
            continue
        if next_header == 44:
            raise PacketParseError("fragmented-initial-ipv6-tcp-syn")
        if next_header == 51:  # Authentication Header
            if len(frame) < cursor + 2:
                raise PacketParseError("truncated-ipv6-authentication-header")
            new_next = frame[cursor]
            header_length = (frame[cursor + 1] + 2) * 4
            if len(frame) < cursor + header_length:
                raise PacketParseError("truncated-ipv6-authentication-body")
            next_header = new_next
            cursor += header_length
            continue
        return None
    raise PacketParseError("too-many-ipv6-extension-headers")


def _parse_tcp_syn(
    frame: bytes,
    offset: int,
    family: str,
    source: str,
    destination: str,
) -> ParsedSyn | None:
    if len(frame) < offset + 20:
        raise PacketParseError("truncated-tcp-header")
    source_port, destination_port, sequence = struct.unpack_from("!HHI", frame, offset)
    data_offset = (frame[offset + 12] >> 4) * 4
    if data_offset < 20 or len(frame) < offset + data_offset:
        raise PacketParseError("invalid-tcp-header-length")
    flags = frame[offset + 13]
    if not (flags & _TCP_SYN) or (flags & _TCP_ACK):
        return None
    return ParsedSyn(
        family=family,
        source_address=source,
        source_port=source_port,
        destination_address=destination,
        destination_port=destination_port,
        sequence=sequence,
    )
