"""Runtime models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .manifest import EpisodeManifest
from .state import EpisodeState


@dataclass(slots=True)
class RuntimeEpisode:
    """Mutable execution holder with immutable identity manifest."""

    episode_id: str
    manifest: EpisodeManifest
    state: EpisodeState = EpisodeState.CREATED
    attributes: dict[str, Any] | None = None

    def transition(self, target: EpisodeState) -> None:
        from .state import assert_transition

        assert_transition(self.state, target)
        self.state = target
