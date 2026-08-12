from __future__ import annotations

from dataclasses import dataclass

from avp_ref.runtime.episode import Episode


@dataclass(frozen=True, slots=True)
class FailureLocalization:
    taxonomy: str
    first_bad_event_id: str | None
    first_bad_sequence: int | None
    rationale: str


def _target_order_id(episode: Episode) -> str:
    return str(episode.scenario.document.get("extensions", {}).get("avp_ref", {}).get("target_order_id", ""))


def locate_first_bad_step(episode: Episode) -> FailureLocalization | None:
    """Locate the earliest high-confidence deviation for the reference domain."""

    failed = {result.claim_id for result in episode.verification if result.verdict == "FAIL"}
    if not failed:
        return None
    target_order_id = _target_order_id(episode)
    for event in episode.events:
        if event.event_type != "environment.state.changed":
            continue
        for change in event.payload.get("changes", []):
            after = change.get("after") or {}
            if change.get("entity", "").startswith("refunds:") and after.get("order_id") != target_order_id:
                return FailureLocalization("tool.wrong_target", event.event_id, event.sequence, "first authoritative mutation created a refund for a non-target order")
    if "refund.completed" in failed:
        for event in episode.events:
            if event.event_type == "agent.stop" and "success" in str(event.payload.get("report", "")).lower():
                return FailureLocalization("state.false_success", event.event_id, event.sequence, "Agent reported success without authoritative success state")
    return FailureLocalization("goal.unsatisfied", None, None, "verification failed but no higher-confidence first bad step was localized")
