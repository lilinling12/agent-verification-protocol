# Security Policy

AVP treats the subject Agent, external content, and potentially tool/MCP outputs as untrusted.

Security-sensitive issues include:

- access from Agent Plane to evaluator-only state or credentials;
- sandbox/runtime escape;
- cross-tenant artifact or snapshot access;
- Oracle or benchmark answer leakage;
- prompt injection into semantic/agentic Judges;
- trace or evidence tampering;
- unsafe conformance-test network scanning;
- registry package integrity failures.

Do not publish exploit details for an unpatched evaluator isolation or sandbox escape issue in a public issue. Use the repository's private security reporting mechanism once the GitHub repository is live.

The reference runtime demonstrates API-plane separation only. It is not a hardened multi-tenant sandbox.
