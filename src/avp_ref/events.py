from __future__ import annotations

from .models import AVPEvent


class EventRecorder:
    """Append observable AVP events and forward them to optional telemetry."""

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
        return event
