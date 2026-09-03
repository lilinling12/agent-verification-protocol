"""Same-run duplicate-SYN normalization qualification for TEL-RB-003.

The base capture qualification proves topology, directionality, admission ordering,
exact counts for independent connects, alternate-target visibility, and zero-drop
capture integrity. This extension adds a fourth exact-run canary that deliberately
emits two byte-identical initial SYN packets from the qualified source namespace.

The packets have the same TCP tuple and initial sequence, so the main-adopted
normalizer must retain both raw observations while producing one initiation and at
least one retransmission observation. The injector is qualification-only: a
one-shot helper sharing the source namespace with every capability dropped except
``NET_RAW`` and with no Docker socket.
"""

from __future__ import annotations

from .capture_qualification import (
    CaptureQualification,
    CaptureQualificationResult,
    _require_counts,
)
from .evidence_core import MaterializedEndpoint
from .toxiproxy_binding import ToxiproxyPrerequisiteError

_ENHANCED_QUALIFICATION_FORMAT = "avp-project-network-capture-qualification-v0.3"
_DUPLICATE_SOURCE_PORT = 43123
_DUPLICATE_SEQUENCE = 0x4A565031


class RetransmissionQualifiedCaptureQualification(CaptureQualification):
    """Add same-run duplicate-SYN normalization evidence to capture qualification."""

    _duplicate_syn_probe = False

    def _execute_materialized(
        self,
        docker_info: dict[str, object],
    ) -> CaptureQualificationResult:
        base = super()._execute_materialized(docker_info)

        self._duplicate_syn_probe = True
        try:
            duplicate = self._observe(
                label="duplicate-syn-normalization",
                expected=MaterializedEndpoint(
                    "ipv4",
                    self.topology.expected_target,
                    43001,
                    "qualification-target",
                ),
                connect_targets=((self.topology.expected_target, 43001),),
            )
        finally:
            self._duplicate_syn_probe = False

        raw_bytes = duplicate.pop("rawBytes")
        _require_duplicate_syn_normalization(duplicate)

        document = dict(base.document)
        canaries = list(document.get("canaries", []))
        canaries.append(duplicate)
        basis = list(document.get("qualificationBasis", []))
        basis.append(
            "two byte-identical initial SYN packets from one qualification-only "
            "NET_RAW injector normalize to one initiation while retaining duplicate "
            "raw SYN evidence"
        )
        document["format"] = _ENHANCED_QUALIFICATION_FORMAT
        document["canaries"] = canaries
        document["qualificationBasis"] = basis
        document["normalizationProbe"] = {
            "label": "duplicate-syn-normalization",
            "sourceAddress": self.topology.source,
            "sourcePort": _DUPLICATE_SOURCE_PORT,
            "destinationAddress": self.topology.expected_target,
            "destinationPort": 43001,
            "initialSequence": _DUPLICATE_SEQUENCE,
            "injectedCopies": 2,
            "namespace": f"container:{self.source_name}",
            "capabilityPolicy": {
                "dropAll": True,
                "add": ["NET_RAW"],
                "readOnly": True,
                "noNewPrivileges": True,
                "dockerSocketMounted": False,
            },
        }
        return CaptureQualificationResult(
            document=document,
            raw_artifacts=base.raw_artifacts
            + (("duplicate-syn-normalization.raw.json", raw_bytes),),
        )

    def _connect_sequence(self, targets: tuple[tuple[str, int], ...]) -> None:
        if not self._duplicate_syn_probe:
            super()._connect_sequence(targets)
            return

        expected = ((self.topology.expected_target, 43001),)
        if targets != expected:
            raise ToxiproxyPrerequisiteError(
                f"duplicate-SYN qualification target drift: {targets!r}"
            )
        self.docker.run(*self._duplicate_syn_injector_args())

    def _duplicate_syn_injector_args(self) -> tuple[str, ...]:
        return (
            "run",
            "--rm",
            "--network",
            f"container:{self.source_name}",
            "--read-only",
            "--cap-drop=ALL",
            "--cap-add=NET_RAW",
            "--security-opt=no-new-privileges",
            self.helper.image_ref,
            "python",
            "-c",
            self._duplicate_syn_script(),
        )

    def _duplicate_syn_script(self) -> str:
        source = self.topology.source
        destination = self.topology.expected_target
        return (
            "import socket,struct,time\n"
            f"src={source!r}; dst={destination!r}; "
            f"sport={_DUPLICATE_SOURCE_PORT}; dport=43001; seq={_DUPLICATE_SEQUENCE}\n"
            "def checksum(data):\n"
            " if len(data) % 2: data += b'\\x00'\n"
            " words=struct.unpack(f'!{len(data)//2}H', data)\n"
            " total=sum(words)\n"
            " while total >> 16: total=(total & 0xffff) + (total >> 16)\n"
            " return (~total) & 0xffff\n"
            "src_b=socket.inet_aton(src); dst_b=socket.inet_aton(dst)\n"
            "ver_ihl=(4 << 4) | 5\n"
            "ip=struct.pack('!BBHHHBBH4s4s',ver_ihl,0,40,0x4A11,0,64,"
            "socket.IPPROTO_TCP,0,src_b,dst_b)\n"
            "ip_csum=checksum(ip)\n"
            "ip=struct.pack('!BBHHHBBH4s4s',ver_ihl,0,40,0x4A11,0,64,"
            "socket.IPPROTO_TCP,ip_csum,src_b,dst_b)\n"
            "offset_flags=(5 << 12) | 0x002\n"
            "tcp=struct.pack('!HHLLHHHH',sport,dport,seq,0,offset_flags,65535,0,0)\n"
            "pseudo=struct.pack('!4s4sBBH',src_b,dst_b,0,socket.IPPROTO_TCP,len(tcp))\n"
            "tcp_csum=checksum(pseudo + tcp)\n"
            "tcp=struct.pack('!HHLLHHHH',sport,dport,seq,0,offset_flags,65535,tcp_csum,0)\n"
            "packet=ip + tcp\n"
            "sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_RAW)\n"
            "sock.setsockopt(socket.IPPROTO_IP,socket.IP_HDRINCL,1)\n"
            "sock.sendto(packet,(dst,0)); time.sleep(0.01); sock.sendto(packet,(dst,0))\n"
            "sock.close()\n"
        )


def _require_duplicate_syn_normalization(document: dict[str, object]) -> None:
    """Require duplicate raw SYNs to collapse into one initiation."""

    _require_counts(document, total=1, expected=1, alternate=0)
    raw = int(document["rawSynPackets"])
    retransmitted = int(document["retransmittedSynPackets"])
    if raw < 2:
        raise ToxiproxyPrerequisiteError(
            f"duplicate-SYN qualification observed fewer than two raw SYNs: {raw}"
        )
    if retransmitted != raw - 1:
        raise ToxiproxyPrerequisiteError(
            "duplicate-SYN qualification retransmission accounting mismatch: "
            f"raw={raw}, retransmitted={retransmitted}"
        )
