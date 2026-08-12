"""Replay identity capability for the Python reference runtime."""

from __future__ import annotations

from avp_ref.environment import EnvironmentAdapter
from avp_ref.events import EventRecorder
from avp_ref.mcp import MCPVerificationGateway
from avp_ref.oracle_runner import OraclePackage
from avp_ref.subject import SubjectAdapter

from .engine import ReferenceRuntime
from .episode import Episode
from .identity import ReplaySourceIdentity


def create_replay_episode(
    runtime: ReferenceRuntime,
    source_episode_id: str,
    *,
    environment_adapter: EnvironmentAdapter,
    subject_adapter: SubjectAdapter,
    oracle_package: OraclePackage,
    mcp_gateway: MCPVerificationGateway | None = None,
) -> Episode:
    """Create a new Episode linked explicitly to a prior Episode.

    This operation intentionally establishes identity only. AVP Core v0.1 does
    not let the reference runtime infer or advertise snapshot, environment,
    artifact, or behavioral equivalence merely because identities are linked.
    Callers must supply the adapters/evaluator inputs selected for the replay;
    future replay profiles may standardize stronger equivalence declarations.
    """

    try:
        source = runtime.episodes[source_episode_id]
    except KeyError as exc:
        raise KeyError(f"unknown source episode: {source_episode_id}") from exc

    replay = runtime.create_episode(
        scenario=source.scenario,
        agent_system=source.agent_system,
        environment_adapter=environment_adapter,
        subject_adapter=subject_adapter,
        oracle_package=oracle_package,
        mcp_gateway=mcp_gateway,
    )
    source_identity = ReplaySourceIdentity(
        episode_id=source.episode_id,
        manifest_digest=source.manifest.manifest_digest,
    )
    replay.bind_replay_source(source_identity)
    EventRecorder(replay).emit(
        "episode.replay.linked",
        "orchestrator",
        0,
        payload={"source": source_identity.to_dict()},
    )
    return replay
