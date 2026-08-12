from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from avp_ref.benchmark import run_reference_benchmark
from avp_ref.conformance import run_suite
from avp_ref.reference import (
    correct_subject,
    false_success_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import ReferenceRuntime
from avp_ref.scenario import (
    CompileOptions,
    ScenarioCompileError,
    ScenarioCompiler,
    StaticReferenceResolver,
    load_scenario,
    validate_template,
)
from avp_ref.tck_adapter import TCKAdapterError, TCKRepository, TCKRunner


def _run_demo_subject(subject):
    runtime = ReferenceRuntime()
    episode = runtime.create_episode(
        reference_scenario(),
        reference_agent_system(subject.__name__),
        reference_environment(),
        reference_subject_adapter(subject),
        reference_oracle_package(),
    )
    runtime.provision(episode.episode_id)
    runtime.run_subject(episode.episode_id)
    runtime.verify(episode.episode_id)
    return episode


def cmd_demo() -> None:
    subjects = (
        ("False-success subject", false_success_subject),
        ("Correct deterministic subject", correct_subject),
    )
    for title, subject in subjects:
        episode = _run_demo_subject(subject)
        print(f"== {title} ==")
        print(
            json.dumps(
                {
                    "episode_id": episode.episode_id,
                    "manifest_digest": episode.manifest.manifest_digest,
                    "agent_report": episode.agent_report,
                    "task_verdict": episode.task_verdict.value,
                    "validity": episode.validity.value,
                    "claims": [
                        {"id": result.claim_id, "verdict": result.verdict}
                        for result in episode.verification
                    ],
                },
                indent=2,
            )
        )


def cmd_conformance() -> None:
    """Run the legacy Python reference-implementation smoke suite."""

    results = run_suite()
    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL'} {result.case_id} — {result.detail}")
    if not all(result.passed for result in results):
        raise SystemExit(1)


def cmd_validate(path: str) -> None:
    template = load_scenario(path)
    validate_template(template)
    print(
        json.dumps(
            {
                "valid": True,
                "kind": template.get("kind"),
                "name": template.get("metadata", {}).get("name"),
                "version": template.get("metadata", {}).get("version"),
            },
            indent=2,
            sort_keys=True,
        )
    )


def _parse_override(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("parameter override must use NAME=VALUE")
    name, text = raw.split("=", 1)
    if not name:
        raise argparse.ArgumentTypeError("parameter override name cannot be empty")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = text
    return name, value


def _load_reference_lock(path: str | None) -> StaticReferenceResolver | None:
    if not path:
        return None
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid reference lock file '{source}': {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("reference lock root must be an object keyed by URI")
    return StaticReferenceResolver(records=data)


def _write_text_atomic(target: Path, payload: str) -> None:
    """Replace a text artifact atomically on the target filesystem."""

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def cmd_compile(
    path: str,
    *,
    seed: int,
    overrides: list[tuple[str, Any]],
    output: str | None,
    strict_references: bool,
    lock_file: str | None,
) -> None:
    template = load_scenario(path)
    resolver = _load_reference_lock(lock_file)
    compiler = ScenarioCompiler(resolver=resolver) if resolver else ScenarioCompiler()
    instance = compiler.compile(
        template,
        CompileOptions(
            root_seed=seed,
            parameter_overrides=dict(overrides),
            strict_references=strict_references,
        ),
    )
    payload = json.dumps(instance.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        _write_text_atomic(target, payload)
        print(json.dumps({"instance_digest": instance.instance_digest, "output": str(target)}, sort_keys=True))
    else:
        print(payload, end="")


def cmd_tck_run(
    *,
    profile: str,
    capabilities: list[str],
    cases: list[str],
    output: str | None,
    repository_root: str | None,
) -> None:
    repository = (
        TCKRepository(Path(repository_root))
        if repository_root is not None
        else TCKRepository.discover()
    )
    runner = TCKRunner.for_reference(repository, capabilities=capabilities)
    run = runner.run(profile=profile, selected_case_ids=cases or None)
    payload = json.dumps(run.report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        _write_text_atomic(target, payload)
        print(json.dumps({"output": str(target), "summary": run.report["summary"]}, sort_keys=True))
    else:
        print(payload, end="")
    if not run.conformant:
        raise SystemExit(1)


def cmd_serve(port: int) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[http]'") from exc
    uvicorn.run("avp_ref.http_server:create_app", factory=True, host="127.0.0.1", port=port)


def _print_compile_error(exc: ScenarioCompileError) -> None:
    print(
        json.dumps(
            {
                "error": type(exc).__name__,
                "message": str(exc),
                "diagnostics": [
                    {
                        "code": item.code,
                        "message": item.message,
                        "path": item.path,
                        "severity": item.severity.value,
                    }
                    for item in exc.diagnostics
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="avp")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    sub.add_parser("conformance", help="run reference implementation smoke tests")

    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--runs", type=int, default=4)

    validate = sub.add_parser("validate", help="validate an AVS ScenarioTemplate")
    validate.add_argument("scenario")

    compile_parser = sub.add_parser("compile", help="compile AVS to an immutable ScenarioInstance")
    compile_parser.add_argument("scenario")
    compile_parser.add_argument("--seed", type=int, default=0)
    compile_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        type=_parse_override,
        default=[],
        metavar="NAME=VALUE",
    )
    compile_parser.add_argument("--out", dest="output")
    compile_parser.add_argument("--strict-refs", action="store_true")
    compile_parser.add_argument("--lock", dest="lock_file")

    tck = sub.add_parser("tck", help="execute language-independent AVP TCK resources")
    tck_sub = tck.add_subparsers(dest="tck_command", required=True)
    tck_run = tck_sub.add_parser("run", help="run a TCK profile against the reference implementation")
    tck_run.add_argument("--profile", default="avp-core-v0.1")
    tck_run.add_argument("--capability", action="append", default=[], dest="capabilities")
    tck_run.add_argument("--case", action="append", default=[], dest="cases")
    tck_run.add_argument("--out", dest="output")
    tck_run.add_argument("--repository-root")

    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8790)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    try:
        if args.command == "demo":
            cmd_demo()
        elif args.command == "conformance":
            cmd_conformance()
        elif args.command == "benchmark":
            print(json.dumps(run_reference_benchmark(args.runs), indent=2))
        elif args.command == "validate":
            cmd_validate(args.scenario)
        elif args.command == "compile":
            cmd_compile(
                args.scenario,
                seed=args.seed,
                overrides=args.overrides,
                output=args.output,
                strict_references=args.strict_refs,
                lock_file=args.lock_file,
            )
        elif args.command == "tck" and args.tck_command == "run":
            cmd_tck_run(
                profile=args.profile,
                capabilities=args.capabilities,
                cases=args.cases,
                output=args.output,
                repository_root=args.repository_root,
            )
        elif args.command == "serve":
            cmd_serve(args.port)
    except ScenarioCompileError as exc:
        _print_compile_error(exc)
        raise SystemExit(2) from exc
    except TCKAdapterError as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, sort_keys=True))
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
