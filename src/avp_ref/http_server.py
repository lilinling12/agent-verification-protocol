from __future__ import annotations
from dataclasses import asdict
from .runtime import ReferenceRuntime

runtime = ReferenceRuntime()

def create_app():
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("Install avp-reference[http] to use the HTTP binding") from exc

    app = FastAPI(title="AVP Reference Runtime", version="0.1.0")

    @app.get("/.well-known/avp")
    def capabilities():
        return runtime.capabilities()

    @app.post("/v1/episodes")
    def create_episode(body: dict):
        task = body.get("task") or body.get("scenario_instance", {}).get("uri", "reference-task")
        ep = runtime.create_episode(task)
        return {"episode_id": ep.episode_id, "state": ep.state.value}

    @app.get("/v1/episodes/{episode_id}")
    def get_episode(episode_id: str):
        ep = runtime.episodes.get(episode_id)
        if not ep:
            raise HTTPException(404)
        return {
            "episode_id": ep.episode_id,
            "state": ep.state.value,
            "task_verdict": ep.task_verdict.value,
            "validity": ep.validity.value,
        }

    @app.post("/v1/episodes/{episode_id}/snapshots")
    def snapshot(episode_id: str):
        s = runtime.snapshot(episode_id)
        return {
            "snapshot_id": s.snapshot_id,
            "mode": "logical",
            "environment_digest": s.state_digest,
        }

    @app.post("/v1/episodes/{episode_id}:restore")
    def restore(episode_id: str, body: dict):
        level = runtime.restore(episode_id, body["snapshot_id"])
        return {"restored": True, "equivalence": {"level": level, "differences": []}}

    @app.post("/v1/episodes/{episode_id}:verify")
    def verify(episode_id: str, body: dict | None = None):
        target = (body or {}).get("target_order_id", "ord_1")
        ep = runtime.verify(episode_id, target)
        return {
            "task": ep.task_verdict.value,
            "validity": ep.validity.value,
            "claims": [asdict(r) for r in ep.verification],
        }

    return app
