from __future__ import annotations

from dataclasses import asdict

from avp_ref.oracle import RefundOracle
from avp_ref.reference import correct_subject, false_success_subject, recovering_subject, reference_environment, wrong_target_subject
from avp_ref.runtime import AgentSystem, InvalidEpisodeTransition, ReferenceRuntime
from avp_ref.scenario import CompileOptions, ScenarioCompiler

runtime = ReferenceRuntime()
_REFERENCE_SUBJECTS = {"correct": correct_subject, "false-success": false_success_subject, "wrong-target": wrong_target_subject, "recovering": recovering_subject}


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("Install avp-reference[http] to use the HTTP binding") from exc

    app = FastAPI(title="AVP Reference Runtime", version="0.2.0-alpha.1")

    @app.get("/.well-known/avp")
    def capabilities():
        return runtime.capabilities()

    @app.post("/v1/episodes")
    def create_episode(body: dict):
        try:
            scenario = ScenarioCompiler().compile(body["scenario_template"], CompileOptions(root_seed=int(body.get("seed", 0))))
            agent = AgentSystem(**body["agent_system"])
            episode = runtime.create_episode(scenario, agent, reference_environment())
            return {"episode_id": episode.episode_id, "state": episode.state.value, "manifest_digest": episode.manifest.manifest_digest}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(422, detail=str(exc)) from exc

    @app.post("/v1/episodes/{episode_id}:provision")
    def provision(episode_id: str):
        try:
            episode = runtime.provision(episode_id)
            return {"episode_id": episode.episode_id, "state": episode.state.value}
        except KeyError as exc:
            raise HTTPException(404, detail=str(exc)) from exc
        except InvalidEpisodeTransition as exc:
            raise HTTPException(409, detail=str(exc)) from exc

    @app.post("/v1/episodes/{episode_id}:run-reference")
    def run_reference(episode_id: str, body: dict):
        subject = _REFERENCE_SUBJECTS.get(body.get("subject"))
        if subject is None:
            raise HTTPException(422, detail="unknown reference subject")
        try:
            report = runtime.run_subject(episode_id, subject)
            return {"report": report, "state": runtime.episodes[episode_id].state.value}
        except KeyError as exc:
            raise HTTPException(404, detail=str(exc)) from exc
        except InvalidEpisodeTransition as exc:
            raise HTTPException(409, detail=str(exc)) from exc

    @app.get("/v1/episodes/{episode_id}")
    def get_episode(episode_id: str):
        episode = runtime.episodes.get(episode_id)
        if episode is None:
            raise HTTPException(404)
        return {"episode_id": episode.episode_id, "state": episode.state.value, "manifest_digest": episode.manifest.manifest_digest, "task_verdict": episode.task_verdict.value, "validity": episode.validity.value}

    @app.post("/v1/episodes/{episode_id}/snapshots")
    def snapshot(episode_id: str):
        try:
            item = runtime.snapshot(episode_id)
            return {"snapshot_id": item.snapshot_id, "mode": "logical", "environment_digest": item.state_digest}
        except InvalidEpisodeTransition as exc:
            raise HTTPException(409, detail=str(exc)) from exc

    @app.post("/v1/episodes/{episode_id}:restore")
    def restore(episode_id: str, body: dict):
        try:
            level = runtime.restore(episode_id, body["snapshot_id"])
            return {"restored": True, "equivalence": {"level": level, "differences": []}}
        except InvalidEpisodeTransition as exc:
            raise HTTPException(409, detail=str(exc)) from exc

    @app.post("/v1/episodes/{episode_id}:verify")
    def verify(episode_id: str):
        try:
            episode = runtime.verify(episode_id, RefundOracle())
            return {"task": episode.task_verdict.value, "validity": episode.validity.value, "state": episode.state.value, "claims": [asdict(result) for result in episode.verification]}
        except InvalidEpisodeTransition as exc:
            raise HTTPException(409, detail=str(exc)) from exc

    return app
