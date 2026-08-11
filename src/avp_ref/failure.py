from __future__ import annotations
from dataclasses import dataclass
from .models import Episode


@dataclass(frozen=True)
class FailureLocalization:
    taxonomy: str
    first_bad_event_id: str | None
    first_bad_sequence: int | None
    rationale: str


def locate_first_bad_step(ep: Episode, target_order_id: str = "ord_1") -> FailureLocalization | None:
    failed = {r.claim_id for r in ep.verification if r.verdict == "FAIL"}
    if not failed:
        return None

    for event in ep.events:
        if event.event_type != "environment.state.changed":
            continue
        changes = event.payload.get("changes", [])
        for change in changes:
            after = change.get("after") or {}
            if change.get("entity", "").startswith("refunds:") and after.get("order_id") != target_order_id:
                return FailureLocalization(
                    taxonomy="tool.wrong_target",
                    first_bad_event_id=event.event_id,
                    first_bad_sequence=event.sequence,
                    rationale="first authoritative mutation created a refund for a non-target order",
                )

    if "refund.completed" in failed:
        for event in ep.events:
            if event.event_type == "agent.stop" and "success" in str(event.payload.get("report", "")).lower():
                return FailureLocalization(
                    taxonomy="state.false_success",
                    first_bad_event_id=event.event_id,
                    first_bad_sequence=event.sequence,
                    rationale="Agent reported success without authoritative success state",
                )

    return FailureLocalization(
        taxonomy="goal.unsatisfied",
        first_bad_event_id=None,
        first_bad_sequence=None,
        rationale="verification failed but no higher-confidence first bad step was localized",
    )
