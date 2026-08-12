# AVP Core Terminology

Status: Draft normative candidate for AVP v0.1.

This document defines the minimum shared vocabulary needed by AVP Core. Capitalized terms below have protocol meaning when used by normative requirements.

## Agent System

An **Agent System** is the system under verification. It may contain one or more models, prompts, planners, memories, retrieval components, tools, policies, and application code. AVP does not require a particular internal architecture.

## Subject

A **Subject** is the execution-facing representation of an Agent System inside an Episode. The Subject receives only information and capabilities permitted by the Scenario and verification boundary. The Subject MUST NOT be assumed to have access to evaluator-private state.

## Scenario

A **Scenario** is a reusable verification program or template that describes task intent, environment requirements, capabilities, evaluator-owned checks, and reproducibility inputs.

## Scenario Instance

A **Scenario Instance** is an immutable resolved instance of a Scenario after parameter resolution, deterministic generation, reference resolution, and visibility enforcement. A Scenario Instance is the execution input bound to an Episode.

## Episode

An **Episode** is one bounded verification execution of a Scenario Instance against one identified Agent System configuration and one identified verification configuration.

## Environment

An **Environment** is the authoritative external state and capability surface against which the Subject acts. AVP does not require a specific implementation technology.

## Evaluator

An **Evaluator** is the privileged verification side that may observe evaluator-authorized state, execute Oracles, classify validity, and produce Verification Results. The Evaluator is outside the Subject trust boundary.

## Evidence

**Evidence** is an identified verification artifact used to support or refute a Claim or to establish evaluation validity. Evidence may include state projections, diffs, events, telemetry artifacts, Oracle execution artifacts, or other protocol-defined forms.

## Claim

A **Claim** is a proposition that an Evaluator attempts to verify from Evidence and an Oracle or another protocol-defined verification method.

## Oracle

An **Oracle** is an evaluator-owned verification component that evaluates Claims using authorized verification inputs. AVP does not require a particular implementation language or isolation mechanism unless a profile says otherwise.

## Task Verdict

A **Task Verdict** states the result of the Agent System's task execution. Task Verdict is distinct from evaluation validity and infrastructure health.

## Validity

**Validity** states whether an evaluation can be interpreted as valid evidence about the Agent System. A task result MUST NOT be converted into an Agent failure solely because the evaluation itself was invalid or infrastructure-confounded.

## Conformance

**Conformance** means satisfying the normative AVP requirements claimed by an implementation or profile. Reference implementation behavior is not sufficient evidence of conformance unless demonstrated by the corresponding conformance requirements and tests.
