# 15 AVP Package & Registry Specification

> Status: Draft v0.1  
> Goal: make verification assets portable across implementations.

## 1. Package Types

AVP ecosystem distributes:

```text
Scenario Package
Environment Package
Oracle Package
Mutation Pack
Policy Pack
Benchmark Adapter
Conformance Extension
```

---

## 2. Package Manifest

```yaml
apiVersion: avp.spec/v0.1
kind: Package

metadata:
  name: org.example.commerce-refunds
  version: 1.3.0
  license: Apache-2.0

package:
  type: scenario
  digest: sha256:...
  supportedAvp: ">=0.1 <0.2"

contents:
  - path: scenarios/refund.yaml
    digest: sha256:...
```

---

## 3. Identity

Registry identity is:

```text
publisher namespace
+ package name
+ semantic version
+ immutable digest
```

Version tags may move only under explicitly documented prerelease policies; digests never move.

---

## 4. Distribution

OCI artifact registries are RECOMMENDED for packages containing runtime/container artifacts.

Plain HTTPS/package registries MAY be used for metadata-only packages.

AVP does not invent a new blob transport.

---

## 5. Dependencies

```yaml
dependencies:
  - name: avp://oracle/refund-state
    version: "^2.0"
    digest: optional-at-template-time

  - name: oci://example/environment-commerce
    version: "4.2.0"
```

ScenarioInstance compilation resolves dependencies to immutable digests.

---

## 6. Lock File

A compiled benchmark SHOULD emit an `avp.lock` containing every resolved dependency.

This is essential for reproducibility.

---

## 7. Signing and Provenance

Future-ready metadata:

```text
signature
publisher identity
SBOM
build provenance
source commit
```

Reuse Sigstore/SLSA/OCI mechanisms where practical.

---

## 8. Trust Policy

Registry supports policy such as:

```text
allow publisher X
require signed oracle
deny mutable runtime tag
require security review
```

The subject Agent must never be able to choose a privileged Oracle package for its own evaluation.

---

## 9. Registry APIs

Core operations:

```text
resolve
fetch manifest
fetch artifact
publish
deprecate
list versions
verify signature
```

Search/discovery is informative, not normative.

---

## 10. Public vs Private Registry

Organizations can use:

```text
public community registry
private enterprise registry
air-gapped mirror
```

Package identity remains portable.

---

## 11. Benchmark Packs

A Benchmark package can reference:

```text
Scenario templates
holdout policy
Environment package
Oracle package
coverage taxonomy
calibration metadata
license
```

Private living benchmark instances need not be published.

---

## 12. Oracle Security

Oracle code packages are privileged execution content.

Registry metadata SHOULD include:

```text
network requirement
filesystem requirement
language/runtime
resource requirement
declared evidence inputs
```

Runtime enforces these restrictions.

---

## 13. Deprecation

Packages can be:

```text
active
deprecated
withdrawn
security-revoked
```

Historical Episodes still retain the original digest.

---

## 14. Registry Network Effect

The long-term open ecosystem becomes:

```text
write Scenario once
publish Oracle once
reuse Environment
run on many AVP implementations
```

This is a stronger standardization target than a proprietary benchmark marketplace.
