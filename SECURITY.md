# Security Policy

AVP verifies systems that may execute tools and mutate state, so vulnerabilities in evaluator boundaries, authorization, sandboxing, artifact integrity, schema validation, or secret handling are treated as security-sensitive.

## Supported versions

During the pre-1.0 phase, security fixes target the latest development line and the most recent published release when a practical patch can be produced. Older pre-1.0 releases may require users to upgrade rather than receive a backport.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private data, or a working bypass.

Use GitHub's **Security → Report a vulnerability** flow for this repository when private vulnerability reporting is available. If that option is unavailable, contact the current maintainer through a private contact method listed on their GitHub profile and disclose only enough public information to establish a private channel.

Include, when possible:

- affected version/commit;
- affected trust boundary or component;
- prerequisites and attack path;
- minimal reproduction;
- expected versus actual security property;
- impact assessment;
- suggested mitigation, if known.

## Disclosure

The project aims to validate the report, coordinate a fix, add regression coverage, and publish an advisory when appropriate before detailed public disclosure. Exact timing depends on severity, exploitability, and downstream coordination; this policy does not promise a fixed response SLA during the experimental phase.

## Scope examples

Security reports are especially relevant for evaluator privilege leakage, Subject-to-Evaluator boundary bypass, Oracle isolation escape, authorization/capability bypass, artifact or digest substitution, secret exposure, unsafe deserialization, code execution through untrusted protocol input, and verification results that can be forged across trust boundaries.
