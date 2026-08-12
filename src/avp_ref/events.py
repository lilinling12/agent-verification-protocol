from __future__ import annotations

from .models import AVPEvent, Evidence


class EventRecorder:
    def __init__(self, episode):
        self.episode = episode

    def emit(self, event_type: str, plane: str, logical_time: int, payload=None, state=None, evidence=None):
        seq = len(self.episode.events) + 1
        event = AVPEvent(
            event_id=f"evt_{self.episode.episode_id}_{seq:04d}",
            event_type=event_type,
            episode_id=self.episode.episode_id,
            sequence=seq,
            plane=plane,
            logical_time=logical_time,
            payload=payload or {},
            state=state or {},
            evidence=evidence or [],
        )
        self.episode.events.append(event)
        telemetry = self.episode.telemetry
        if telemetry is not None:
            telemetry.record_event(event)
            artifact = telemetry.artifact
            if artifact is not None:
                evidence_id = f"ev_{self.episode.episode_id}_telemetry"
                if evidence_id not in self.episode.evidence:
                    self.episode.evidence[evidence_id] = Evidence(
                        evidence_id,
                        "telemetry_artifact",
                        artifact.to_dict(),
                        artifact.artifact_digest,
                        classification="evaluator-confidential",
                    )
        return event
