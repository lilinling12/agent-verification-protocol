from __future__ import annotations
import argparse
import json
from .conformance import run_suite
from .runtime import ReferenceRuntime, false_success_subject, correct_subject
from .benchmark import run_reference_benchmark

def cmd_demo():
    rt = ReferenceRuntime()

    print("== False-success subject ==")
    ep = rt.create_episode("Refund ord_1")
    rt.run_subject(ep.episode_id, false_success_subject)
    rt.verify(ep.episode_id, "ord_1")
    print(json.dumps({
        "agent_report": ep.agent_report,
        "task_verdict": ep.task_verdict.value,
        "validity": ep.validity.value,
        "claims": [{"id": r.claim_id, "verdict": r.verdict} for r in ep.verification],
    }, indent=2))

    print("\n== Correct deterministic subject ==")
    ep2 = rt.create_episode("Refund ord_1")
    rt.run_subject(ep2.episode_id, correct_subject)
    rt.verify(ep2.episode_id, "ord_1")
    print(json.dumps({
        "agent_report": ep2.agent_report,
        "task_verdict": ep2.task_verdict.value,
        "validity": ep2.validity.value,
    }, indent=2))

def cmd_conformance():
    results = run_suite()
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'} {r.case_id} — {r.detail}")
    if not all(r.passed for r in results):
        raise SystemExit(1)

def cmd_serve(port: int):
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[http]'") from exc
    uvicorn.run("avp_ref.http_server:create_app", factory=True, host="127.0.0.1", port=port)

def main():
    parser = argparse.ArgumentParser(prog="avp")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    sub.add_parser("conformance")
    bench = sub.add_parser("benchmark")
    bench.add_argument("--runs", type=int, default=4)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()

    if args.command == "demo":
        cmd_demo()
    elif args.command == "conformance":
        cmd_conformance()
    elif args.command == "benchmark":
        print(json.dumps(run_reference_benchmark(args.runs), indent=2))
    elif args.command == "serve":
        cmd_serve(args.port)

if __name__ == "__main__":
    main()
