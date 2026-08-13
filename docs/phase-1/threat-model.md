# Phase 1 — Threat Model

The auditor itself is a security-sensitive system because it processes attacker-controlled source code, build instructions, dependencies, configuration, prompts, logs, and generated artifacts.

## 1. Assets

Critical assets:

- Source repositories and private source code.
- Repository access tokens and OAuth credentials.
- Dependency/package credentials.
- LLM provider credentials.
- Internal findings and security reports.
- Tenant metadata.
- Audit artifacts and runtime logs.
- Signing keys and deployment credentials.
- Database contents.
- Sandbox/control-plane communication channels.

## 2. Trust zones

```text
ZONE A — User / External Internet
    |
ZONE B — Public API / Web
    |
ZONE C — Control Plane
    |
ZONE D — Analysis Orchestrator
    |
ZONE E — Untrusted Repository Workers
    |
ZONE F — Runtime Sandbox
```

Repository execution belongs in Zone E/F and must never be trusted by Zones B/C/D.

## 3. Threat actors

- Malicious repository author.
- Compromised dependency maintainer.
- Malicious contributor to an otherwise trusted repository.
- Malicious or compromised user/tenant.
- External attacker targeting the auditor service.
- Insider with excessive privileges.
- Compromised tool or model provider.

## 4. Major threats

### T1 — Arbitrary code execution breakout

A repository can execute code during package installation, build, test, or analysis and attempt to compromise the host or control plane.

Required controls:

- Strong sandboxing.
- No unrestricted host mounts.
- Resource limits.
- Network restrictions.
- Process limits.
- Ephemeral workers.
- Separate credentials.

### T2 — Prompt injection through repository content

README files, source comments, tests, generated files, or documentation can attempt to control an LLM agent.

Required controls:

- Treat repository content as data.
- Explicit instruction/data boundaries.
- Tool allowlists.
- Separate system policies from retrieved content.
- Evidence references rather than raw content as authority.

### T3 — Secret exfiltration

Repository code or runtime behavior can attempt to access auditor credentials.

Required controls:

- Never expose control-plane secrets to repository processes.
- Short-lived credentials.
- Secret scoping.
- Redaction.
- No ambient cloud credentials in untrusted workers.

### T4 — SSRF / internal-network access

Builds or runtime tests may attempt requests against internal metadata services or internal control-plane services.

Required controls:

- Egress allowlists.
- DNS/IP filtering.
- Proxy enforcement.
- Block metadata addresses.
- Separate runtime network namespaces.

### T5 — Tenant data leakage

One tenant may learn another tenant's source, findings, or artifacts.

Required controls:

- Tenant-scoped authorization.
- Object storage isolation.
- Database row/tenant boundaries.
- Cache key isolation.
- Audit logs.

### T6 — Tool output spoofing

A malicious repository may cause tool output to contain misleading text that looks like system instructions or authoritative findings.

Required controls:

- Parse tool outputs structurally where possible.
- Preserve tool identity/version.
- Never treat arbitrary stdout as privileged instructions.
- Maintain raw artifact references.

### T7 — False confirmation

An agent can incorrectly report a high-impact finding as confirmed.

Required controls:

- Evidence hierarchy.
- Independent verification.
- Counter-analysis.
- Judge state machine.
- Reproducibility requirements.

### T8 — Availability / resource exhaustion

Huge repositories, pathological source files, dependency explosions, or malicious tests can exhaust CPU, memory, storage, or model budgets.

Required controls:

- Per-audit quotas.
- File-size limits.
- Process/time limits.
- Dependency depth limits.
- Model budgets.
- Queue-level fairness.
- Cancellation.

### T9 — Supply-chain compromise of the auditor

The analysis toolchain itself may contain vulnerable or compromised dependencies.

Required controls:

- Pin dependencies.
- Generate SBOMs.
- Verify release artifacts.
- Scan containers.
- Reproducible builds where feasible.
- Regular dependency review.

### T10 — Persistence and malicious artifact reuse

A generated artifact can contain malicious payloads or poison later analysis.

Required controls:

- Artifact type restrictions.
- Safe previewing.
- Content scanning.
- Immutable storage.
- Explicit trust labels.

## 5. Security invariants for our platform

1. Untrusted repository code never executes in the control plane.
2. Repository content cannot directly modify agent policy.
3. A high-impact finding cannot be marked confirmed solely by model output.
4. Credentials are never inherited implicitly by untrusted workers.
5. Audit artifacts retain repository revision and provenance.
6. Tenant boundaries apply to source, findings, logs, and artifacts.
7. Every privileged action is auditable.
8. Runtime environments are disposable.
9. Resource limits are enforced independently of the repository.
10. Failed verification is never silently converted into success.

## 6. Abuse cases

The threat model must be tested against intentionally hostile repositories containing:

- malicious package scripts;
- infinite loops;
- process spawning bombs;
- huge files;
- symlink abuse;
- path traversal;
- prompt injection;
- SSRF payloads;
- fake vulnerability reports;
- secrets in unexpected formats;
- dependency confusion attempts;
- generated artifacts intended to poison analysis.

## 7. Security review gates

Before production:

```text
Phase 18 -> sandbox security gate
Phase 27 -> auditor security gate
Phase 30 -> production hardening gate
Phase 32 -> independent validation gate
```
