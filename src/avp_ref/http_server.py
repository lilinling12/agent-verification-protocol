from __future__ import annotations

from dataclasses import asdict

from avp_ref import __version__
from avp_ref.reference import correct_subject, false_success_subject, recovering_subject, reference_environment, reference_oracle_package, wrong_target_subject
from avp_ref.runtime import AgentSystem, InvalidEpisodeTransition, ReferenceRuntime
from avp_ref.scenario import CompileOptions, ScenarioCompiler
from avp_ref.subject import HTTPSubjectAdapter, InProcessSubjectAdapter

runtime = ReferenceRuntime()
_REFERENCE_SUBJECTS = {"correct": correct_subject, "false-success": false_success_subject, "wrong-target": wrong_target_subject, "recovering": recovering_subject}


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("Install avp-reference[http] to use the HTTP binding") from exc

    app = FastAPI(title="AVP Reference Runtime", version=__version__)

    @app.get("/.well-known/avp")
    def capabilities(): return runtime.capabilities()

    @app.post("/v1/episodes")
    def create_episode(body: dict):
        try:
            scenario = ScenarioCompiler().compile(body["scenario_template"], CompileOptions(root_seed=int(body.get("seed", 0))))
            agent = AgentSystem(**body["agent_system"])
            subject = body["subject"]
            kind = subject.get("type")
            if kind == "http":
                subject_adapter = HTTPSubjectAdapter(subject["base_url"], headers=subject.get("headers"))
            elif kind == "reference":
                fixture = _REFERENCE_SUBJECTS.get(subject.get("name"))
                if fixture is None: raise ValueError("unknown reference subject")
                subject_adapter = InProcessSubjectAdapter(fixture)
            else:
                raise ValueError("subject.type must be 'http' or 'reference'")
            episode = runtime.create_episode(scenario, agent, reference_environment(), subject_adapter, reference_oracle_package())
            return {"episode_id": episode.episode_id, "state": episode.state.value, "manifest_digest": episode.manifest.manifest_digest}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(422, detail=str(exc)) from exc

    @app.post("/v1/episodes/{episode_id}:provision")
    def provision(episode_id: str):
        try:
            episode = runtime.provision(episode_id); return {"episode_id": episode.episode_id, "state": episode.state.value}
        except KeyError as exc: raise HTTPException(404, detail=str(exc)) from exc
        except InvalidEpisodeTransition as exc: raise HTTPException(409, detail=str(exc)) from exc

    @app.post("/v1/episodes/{episode_id}:run")
    def run(episode_id: str):
        try:
            report = runtime.run_subject(episode_id); return {"report": report, "state": runtime.episodes[episode_id].state.value, "validity": runtime.episodes[episode_id].validity.value}
        except KeyError as exc: raise HTTPException(404, detail=str(exc)) from exc
        except InvalidEpisodeTransition as exc: raise HTTPException(409, detail=str(exc)) from exc

    @app.get("/v1/episodes/{episode_id}")
    def get_episode(episode_id: str):
        episode = runtime.episodes.get(episode_id)
        if episode is None: raise HTTPException(404)
        return {"episode_id": episode.episode_id, "state": episode.state.value, "manifest_digest": episode.manifest.manifest_digest, "task_verdict": episode.task_verdict.value, "validity": episode.validity.value}

    @app.post("/v1/episodes/{episode_id}:verify")
    def verify(episode_id: str):
        try:
            episode = runtime.verify(episode_id); return {"task": episode.task_verdict.value, "validity": episode.validity.value, "state": episode.state.value, "claims": [asdict(result) for result in episode.verification]}
        except KeyError as exc: raise HTTPException(404, detail=str(exc)) from exc
        except InvalidEpisodeTransition as exc: raise HTTPException(409, detail=str(exc)) from exc

    return app
